# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "google-api-python-client>=2.150",
#   "google-auth-oauthlib>=1.2",
#   "google-auth-httplib2>=0.2",
# ]
# ///
"""上傳影片到自己的 YouTube 頻道（YouTube Data API v3，OAuth 2.0 桌面應用流程）。

用法（在 repo 根執行）：

    uv run video/upload.py video/data/01litellm-basics.mp4                 # 讀同名 .json sidecar 當 metadata
    uv run video/upload.py video/data/x.mp4 --title "..." --privacy unlisted  # 命令列參數覆蓋 sidecar
    uv run video/upload.py video/data/x.mp4 --dry-run                        # 只印出會送出的 metadata，不登入不上傳
    uv run video/upload.py --check-auth                                      # 不開瀏覽器：token 能不能用？（exit 3＝要重新登入）
    uv run video/upload.py --login [--no-browser]                            # 只做登入授權＋頻道核對
    uv run video/upload.py --add-existing <video_id> --playlist-title "..."  # 把已上傳的影片補進播放清單
    uv run video/upload.py --playlist-sort --playlist-id PL... --playlist-order id1,id2,...  # 依課程順序整理清單

第一次執行會開瀏覽器做 Google 登入授權，token 存在 video/token.json，之後自動續期。
沒有桌面的機器加 --no-browser：程式印出授權網址，你在自己電腦先 `ssh -L 8090:localhost:8090 <這台>`
再開那個網址，登入完 Google 會導回 localhost:8090，經 ssh 隧道回到這裡。

前置設定（Google Cloud 專案、client_secret.json）見 video/README.md。
整批「上傳＋嵌進課程頁＋部署」請用 publish-videos skill，本檔是它底下的上傳核心。
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import random
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

HERE = Path(__file__).resolve().parent
DEFAULT_CLIENT_SECRET = HERE / "client_secret.json"
DEFAULT_TOKEN = HERE / "token.json"
RECEIPTS = HERE / "uploaded.jsonl"  # 放 video/ 這層：data/ 會被整個清空，紀錄不能跟著消失

# 一個 scope 就涵蓋 videos.insert / thumbnails.set / playlists.* / channels.list
SCOPES = ["https://www.googleapis.com/auth/youtube"]

# 你的頻道：上傳前會核對登入的是不是這個頻道，避免傳到別的帳號／品牌帳號
EXPECTED_CHANNEL_ID = "UCxwORIgu1LL5uGqQWmxmdLA"

DEFAULT_CATEGORY = "27"  # Education（28 = Science & Technology）
DEFAULT_LANGUAGE = "zh-Hant"
PRIVACY_CHOICES = ("private", "unlisted", "public")

CHUNK_SIZE = 8 * 1024 * 1024
RETRIABLE_STATUS = {500, 502, 503, 504}
MAX_RETRIES = 10

TITLE_MAX = 100
DESCRIPTION_MAX = 5000
TAGS_TOTAL_MAX = 500


def die(msg: str, code: int = 2) -> None:
    print(f"錯誤：{msg}", file=sys.stderr)
    sys.exit(code)


# ---------------------------------------------------------------- metadata


def load_sidecar(video: Path) -> dict:
    """同目錄同名的 .json（例：01litellm-basics.mp4 → 01litellm-basics.json）。"""
    sidecar = video.with_suffix(".json")
    if not sidecar.exists():
        return {}
    try:
        data = json.loads(sidecar.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        die(f"sidecar {sidecar} 不是合法 JSON：{e}")
    if not isinstance(data, dict):
        die(f"sidecar {sidecar} 最外層要是物件")
    print(f"讀取 sidecar：{sidecar}")
    return data


def resolve_metadata(args: argparse.Namespace, sidecar: dict) -> dict:
    """命令列 > sidecar > 預設。回傳 videos.insert 要的 body 以外的欄位也一併放回。"""
    title = args.title or sidecar.get("title") or args.video.stem
    description = args.description if args.description is not None else sidecar.get("description", "")
    if args.tags is not None:
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    else:
        tags = list(sidecar.get("tags", []) or [])
    category = str(args.category or sidecar.get("category") or DEFAULT_CATEGORY)
    privacy = args.privacy or sidecar.get("privacy") or "private"
    language = args.language or sidecar.get("language") or DEFAULT_LANGUAGE
    playlist_id = args.playlist_id or sidecar.get("playlist_id")
    thumbnail = args.thumbnail or sidecar.get("thumbnail")
    if thumbnail:
        thumbnail = Path(thumbnail)
        if not thumbnail.is_absolute():
            thumbnail = (args.video.parent / thumbnail).resolve()

    # YouTube 的硬限制，先在本機擋掉，省得上傳到一半才被退
    if not title.strip():
        die("標題不能是空的")
    if len(title) > TITLE_MAX:
        die(f"標題超過 {TITLE_MAX} 字（目前 {len(title)}）")
    if len(description) > DESCRIPTION_MAX:
        die(f"說明超過 {DESCRIPTION_MAX} 字（目前 {len(description)}）")
    for field, value in (("標題", title), ("說明", description)):
        if "<" in value or ">" in value:
            die(f"{field}不能含有 < 或 >（YouTube 會拒收）")
    if sum(len(t) for t in tags) + max(len(tags) - 1, 0) > TAGS_TOTAL_MAX:
        die(f"tags 總長度超過 {TAGS_TOTAL_MAX} 字")
    if privacy not in PRIVACY_CHOICES:
        die(f"privacy 只能是 {', '.join(PRIVACY_CHOICES)}，不是 {privacy!r}")
    if thumbnail and not thumbnail.exists():
        die(f"找不到縮圖 {thumbnail}")

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category,
            "defaultLanguage": language,
            "defaultAudioLanguage": language,
        },
        "status": {
            "privacyStatus": privacy,
            # 不設的話 YouTube Studio 會一直提醒「請設定觀眾」；教學影片預設不是兒童內容
            "selfDeclaredMadeForKids": bool(args.made_for_kids or sidecar.get("made_for_kids", False)),
        },
    }
    return {"body": body, "playlist_id": playlist_id, "thumbnail": thumbnail}


# ---------------------------------------------------------------- auth


def get_credentials(client_secret: Path, token_path: Path, *, open_browser: bool, port: int) -> Credentials:
    creds: Credentials | None = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        if creds.valid:
            return creds
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                save_token(creds, token_path)
                return creds
            except Exception as e:  # noqa: BLE001 — refresh 失敗就重走一次登入
                print(f"token 續期失敗（{e}），重新登入。", file=sys.stderr)

    if not client_secret.exists():
        die(
            f"找不到 OAuth 用戶端憑證 {client_secret}\n"
            "  到 Google Cloud Console → API 和服務 → 憑證 → 建立「OAuth 用戶端 ID」→ 類型選「電腦版應用程式」，\n"
            "  下載 JSON 存成上面那個路徑（或用 --client-secret 指定）。完整步驟見 video/README.md。"
        )

    flow = InstalledAppFlow.from_client_secrets_file(str(client_secret), SCOPES)
    if not open_browser:
        print(
            "\n【無桌面授權】\n"
            f"  1. 在你自己的電腦開一個終端機：ssh -L {port}:localhost:{port} <這台機器>\n"
            "  2. 把下面印出的網址貼到自己電腦的瀏覽器，登入要上傳的 Google 帳號並允許\n"
            f"  3. 瀏覽器會導回 http://localhost:{port}/ ，經 ssh 隧道回到這裡就完成了\n",
            file=sys.stderr,
        )
    creds = flow.run_local_server(
        host="localhost",
        port=port,
        open_browser=open_browser,
        access_type="offline",  # 要拿 refresh_token，之後不用再登入
        prompt="consent",
    )
    save_token(creds, token_path)
    return creds


def save_token(creds: Credentials, token_path: Path) -> None:
    token_path.write_text(creds.to_json(), encoding="utf-8")
    os.chmod(token_path, 0o600)
    print(f"token 已存到 {token_path}")


def check_auth(token_path: Path, expected_channel: str | None) -> int:
    """不開瀏覽器：token 能用（或能續期）且登入的是預期頻道 → 0；否則 3（要跑 --login）。"""
    hint = "重新登入：uv run video/upload.py --login（沒桌面加 --no-browser）"
    if not token_path.exists():
        print(f"沒有 {token_path}。{hint}", file=sys.stderr)
        return 3
    creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds.valid:
        if not (creds.expired and creds.refresh_token):
            print(f"token 無法使用。{hint}", file=sys.stderr)
            return 3
        try:
            creds.refresh(Request())
            save_token(creds, token_path)
        except Exception as e:  # noqa: BLE001
            print(f"token 續期失敗（{e}）。OAuth 同意畫面停在「測試」時 refresh token 七天到期。{hint}", file=sys.stderr)
            return 3
    try:
        yt = build("youtube", "v3", credentials=creds, cache_discovery=False)
        ch = check_channel(yt, expected_channel)
    except SystemExit:
        return 3
    print(f"auth OK：{ch['snippet']['title']}（{ch['id']}）")
    return 0


def check_channel(yt, expected: str | None) -> dict:
    resp = yt.channels().list(part="snippet", mine=True).execute()
    items = resp.get("items") or []
    if not items:
        die("這個 Google 帳號沒有 YouTube 頻道（或授權時選錯帳號）。刪掉 token.json 重新登入。")
    ch = items[0]
    cid, name = ch["id"], ch["snippet"]["title"]
    print(f"登入頻道：{name}（{cid}）")
    if expected and cid != expected:
        die(
            f"登入的頻道不是預期的 {expected}。\n"
            "  若你有多個頻道（品牌帳號），授權時要在 Google 的「選擇帳戶／頻道」畫面選對一個；\n"
            "  刪掉 video/token.json 重來，或用 --channel-id / --any-channel 改預期值。"
        )
    return ch


# ---------------------------------------------------------------- upload


def already_uploaded(video: Path) -> dict | None:
    if not RECEIPTS.exists():
        return None
    for line in RECEIPTS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("file") == video.name:
            return rec
    return None


def record_receipt(video: Path, response: dict) -> dict:
    rec = {
        "file": video.name,
        "video_id": response["id"],
        "url": f"https://youtu.be/{response['id']}",
        "title": response["snippet"]["title"],
        "privacy": response["status"]["privacyStatus"],
        "uploaded_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    with RECEIPTS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"已記錄到 {RECEIPTS}")
    return rec


def fmt_mb(n: int) -> str:
    return f"{n / (1024 * 1024):.1f} MB"


def upload_video(yt, video: Path, body: dict, *, notify: bool) -> dict:
    size = video.stat().st_size
    mime = mimetypes.guess_type(video.name)[0] or "video/*"
    media = MediaFileUpload(str(video), mimetype=mime, chunksize=CHUNK_SIZE, resumable=True)
    request = yt.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media,
        notifySubscribers=notify,
    )
    print(f"開始上傳 {video.name}（{fmt_mb(size)}，{mime}）")

    response = None
    retry = 0
    started = time.monotonic()
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                done = int(status.resumable_progress)
                pct = done / size * 100
                print(f"\r  上傳中 {pct:5.1f}%  {fmt_mb(done)} / {fmt_mb(size)}", end="", flush=True)
            retry = 0
        except HttpError as e:
            if e.resp.status not in RETRIABLE_STATUS:
                print()
                raise
            retry = backoff(retry, f"HTTP {e.resp.status}")
        except (OSError, ConnectionError) as e:
            retry = backoff(retry, f"{type(e).__name__}: {e}")
    elapsed = time.monotonic() - started
    print(f"\r  上傳完成 100.0%  {fmt_mb(size)}，耗時 {elapsed:.0f} 秒" + " " * 20)
    return response


def backoff(retry: int, why: str) -> int:
    retry += 1
    if retry > MAX_RETRIES:
        die(f"重試 {MAX_RETRIES} 次仍失敗（{why}），放棄。resumable session 已中斷，請重跑。", code=1)
    wait = random.random() * (2**retry)
    print(f"\n  暫時性錯誤（{why}），{wait:.1f} 秒後重試 {retry}/{MAX_RETRIES}", file=sys.stderr)
    time.sleep(wait)
    return retry


def set_thumbnail(yt, video_id: str, thumbnail: Path) -> None:
    mime = mimetypes.guess_type(thumbnail.name)[0] or "image/jpeg"
    try:
        yt.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(str(thumbnail), mimetype=mime)).execute()
        print(f"縮圖已設定：{thumbnail.name}")
    except HttpError as e:
        # 自訂縮圖要頻道先完成電話驗證，沒驗證會 403
        print(f"縮圖設定失敗（{e.resp.status}）：{e.reason}。頻道需先在 youtube.com/verify 完成驗證。", file=sys.stderr)


# ---------------------------------------------------------------- playlist


def ensure_playlist(yt, title: str, privacy: str) -> str:
    """同名播放清單存在就用它，否則建一個。標題是唯一鍵，所以模板固定後不會重複建。"""
    token = None
    while True:
        resp = yt.playlists().list(part="snippet", mine=True, maxResults=50, pageToken=token).execute()
        for it in resp.get("items", []):
            if it["snippet"]["title"] == title:
                print(f"播放清單已存在：{title}（{it['id']}）")
                return it["id"]
        token = resp.get("nextPageToken")
        if not token:
            break
    body = {"snippet": {"title": title}, "status": {"privacyStatus": privacy}}
    pid = yt.playlists().insert(part="snippet,status", body=body).execute()["id"]
    print(f"已建立播放清單：{title}（{pid}，{privacy}）")
    return pid


def playlist_video_ids(yt, playlist_id: str) -> list[str]:
    """剛建立的播放清單要幾秒才查得到（playlistNotFound 404）：遇到就等一下重試，最多約 30 秒。"""
    ids, token = [], None
    while True:
        for attempt in range(8):
            try:
                resp = yt.playlistItems().list(part="snippet", playlistId=playlist_id, maxResults=50, pageToken=token).execute()
                break
            except HttpError as e:
                if e.resp.status == 404 and attempt < 7:
                    print(f"  播放清單尚未同步（404），{2 + attempt * 2} 秒後重試…", file=sys.stderr)
                    time.sleep(2 + attempt * 2)
                    continue
                raise
        ids += [it["snippet"]["resourceId"].get("videoId") for it in resp.get("items", [])]
        token = resp.get("nextPageToken")
        if not token:
            return ids


def add_to_playlist(yt, video_id: str, playlist_id: str, order: list[str] | None) -> None:
    """order＝這個主題所有影片 id 的課程順序（含這支）。有 order 就算出插入位置，讓清單永遠照課程順序；
    沒 order 就直接接在最後。已在清單裡就不重複加。"""
    existing = playlist_video_ids(yt, playlist_id)
    if video_id in existing:
        print(f"已在播放清單裡：{playlist_id}")
        return
    snippet = {"playlistId": playlist_id, "resourceId": {"kind": "youtube#video", "videoId": video_id}}
    if order and video_id in order:
        before = set(order[: order.index(video_id)])
        snippet["position"] = sum(1 for v in existing if v in before)
    yt.playlistItems().insert(part="snippet", body={"snippet": snippet}).execute()
    pos = snippet.get("position", "末尾")
    print(f"已加入播放清單（位置 {pos}）：https://www.youtube.com/playlist?list={playlist_id}")


def playlist_items(yt, playlist_id: str) -> list[dict]:
    items, token = [], None
    while True:
        resp = yt.playlistItems().list(part="snippet", playlistId=playlist_id, maxResults=50, pageToken=token).execute()
        items += resp.get("items", [])
        token = resp.get("nextPageToken")
        if not token:
            return items


def sort_playlist(yt, playlist_id: str, order: list[str]) -> int:
    """把播放清單整理成 order 的順序（order 沒列到的維持原相對順序排後面）。
    為什麼要有這步：插入時算位置靠 playlistItems.list，而剛插入的項目要幾秒才查得到，
    連續加多支時位置會算錯；加完後整理一次就確定了。每移一項 50 單位。"""
    items = playlist_items(yt, playlist_id)
    current = [it["snippet"]["resourceId"].get("videoId") for it in items]
    rank = {v: i for i, v in enumerate(order)}
    desired = sorted(current, key=lambda v: (rank.get(v, len(order)), current.index(v)))
    moves = 0
    for target, vid in enumerate(desired):
        if current[target] == vid:
            continue
        it = next(x for x in items if x["snippet"]["resourceId"].get("videoId") == vid)
        yt.playlistItems().update(part="snippet", body={
            "id": it["id"],
            "snippet": {"playlistId": playlist_id, "resourceId": it["snippet"]["resourceId"], "position": target},
        }).execute()
        current.remove(vid)
        current.insert(target, vid)
        moves += 1
    print(f"播放清單已整理：{moves} 項移動，共 {len(current)} 項")
    return moves


def resolve_playlist(yt, args: argparse.Namespace, explicit_id: str | None) -> str | None:
    if explicit_id:
        return explicit_id
    if args.playlist_title:
        return ensure_playlist(yt, args.playlist_title, args.playlist_privacy)
    return None


# ---------------------------------------------------------------- main


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="上傳影片到自己的 YouTube 頻道。metadata 來源：命令列 > 同名 .json sidecar > 預設。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "sidecar 範例（video/data/01litellm-basics.json）：\n"
            '  {"title": "...", "description": "...", "tags": ["a", "b"],\n'
            '   "category": "27", "privacy": "unlisted", "language": "zh-Hant",\n'
            '   "playlist_id": "PL...", "thumbnail": "01litellm-basics.jpg"}'
        ),
    )
    p.add_argument("video", type=Path, nargs="?", help="影片檔（.mp4 等）；--check-auth / --login / --add-existing 時不用")
    p.add_argument("--title", help=f"標題（≤{TITLE_MAX} 字，不能含 <>）")
    p.add_argument("--description", help=f"說明（≤{DESCRIPTION_MAX} 字）")
    p.add_argument("--tags", help="標籤，逗號分隔")
    p.add_argument("--category", help=f"YouTube 分類 id（預設 {DEFAULT_CATEGORY}=Education）")
    p.add_argument("--privacy", choices=PRIVACY_CHOICES, help="預設 private（最安全，上線前可在 Studio 改）")
    p.add_argument("--language", help=f"defaultLanguage / defaultAudioLanguage（預設 {DEFAULT_LANGUAGE}）")
    p.add_argument("--thumbnail", help="自訂縮圖（jpg/png，≤2MB；頻道需完成驗證）")
    p.add_argument("--made-for-kids", action="store_true", help="標記為兒童內容（預設否）")
    p.add_argument("--no-notify", action="store_true", help="不通知訂閱者（只對 public 有意義）")
    p.add_argument("--force", action="store_true", help="就算 uploaded.jsonl 已有同名紀錄也照傳")
    p.add_argument("--dry-run", action="store_true", help="只印出會送出的 metadata，不登入不上傳")
    p.add_argument("--json-out", type=Path, help="把結果（video_id、url、playlist_id…）寫成 JSON 檔，給上層腳本讀")

    g = p.add_argument_group("播放清單")
    g.add_argument("--playlist-id", help="上傳後加入這個播放清單")
    g.add_argument("--playlist-title", help="沒給 --playlist-id 時：用這個標題找播放清單，找不到就建立")
    g.add_argument("--playlist-privacy", choices=PRIVACY_CHOICES, default="public", help="建立播放清單時的隱私（預設 public）")
    g.add_argument("--playlist-order", help="這個主題全部影片 id 的課程順序，逗號分隔，新影片用 NEW 佔位；用來算插入位置")
    g.add_argument("--add-existing", metavar="VIDEO_ID", help="不上傳，只把已存在的影片加進播放清單")
    g.add_argument("--playlist-sort", action="store_true", help="不上傳，把播放清單整理成 --playlist-order 的順序")

    g = p.add_argument_group("授權")
    g.add_argument("--client-secret", type=Path, default=Path(os.environ.get("YT_CLIENT_SECRET", DEFAULT_CLIENT_SECRET)))
    g.add_argument("--token", type=Path, default=Path(os.environ.get("YT_TOKEN", DEFAULT_TOKEN)))
    g.add_argument("--no-browser", action="store_true", help="不開瀏覽器，印出授權網址（無桌面機器用，配合 ssh -L）")
    g.add_argument("--port", type=int, default=8090, help="OAuth 回呼用的本機 port（預設 8090）")
    g.add_argument("--channel-id", default=EXPECTED_CHANNEL_ID, help="上傳前核對登入頻道要是這個 id")
    g.add_argument("--any-channel", action="store_true", help="跳過頻道核對")
    g.add_argument("--check-auth", action="store_true", help="不開瀏覽器檢查 token（能續期就續）；exit 0 可用、3 要重新登入")
    g.add_argument("--login", action="store_true", help="只做登入授權與頻道核對，不上傳")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    sys.stdout.reconfigure(line_buffering=True)  # 進度列與 die() 的 stderr 順序一致，tee 也看得到
    expected = None if args.any_channel else args.channel_id

    if args.check_auth:
        sys.exit(check_auth(args.token, expected))
    if args.login:
        creds = get_credentials(args.client_secret, args.token, open_browser=not args.no_browser, port=args.port)
        check_channel(build("youtube", "v3", credentials=creds, cache_discovery=False), expected)
        print("登入完成。")
        return
    if args.playlist_sort:
        if not args.playlist_order:
            die("--playlist-sort 需要 --playlist-order")
        creds = get_credentials(args.client_secret, args.token, open_browser=not args.no_browser, port=args.port)
        yt = build("youtube", "v3", credentials=creds, cache_discovery=False)
        check_channel(yt, expected)
        pid = resolve_playlist(yt, args, args.playlist_id)
        if not pid:
            die("--playlist-sort 需要 --playlist-id 或 --playlist-title")
        sort_playlist(yt, pid, [v for v in args.playlist_order.split(",") if v and v != "NEW"])
        return
    if args.add_existing:
        creds = get_credentials(args.client_secret, args.token, open_browser=not args.no_browser, port=args.port)
        yt = build("youtube", "v3", credentials=creds, cache_discovery=False)
        check_channel(yt, expected)
        pid = resolve_playlist(yt, args, args.playlist_id)
        if not pid:
            die("--add-existing 需要 --playlist-id 或 --playlist-title")
        order = [args.add_existing if v == "NEW" else v for v in args.playlist_order.split(",")] if args.playlist_order else None
        add_to_playlist(yt, args.add_existing, pid, order)
        if args.json_out:
            args.json_out.write_text(json.dumps({"video_id": args.add_existing, "playlist_id": pid}, ensure_ascii=False, indent=2))
        return

    video: Path | None = args.video
    if not video:
        die("要上傳的影片檔沒給（或改用 --check-auth / --login / --add-existing）")
    if not video.exists():
        die(f"找不到影片 {video}")
    if not video.is_file():
        die(f"{video} 不是檔案")
    args.video = video = video.resolve()

    meta = resolve_metadata(args, load_sidecar(video))
    body = meta["body"]

    print("將送出的 metadata：")
    print(json.dumps(body, ensure_ascii=False, indent=2))
    if meta["playlist_id"] or args.playlist_title:
        print(f"播放清單：{meta['playlist_id'] or args.playlist_title!r}")
    if meta["thumbnail"]:
        print(f"縮圖：{meta['thumbnail']}")
    print(f"檔案：{video}（{fmt_mb(video.stat().st_size)}）")

    if args.dry_run:
        print("\n--dry-run：到此為止，沒有登入也沒有上傳。")
        return

    prev = already_uploaded(video)
    if prev and not args.force:
        die(
            f"{video.name} 已在 {RECEIPTS} 有紀錄（{prev['url']}，{prev['uploaded_at']}）。\n"
            "  確定要再傳一份就加 --force。"
        )

    creds = get_credentials(args.client_secret, args.token, open_browser=not args.no_browser, port=args.port)
    yt = build("youtube", "v3", credentials=creds, cache_discovery=False)
    check_channel(yt, expected)
    playlist_id = resolve_playlist(yt, args, meta["playlist_id"])

    try:
        response = upload_video(yt, video, body, notify=not args.no_notify)
    except HttpError as e:
        detail = e.error_details or e.reason
        if e.resp.status == 403 and "quota" in str(detail).lower():
            die(f"配額用完（videos.insert 每個專案每日 100 次，太平洋時間午夜重置）：{detail}", code=1)
        die(f"YouTube 拒絕上傳（HTTP {e.resp.status}）：{detail}", code=1)

    video_id = response["id"]
    status = response.get("status", {})
    print(f"\n影片 id：{video_id}")
    print(f"網址：https://youtu.be/{video_id}")
    print(f"Studio：https://studio.youtube.com/video/{video_id}/edit")
    print(f"狀態：uploadStatus={status.get('uploadStatus')} privacy={status.get('privacyStatus')}")
    if status.get("privacyStatus") != "private":
        print(
            "提醒：未經 Google 審核（API compliance audit）的 API 專案上傳的影片會被鎖成私人，\n"
            "      若在 Studio 看到「私人（鎖定）」，見 video/README.md 的說明。"
        )
    result = record_receipt(video, response)
    result["playlist_id"] = playlist_id

    if meta["thumbnail"]:
        set_thumbnail(yt, video_id, meta["thumbnail"])
    if playlist_id:
        order = [video_id if v == "NEW" else v for v in args.playlist_order.split(",")] if args.playlist_order else None
        add_to_playlist(yt, video_id, playlist_id, order)
    if args.json_out:
        args.json_out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"結果已寫到 {args.json_out}")


if __name__ == "__main__":
    main()
