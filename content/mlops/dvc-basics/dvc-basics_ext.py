# DVC 資料版本控制：資料與模型也要有 git
# 不需要 GPU——molab 免費 CPU 環境即可全程執行（全部在本機的暫存資料夾裡，不連任何伺服器）。
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "dvc>=3.50",
#     "scikit-learn",
#     "pandas",
#     "numpy",
#     "pyyaml",
#     "mlflow>=3.0",
# ]
# ///
import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="DVC 資料版本控制：資料與模型也要有 git")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🗃️ DVC 資料版本控制：資料與模型也要有 git

    你的程式碼有 git，每一行改動都查得到。那**資料**呢？

    - 訓練資料 300 MB，丟進 git → clone 一次十分鐘，而且 `git diff` 給你看兩百萬行亂碼。
    - 模型檔 500 MB，每訓練一次就多一份 → repo 半年後變成 40 GB。
    - 最後大家的做法變成：`raw_final.csv`、`raw_final_v2.csv`、`raw_final_v2_修正版.csv`。

    **DVC**（Data Version Control）的解法只有一句話：

    > **git 只存一個小小的「指標檔」（記檔案的 md5 與大小），真正的檔案放在 cache 與遠端儲存。**

    於是「切回上個月那版資料」變成兩個動作：`git checkout` 拿回當時的指標檔、
    `dvc checkout` 把工作區的檔案換成指標檔指的那一份。

    這份 notebook 會在一個暫存資料夾裡開一個真的 git repo，從零把 DVC 做完一輪：

    | 節 | 做什麼 | 你會看到 |
    |---|---|---|
    | 0️⃣ | `git init` ＋ `dvc init` | `.dvc/` 目錄長什麼樣 |
    | 1️⃣ | `dvc add` 一份資料 | 89 bytes 的指標檔、自動寫好的 `.gitignore`、內容定址的 cache |
    | 2️⃣ | 回到舊版資料 | `git checkout` ＋ `dvc checkout` 兩步，資料真的變回去 |
    | 3️⃣ | `dvc.yaml` 管線 | `dvc repro` 第一次跑、第二次 skip |
    | 4️⃣ | 改參數重跑 | `dvc params diff`／`dvc metrics diff` |
    | 5️⃣ | 兩個 stage | 只有受影響的 stage 會重跑；`dvc dag` |
    | 6️⃣ | `dvc exp run` | 一次跑好幾組參數再一起比 |
    | 7️⃣ | 遠端儲存 | `dvc push` / `dvc pull`——同事怎麼拿到資料 |
    | 8️⃣ | 跟 MLflow 分工 | 把資料的 md5 記進 MLflow run |
    | 9️⃣ | 換你動手 | 選一種改動，真的跑一次 `dvc repro` |

    從第一格往下全部執行即可（首次安裝套件約 1–2 分鐘，之後整份 notebook 跑完約 40–60 秒）。
    所有東西都寫在系統暫存資料夾裡，不會動到你的任何專案。
    """
    )
    return


@app.cell
def _():
    import html
    import json
    import os
    import shutil
    import subprocess
    import sys
    import tempfile
    import textwrap
    import time
    from pathlib import Path

    import marimo as mo
    import pandas as pd
    import yaml
    from sklearn.datasets import make_classification

    return (
        Path,
        html,
        json,
        make_classification,
        mo,
        os,
        pd,
        shutil,
        subprocess,
        sys,
        tempfile,
        textwrap,
        time,
        yaml,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 0️⃣ 準備：一個暫存的 git repo，跟一份訓練資料

    DVC **不取代 git，它站在 git 旁邊**：程式碼、設定、指標檔歸 git；大檔案歸 DVC。
    所以第一步一定是先有一個 git repo（沒有 git，`dvc init` 會直接拒絕）。

    下面這一格把工作目錄開在系統暫存資料夾（`/tmp/dvc-lesson` 之類的地方），
    每次重跑都會先清空，數字才對得起來。所有指令都用 `subprocess` 送到那個資料夾裡執行——
    **我們不切換 notebook 自己的工作目錄**，每一格都明確指定 `cwd`，這樣你怎麼跳著跑都不會亂。
    """
    )
    return


@app.cell
def _(Path, html, mo, os, subprocess, sys, tempfile):
    # 工作目錄（每次重跑先清空）與「假裝是 S3」的遠端目錄
    WORK = Path(tempfile.gettempdir()) / "dvc-lesson"
    REMOTE = Path(tempfile.gettempdir()) / "dvc-lesson-remote"
    MLRUNS = Path(tempfile.gettempdir()) / "dvc-lesson-mlflow"  # 第 8 節的 MLflow 紀錄簿放這，不弄髒 repo

    # dvc 沒有保證裝在 PATH 上，但它有 __main__ → 一律用 `python -m dvc`；
    # 同時把目前這個 python 的資料夾放進 PATH，dvc.yaml 裡的 `python train.py` 才找得到直譯器。
    PY = sys.executable
    ENV = {
        **os.environ,
        "PATH": str(Path(PY).parent) + os.pathsep + os.environ.get("PATH", ""),
        "DVC_NO_ANALYTICS": "1",  # 關掉匿名統計回報：跑起來更快，也不需要網路
    }

    def sh(cmd, cwd=None):
        """在工作目錄裡跑一行指令，回傳 (顯示用的指令, 合併後的輸出)。"""
        _r = subprocess.run(
            cmd,
            shell=True,
            cwd=str(cwd or WORK),
            capture_output=True,
            text=True,
            env=ENV,
            check=False,
        )
        return cmd.replace(PY + " -m dvc", "dvc"), (_r.stdout + _r.stderr).strip()

    def dvc(args, cwd=None):
        """跑一行 dvc 指令。"""
        return sh(f"{PY} -m dvc {args}", cwd=cwd)

    # 這兩個 helper 刻意不走 mo.md 的 markdown：實測 marimo 0.24 會把程式碼區塊裡
    # 以 "- " 開頭的行（YAML 清單、dvc.lock）當成 markdown 清單重排——縮排會跑掉、
    # 中間被插入空行。改成直接輸出 <pre>，看到的就跟檔案裡一模一樣。
    _PRE = (
        "font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;"
        "font-size:12.5px;line-height:1.6;margin:0;padding:11px 13px;"
        "overflow-x:auto;white-space:pre;"
    )
    _BOX = (
        "border-radius:8px;margin:8px 0;overflow:hidden;"
        "background:color-mix(in srgb, currentColor 6%, transparent);"
    )
    _TAG = (
        "font-family:ui-monospace,monospace;font-size:10px;letter-spacing:.1em;"
        "text-transform:uppercase;opacity:.5;padding:7px 13px 0;"
    )

    def term(*results):
        """把好幾組 (指令, 輸出) 排成一塊終端機畫面。"""
        _lines = []
        for _cmd, _out in results:
            _lines.append("$ " + _cmd + ("\n" + _out if _out else ""))
        return mo.Html(
            f"<div style='{_BOX}'><pre style='{_PRE}'>"
            + html.escape("\n\n".join(_lines))
            + "</pre></div>"
        )

    def block(text, lang="text"):
        """把一段檔案內容排成程式碼區塊。"""
        return mo.Html(
            f"<div style='{_BOX}'><div style='{_TAG}'>{html.escape(lang)}</div>"
            f"<pre style='{_PRE}'>" + html.escape(str(text).rstrip()) + "</pre></div>"
        )

    def cache_files():
        """列出 .dvc/cache 裡實際存了哪些內容（相對路徑）。"""
        _root = WORK / ".dvc" / "cache"
        if not _root.exists():
            return []
        return sorted(str(_p.relative_to(_root)) for _p in _root.rglob("*") if _p.is_file())

    return ENV, MLRUNS, PY, REMOTE, WORK, block, cache_files, dvc, sh, term


@app.cell
def _(MLRUNS, REMOTE, WORK, dvc, mo, sh, shutil, term):
    # 清空 → git init → dvc init
    for _d in (WORK, REMOTE, MLRUNS):
        shutil.rmtree(_d, ignore_errors=True)
        _d.mkdir(parents=True)

    step0 = mo.vstack(
        [
            term(
                sh("git init -q && git config user.email student@example.com && git config user.name Student"),
                dvc("init -q"),
                dvc("config core.analytics false"),
                dvc("--version"),
                sh("ls -A .dvc"),
                sh("git status --short"),
            ),
            mo.md(
                f"""
    `dvc init` 做完之後，git 的暫存區裡多了三個**很小的檔案**（上面 `git status` 的
    `A` 就是它們）：`.dvc/config`（DVC 的設定）、`.dvc/.gitignore`、`.dvcignore`。
    真正存資料的 `.dvc/cache` 被寫進 `.dvc/.gitignore` ——**它永遠不進 git**：

    ```text
    {(WORK / ".dvc" / ".gitignore").read_text().strip()}
    ```
    """
            ),
        ]
    )
    step0
    return (step0,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    資料用這個系列共用的「客戶流失」模擬資料：2000 筆、12 個匿名特徵 `f0`–`f11`、
    標籤 `label`（1＝流失）。它只有 460 KB，不是什麼大資料——但**流程跟 300 GB 完全一樣**，
    這正是重點：你現在學的動作，等資料長大之後一個字都不用改。
    """
    )
    return


@app.cell
def _(WORK, make_classification, mo, pd, step0):
    step0  # 確保先 init 完才建資料
    COLS = [f"f{_i}" for _i in range(12)]
    _X, _y = make_classification(n_samples=2000, n_features=12, n_informative=6, random_state=0)
    raw_df = pd.DataFrame(_X, columns=COLS).assign(label=_y)
    (WORK / "data").mkdir(exist_ok=True)
    raw_df.to_csv(WORK / "data" / "raw.csv", index=False)

    step_data = mo.md(
        f"""
    `data/raw.csv` 建好了：**{len(raw_df)} 列 × {len(raw_df.columns)} 欄**，
    磁碟上 **{(WORK / "data" / "raw.csv").stat().st_size:,} bytes**（約 {(WORK / "data" / "raw.csv").stat().st_size // 1024} KB）。
    """
    )
    step_data
    return COLS, raw_df, step_data


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ `dvc add`：git 存指標，DVC 存內容

    現在做這堂課最核心的一個動作。`dvc add data/raw.csv` 會一次做完三件事：

    1. 算出這個檔案的 **md5**，把**檔案本身**複製進 `.dvc/cache`；
    2. 產生一個叫 `data/raw.csv.dvc` 的小文字檔（**指標檔**），裡面記 md5、大小、路徑；
    3. 在 `data/.gitignore` 裡加一行 `/raw.csv`——**叫 git 不要碰這個大檔**。

    之後你 commit 進 git 的是那個指標檔，不是 460 KB 的 CSV。
    """
    )
    return


@app.cell
def _(WORK, block, cache_files, dvc, mo, step_data, term):
    step_data  # 資料要先存在
    step1 = mo.vstack(
        [
            term(dvc("add data/raw.csv")),
            mo.md("**產生的指標檔 `data/raw.csv.dvc`**（整個檔案就這 5 行）："),
            block((WORK / "data" / "raw.csv.dvc").read_text(), "yaml"),
            mo.md(
                f"指標檔本身只有 **{(WORK / 'data' / 'raw.csv.dvc').stat().st_size} bytes**，"
                f"而它代表的資料是 **{(WORK / 'data' / 'raw.csv').stat().st_size:,} bytes**。"
                "\n\n**DVC 幫你寫好的 `data/.gitignore`**："
            ),
            block((WORK / "data" / ".gitignore").read_text()),
            mo.md("**`.dvc/cache` 裡多了什麼**："),
            block("\n".join(cache_files())),
        ]
    )
    step1
    return (step1,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    看一下 cache 裡那個檔名：`84/45065497d9a2aa59d1ee84e100dc5d`——
    把前兩碼切出來當資料夾，剩下的當檔名，**合起來就是指標檔裡的那串 md5**。

    這叫**內容定址**（content-addressable storage），有兩個直接的好處：

    - **同樣的內容只會存一份。** 十個人各自 `dvc add` 同一份資料，cache 裡還是一份。
    - **檔案在不在、有沒有被動過，比對 md5 就知道**，不需要相信檔名或修改時間。

    現在把指標檔 commit 進 git。注意 commit 的東西有多小。
    """
    )
    return


@app.cell
def _(mo, sh, step1, term):
    step1
    step1b = mo.vstack(
        [
            term(
                sh("git add -A && git commit -qm 'v1: 2000 列訓練資料'"),
                sh("git log --oneline"),
                sh("du -sh .git data/raw.csv"),
            ),
            mo.md(
                "上面兩個數字就是 DVC 的全部價值：**git repo 幾百 KB，資料多大都不影響它。**"
                "把 460 KB 換成 460 GB，`.git` 還是那個大小。"
            ),
        ]
    )
    step1b
    return (step1b,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ### 資料變了會怎樣？

    假設你發現第 0 列的標籤標錯了，把它改掉。改完之後 `dvc status` 會先告訴你「這個檔跟指標檔對不上了」，
    然後 `dvc add` 一次，指標檔裡的 md5 就換成新的——**而 `git diff` 只會看到一行改動**。
    """
    )
    return


@app.cell
def _(WORK, block, cache_files, dvc, mo, raw_df, sh, step1b, term):
    step1b
    _v2 = raw_df.copy()
    _v2.loc[0, "label"] = 1 - int(_v2.loc[0, "label"])
    _v2.to_csv(WORK / "data" / "raw.csv", index=False)

    step1c = mo.vstack(
        [
            mo.md(
                f"把第 0 列的 `label` 從 **{int(raw_df.loc[0, 'label'])}** 改成 "
                f"**{int(_v2.loc[0, 'label'])}**（2000 列裡只動了一格）。"
            ),
            term(
                dvc("status"),
                dvc("add data/raw.csv"),
                sh("git diff data/raw.csv.dvc"),
            ),
            mo.md(
                "**整個 `git diff` 就是一行 md5。**這是 DVC 最實際的好處之一——"
                "資料的改動在 code review 裡是**一行**，不是兩百萬行亂碼；"
                "但那一行足以精確指出「是哪一份資料」。\n\n"
                "而 cache 裡現在有**兩份**內容（舊的沒有被覆蓋掉，回得去）："
            ),
            block("\n".join(cache_files())),
            term(
                sh("git commit -qam 'v2: 修掉一筆錯標的資料'"),
                sh("git log --oneline"),
            ),
        ]
    )
    step1c
    return (step1c,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ 回到舊版：`git checkout` ＋ `dvc checkout`

    這是最容易踩到的一件事，先把規則講清楚：

    > **git 管指標檔，DVC 管檔案本身。所以切版本要兩步。**

    只做 `git checkout`，你的工作區會處於一個奇怪的狀態：指標檔已經是舊的了，
    但 `data/raw.csv` 還是新的那一份——**而且 git 不會警告你**（它根本不知道有這個檔）。
    要讓資料真的跟著回去，得再跑一次 `dvc checkout`。

    下面就把這個「中間狀態」演一次給你看。
    """
    )
    return


@app.cell
def _(WORK, dvc, mo, pd, sh, step1c, term):
    step1c
    _v1_sha = sh("git rev-parse --short HEAD~1")[1]

    def _label0():
        return int(pd.read_csv(WORK / "data" / "raw.csv").loc[0, "label"])

    _now = _label0()
    _t1 = term(sh("git log --oneline"), sh(f"git checkout {_v1_sha} -- data/raw.csv.dvc"))
    _mid = _label0()
    _t2 = term(dvc("status"), dvc("checkout"))
    _after = _label0()
    _t3 = term(sh("git checkout HEAD -- data/raw.csv.dvc"), dvc("checkout"), sh("git status --short"))
    _back = _label0()

    step2 = mo.vstack(
        [
            mo.md(f"目前（v2）第 0 列的 `label` ＝ **{_now}**。現在把**指標檔**切回 v1（`{_v1_sha}`）："),
            _t1,
            mo.md(
                f"⚠️ 指標檔已經是 v1 的了，但資料檔的第 0 列還是 **{_mid}**——"
                "**git checkout 不會動到 DVC 管的檔案**。`dvc status` 正是在說這件事："
            ),
            _t2,
            mo.md(
                f"✅ `dvc checkout` 之後，第 0 列變成 **{_after}**，資料真的回到 v1 了"
                f"（列數還是 {len(pd.read_csv(WORK / 'data' / 'raw.csv'))}）。"
                "注意它是從 cache 直接還原的，**沒有重新計算、沒有連網**。\n\n"
                "再切回最新版，工作區乾乾淨淨："
            ),
            _t3,
            mo.md(f"第 0 列又是 **{_back}** 了。**回溯資料 ＝ `git checkout` ＋ `dvc checkout`，永遠兩步。**"),
        ]
    )
    step2
    return (step2,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ `dvc.yaml`：把「怎麼從資料變成模型」寫下來

    版本控制只解決了一半的問題。另一半是：**這個模型是怎麼來的？**

    `dvc.yaml` 用一種很像 Makefile 的方式描述整條管線。一個 **stage** 要講四件事：

    | 欄位 | 意思 | 為什麼重要 |
    |---|---|---|
    | `cmd` | 要跑的指令 | 就是你平常在終端機打的那行 |
    | `deps` | 這一步吃什麼（資料、程式） | **任何一個變了才需要重跑** |
    | `params` | 從 `params.yaml` 讀哪些設定 | 參數變了也要重跑 |
    | `outs` / `metrics` | 這一步吐出什麼 | 產物交給 DVC 管（自動進 cache、自動 gitignore） |

    先寫最單純的一個 stage：讀 `data/raw.csv`、訓練一棵隨機森林、吐出 `model.pkl` 與 `metrics.json`。
    """
    )
    return


@app.cell
def _(WORK, block, mo, step2, textwrap):
    step2
    PARAMS_V1 = "train:\n  max_depth: 4\n  n_estimators: 50\n"
    TRAIN_SINGLE = textwrap.dedent("""\
        import json, pickle, yaml, pandas as pd
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import roc_auc_score

        p = yaml.safe_load(open("params.yaml"))["train"]
        df = pd.read_csv("data/raw.csv")
        X, y = df.drop(columns="label"), df["label"]
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=0)

        model = RandomForestClassifier(random_state=0, **p).fit(Xtr, ytr)
        auc = roc_auc_score(yte, model.predict_proba(Xte)[:, 1])

        pickle.dump(model, open("model.pkl", "wb"))
        json.dump({"auc": round(auc, 5), "n_rows": len(df)}, open("metrics.json", "w"))
        print("auc =", round(auc, 5))
    """)
    DVCYAML_SINGLE = textwrap.dedent("""\
        stages:
          train:
            cmd: python train.py
            deps:
              - data/raw.csv
              - train.py
            params:
              - train.max_depth
              - train.n_estimators
            outs:
              - model.pkl
            metrics:
              - metrics.json
    """)
    (WORK / "params.yaml").write_text(PARAMS_V1)
    (WORK / "train.py").write_text(TRAIN_SINGLE)
    (WORK / "dvc.yaml").write_text(DVCYAML_SINGLE)

    step3files = mo.vstack(
        [
            mo.md("**`params.yaml`**——所有會調的數字集中在這裡，不寫死在程式裡："),
            block(PARAMS_V1, "yaml"),
            mo.md("**`train.py`**——一支普通到不能再普通的訓練腳本，它完全不知道 DVC 存在："),
            block(TRAIN_SINGLE, "python"),
            mo.md("**`dvc.yaml`**——把上面那支腳本包成一個 stage："),
            block(DVCYAML_SINGLE, "yaml"),
        ]
    )
    step3files
    return DVCYAML_SINGLE, PARAMS_V1, step3files


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    `dvc repro` 會走過每一個 stage，比對 `deps` 與 `params` 的 md5：
    **對得上就跳過，對不上才跑 `cmd`。**第一次當然全部要跑。
    """
    )
    return


@app.cell
def _(WORK, block, dvc, mo, step3files, term, time):
    step3files
    _t0 = time.time()
    _r = dvc("repro")
    _elapsed = round(time.time() - _t0, 1)

    step3repro = mo.vstack(
        [
            term(_r),
            mo.md(
                f"跑完花了 **{_elapsed} 秒**。產物：`metrics.json` ＝ "
                f"`{(WORK / 'metrics.json').read_text().strip()}`，"
                f"`model.pkl` ＝ **{(WORK / 'model.pkl').stat().st_size:,} bytes**"
                "（模型檔也被 DVC 收進 cache 了——**「資料與模型也要有 git」的模型那一半，就是這樣做的**）。\n\n"
                "同時多了一個很關鍵的檔案 **`dvc.lock`**。它是這次執行的「收據」，"
                "把每一個依賴、每一個參數、每一個產物的 md5 全部記下來："
            ),
            block((WORK / "dvc.lock").read_text(), "yaml"),
            mo.md(
                "`dvc.lock` 要**進 git**（它很小），`model.pkl` 與 `metrics.json` 則被自動寫進根目錄的 "
                "`.gitignore`。這樣一來，任何一個 commit 都完整回答了「這個模型是用哪一版資料、哪些參數、哪一版程式跑出來的」。"
            ),
        ]
    )
    step3repro
    return (step3repro,)


@app.cell
def _(dvc, mo, sh, step3repro, term, time):
    step3repro
    _c = sh("git add -A && git commit -qm 'v3: 建立訓練管線（max_depth=4）'")
    _t0 = time.time()
    _r = dvc("repro")
    _elapsed = round(time.time() - _t0, 1)

    step3skip = mo.vstack(
        [
            term(_c, _r, dvc("status")),
            mo.md(
                f"第二次 `dvc repro` 只花 **{_elapsed} 秒**，而且什麼都沒跑。"
                "**這就是管線的核心價值**：它不是「一鍵重跑全部」，而是「只跑真的需要跑的部分」。"
                "在真實專案裡，這個差別是三十秒與三小時。"
            ),
        ]
    )
    step3skip
    return (step3skip,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ 改一個參數，看 DVC 幫你比

    把 `params.yaml` 的 `max_depth` 從 4 改成 12，再 `dvc repro`。
    DVC 會發現參數的 md5 對不上 → 重跑 `train`。

    跑完之後有兩個很好用的指令：

    - `dvc params diff`：**現在的參數** vs **HEAD（上一個 commit）的參數**
    - `dvc metrics diff`：同樣的比法，但比的是指標，還會算出差值

    這兩個指令是 DVC 版的「這次改動帶來什麼效果」，可以直接貼進 PR 描述裡。
    """
    )
    return


@app.cell
def _(WORK, dvc, mo, sh, step3skip, term):
    step3skip
    (WORK / "params.yaml").write_text("train:\n  max_depth: 12\n  n_estimators: 50\n")
    step4 = mo.vstack(
        [
            term(
                dvc("repro"),
                dvc("params diff"),
                dvc("metrics diff"),
                sh("git add -A && git commit -qm 'v4: 調參 max_depth 4 → 12'"),
            ),
            mo.md(
                "`Change` 那一欄是 DVC 幫你算的。注意這裡**沒有任何一份資料被複製**——"
                "資料的 md5 沒變，DVC 認得出來是同一份，cache 裡也不會多存一份。"
                "**參數的版本與資料的版本，是分開追蹤的兩件事。**"
            ),
        ]
    )
    step4
    return (step4,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5️⃣ 兩個 stage：只有下游會重跑

    真實的管線不會只有一步。把它拆成兩個 stage——

    - **`prepare`**：讀 `data/raw.csv`，切成 `data/train.csv` 與 `data/test.csv`
    - **`train`**：讀那兩個檔，訓練、算 AUC

    拆開之後，`train` 的 `deps` 不再是 `data/raw.csv`，而是 `prepare` 的產物。
    DVC 會自己從「誰吃誰的產物」推出執行順序（**你不用宣告順序**），
    而且——這才是重點——**改參數只會重跑 `train`，`prepare` 會被跳過**。
    """
    )
    return


@app.cell
def _(WORK, block, dvc, mo, step4, term, textwrap):
    step4
    PREPARE_PY = textwrap.dedent("""\
        import pandas as pd
        from sklearn.model_selection import train_test_split

        df = pd.read_csv("data/raw.csv")
        train, test = train_test_split(df, test_size=0.25, random_state=0)
        train.to_csv("data/train.csv", index=False)
        test.to_csv("data/test.csv", index=False)
        print(f"prepare: {len(df)} 列 -> train {len(train)} / test {len(test)}")
    """)
    TRAIN_TWO = textwrap.dedent("""\
        import json, pickle, yaml, pandas as pd
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.metrics import roc_auc_score

        p = yaml.safe_load(open("params.yaml"))["train"]
        train = pd.read_csv("data/train.csv")
        test = pd.read_csv("data/test.csv")

        model = RandomForestClassifier(random_state=0, **p).fit(
            train.drop(columns="label"), train["label"]
        )
        auc = roc_auc_score(test["label"], model.predict_proba(test.drop(columns="label"))[:, 1])

        pickle.dump(model, open("model.pkl", "wb"))
        json.dump({"auc": round(auc, 5), "n_rows": len(train)}, open("metrics.json", "w"))
        print("auc =", round(auc, 5))
    """)
    DVCYAML_TWO = textwrap.dedent("""\
        stages:
          prepare:
            cmd: python prepare.py
            deps:
              - data/raw.csv
              - prepare.py
            outs:
              - data/train.csv
              - data/test.csv
          train:
            cmd: python train.py
            deps:
              - data/train.csv
              - data/test.csv
              - train.py
            params:
              - train.max_depth
              - train.n_estimators
            outs:
              - model.pkl
            metrics:
              - metrics.json
    """)
    (WORK / "prepare.py").write_text(PREPARE_PY)
    (WORK / "train.py").write_text(TRAIN_TWO)
    (WORK / "dvc.yaml").write_text(DVCYAML_TWO)

    step5a = mo.vstack(
        [
            mo.md("**新的 `dvc.yaml`**（`train` 的 `deps` 換成 `prepare` 的 `outs`，依賴關係就這樣接起來）："),
            block(DVCYAML_TWO, "yaml"),
            term(dvc("repro"), dvc("dag")),
            mo.md(
                "`dvc dag` 把管線畫出來給你看。這張圖不是你畫的，是 DVC **從 deps／outs 推出來的**——"
                "所以它永遠跟真正跑的東西一致，不會像投影片上的架構圖那樣過期。\n\n"
                "AUC 跟上一節一樣（同一份資料、同一個切法、同一組參數），"
                "**重構管線不該改變結果**——這正好是一個很好的自我檢查。"
            ),
        ]
    )
    step5a
    return (step5a,)


@app.cell
def _(WORK, dvc, mo, sh, step5a, term, time):
    step5a
    _c = sh("git add -A && git commit -qm 'v5: 拆成 prepare + train 兩個 stage'")
    (WORK / "params.yaml").write_text("train:\n  max_depth: 8\n  n_estimators: 50\n")
    _t0 = time.time()
    _r = dvc("repro")
    _elapsed = round(time.time() - _t0, 1)

    step5b = mo.vstack(
        [
            mo.md("把 `max_depth` 改成 8 再 repro 一次，盯著第一行看："),
            term(_c, _r, dvc("metrics diff")),
            mo.md(
                f"**`Stage 'prepare' didn't change, skipping`**——切分資料那一步被跳過了，"
                f"只有 `train` 重跑，整輪 **{_elapsed} 秒**。"
                "`prepare` 的依賴（`data/raw.csv` 與 `prepare.py`）一個字都沒變，"
                "DVC 沒有理由重做一次。管線越長，這件事省下的時間越可觀。"
            ),
        ]
    )
    step5b
    return (step5b,)


@app.cell
def _(WORK, dvc, mo, sh, step5b, term):
    step5b
    _r = sh("git checkout -- params.yaml")
    _t = dvc("repro")
    step5c = mo.vstack(
        [
            mo.md("再把 `max_depth` 改回 12（也就是 HEAD 那一版）看看："),
            term(_r, _t),
            mo.md(
                "**`Stage 'train' is cached - skipping run, checking out outputs`**——"
                "這組依賴＋參數的組合 DVC **以前算過**，它直接把當時的產物從 cache 撈回來，"
                "連跑都不用跑。這叫 **run cache**：來回比較兩組參數時，第二次之後都是瞬間完成。\n\n"
                f"目前的 `metrics.json`：`{(WORK / 'metrics.json').read_text().strip()}`。"
            ),
        ]
    )
    step5c
    return (step5c,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 6️⃣ `dvc exp run`：一次跑好幾組，最後一起比

    上面那套「改 `params.yaml` → repro → commit」每試一組參數就要動一次工作區，
    試十組就是十個 commit。`dvc exp run` 是為這件事設計的：

    ```text
    dvc exp run --set-param train.max_depth=6
    ```

    它會**暫時**把參數換成 6、跑一次管線、把結果存成一個「實驗」（掛在 git 上但不是 commit），
    然後 `dvc exp show` 把所有實驗排成一張表。試錯的過程不會弄髒你的 git 歷史。
    """
    )
    return


@app.cell
def _(dvc, mo, sh, step5c, term):
    step5c
    step6 = mo.vstack(
        [
            term(
                dvc("exp run --set-param train.max_depth=6"),
                dvc("exp run --set-param train.max_depth=20"),
                dvc("exp show --only-changed"),
            ),
            mo.md(
                "`workspace` 那一列是你現在的工作區，`master` 是最後一個 commit，"
                "下面兩列是剛剛跑的兩個實驗（名字是 DVC 隨機取的）。"
                "`--only-changed` 讓表只留下**有變動的**參數與指標欄位，不然一大堆沒動的欄位會塞滿畫面。\n\n"
                "**看完就丟**：實驗跑完會把結果套用到工作區，所以下面收拾一下，回到 HEAD 那一版再往下走。"
                "覺得某個實驗值得留下來時，用 `dvc exp branch <實驗名>` 把它變成一個真正的 git 分支。"
            ),
            term(sh("git checkout -- params.yaml dvc.lock"), dvc("repro"), sh("git status --short")),
        ]
    )
    step6
    return (step6,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 7️⃣ 遠端儲存：同事 clone 完之後怎麼拿到資料

    到目前為止，資料都只在你這台機器的 `.dvc/cache` 裡。同事把 repo clone 下來，
    只會拿到指標檔，`data/raw.csv` 是不存在的。

    這就是 **remote** 的工作：一個放「內容」的地方。它可以是 S3、GCS、Azure、SSH、
    HTTP、Google Drive……**也可以只是一個資料夾**（NAS、外接硬碟、共用磁碟機都算）。
    對 DVC 來說差別只有那一行網址：

    ```text
    dvc remote add -d storage s3://my-bucket/dvcstore
    dvc remote add -d storage gs://my-bucket/dvcstore
    dvc remote add -d storage ssh://user@host/path
    dvc remote add -d storage /mnt/nas/dvcstore        ← 我們用這種，最容易看清楚裡面長什麼樣
    ```

    `-d` 是 default 的意思：以後 `dvc push` / `dvc pull` 不用指定名字。
    """
    )
    return


@app.cell
def _(REMOTE, WORK, block, dvc, mo, step6, term):
    step6
    _add = dvc(f"remote add -d local {REMOTE}")
    _push = dvc("push")
    _remote_ls = sorted(str(_p.relative_to(REMOTE)) for _p in REMOTE.rglob("*") if _p.is_file())

    step7a = mo.vstack(
        [
            term(_add, _push),
            mo.md("**`.dvc/config` 現在長這樣**（這個檔會進 git，所以團隊裡每個人自動吃到同一個遠端）："),
            block((WORK / ".dvc" / "config").read_text(), "ini"),
            mo.md(f"**遠端資料夾 `{REMOTE}` 裡的內容**："),
            block("\n".join(_remote_ls)),
            mo.md(
                "跟 `.dvc/cache` 一模一樣的 `md5 前兩碼 / 剩下的碼` 結構——"
                "**遠端就是 cache 的另一份拷貝**，沒有資料庫、沒有中繼服務。"
                "換成 S3 的話，這些就是 bucket 裡的 object key。"
            ),
        ]
    )
    step7a
    return (step7a,)


@app.cell
def _(dvc, mo, sh, step7a, term):
    step7a
    _c = sh("git add -A && git commit -qm 'v6: 設定遠端儲存'")
    # 演一次「同事剛 clone 完」的狀態：cache 與資料檔全部不存在，只剩 git 裡的指標檔
    _t0 = term(_c, sh("rm -rf .dvc/cache data/raw.csv data/train.csv data/test.csv model.pkl"), sh("ls data"))
    _st = dvc("status")
    _pull = dvc("pull")

    step7b = mo.vstack(
        [
            mo.md(
                "現在把 `.dvc/cache` 跟所有資料檔**整個刪掉**，"
                "模擬「同事剛 `git clone` 完」的狀態——git 裡有的只有指標檔："
            ),
            _t0,
            term(_st, _pull, sh("ls data"), dvc("status")),
            mo.md(
                "`dvc pull` 照著指標檔與 `dvc.lock` 裡的 md5 去遠端把內容抓回來，資料與模型都回來了。"
                "**新同事的完整流程就是三行**：\n\n"
                "```text\n"
                "git clone <repo>\n"
                "cd <repo>\n"
                "dvc pull\n"
                "```\n\n"
                "沒有「請找 Alice 要那份 CSV」、沒有 `raw_final_v2_真的最終版.csv`。"
            ),
        ]
    )
    step7b
    return (step7b,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 8️⃣ 跟 MLflow 怎麼分工

    這個主題的第 1、2 課你已經用 MLflow 記過訓練。那 DVC 跟 MLflow 是二選一嗎？**不是，它們管的是不同的東西：**

    | | DVC | MLflow |
    |---|---|---|
    | 管什麼 | **檔案的版本**與**管線的可重現** | **實驗的紀錄**與**模型的註冊** |
    | 綁在哪 | git commit | run id |
    | 典型問題 | 「上個月那版資料在哪？」「這步要不要重跑？」 | 「哪一次跑的 AUC 最高？當時參數是什麼？」 |
    | 存什麼 | 資料、模型檔、中間產物（內容定址） | params、metrics、artifacts、模型版本與 alias |
    | 誰在用 | 整個團隊共用一份資料 | 每個人的每一次訓練 |

    實務上兩個一起用，接點只要一行：**把 `.dvc` 指標檔裡的 md5 記進 MLflow run**。
    這樣看到一個 run 的時候，你能精確知道它用的是哪一份資料——而不是「大概是九月那版吧」。
    """
    )
    return


@app.cell
def _(MLRUNS, WORK, block, json, mo, sh, step7b, textwrap, yaml):
    step7b
    import mlflow

    _md5 = yaml.safe_load((WORK / "data" / "raw.csv.dvc").read_text())["outs"][0]["md5"]
    _commit = sh("git rev-parse --short HEAD")[1]
    _metrics = json.loads((WORK / "metrics.json").read_text())
    _params = yaml.safe_load((WORK / "params.yaml").read_text())["train"]

    mlflow.set_tracking_uri(f"sqlite:///{MLRUNS}/mlflow.db")
    _exp = mlflow.create_experiment("dvc-bridge", artifact_location=str(MLRUNS / "artifacts"))
    with mlflow.start_run(experiment_id=_exp, run_name="from-dvc") as _run:
        mlflow.log_param("data_md5", _md5)  # ← 就是這一行把兩邊接起來
        mlflow.log_param("git_commit", _commit)
        mlflow.log_params(_params)
        mlflow.log_metric("auc", _metrics["auc"])
    _logged = mlflow.get_run(_run.info.run_id)

    step8 = mo.vstack(
        [
            block(
                textwrap.dedent("""\
                    md5 = yaml.safe_load(open("data/raw.csv.dvc"))["outs"][0]["md5"]

                    with mlflow.start_run():
                        mlflow.log_param("data_md5", md5)                 # 用了哪一份資料
                        mlflow.log_param("git_commit", git_short_sha())   # 用了哪一版程式
                        mlflow.log_metric("auc", metrics["auc"])
                """),
                "python",
            ),
            mo.md("**這個 run 記下來的東西**："),
            block(
                "\n".join(f"{_k} = {_v}" for _k, _v in sorted(_logged.data.params.items()))
                + "\n"
                + "\n".join(f"{_k} = {_v}" for _k, _v in sorted(_logged.data.metrics.items()))
            ),
            mo.md(
                "半年後看到這個 run，你可以：`git checkout <git_commit>` 拿回當時的程式與指標檔、"
                "`dvc checkout` 拿回當時的資料、`dvc repro` 重跑一次——"
                "而且因為 md5 對得上，你會拿到**一模一樣**的模型。"
                "**這就是「可重現」的完整定義**，少任何一塊都做不到。"
            ),
        ]
    )
    step8
    return (step8,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 9️⃣ 換你動手：選一種改動，真的跑一次

    下面這個小工具會**先把工作區還原到 HEAD 那一版**（`git checkout -- .` ＋ `dvc checkout --force`），
    再套用你選的改動，然後真的執行一次 `dvc repro`。

    選之前先自己猜一下：**哪些 stage 會重跑？哪些會被 skip？** 再按下去對答案。

    - 「什麼都不改」→ 兩個 stage 應該都 skip
    - 改參數 → `prepare` skip、`train` 重跑
    - 改資料 → 兩個都要重跑（`prepare` 的依賴變了，它的產物變了，`train` 的依賴也就變了）

    每一輪大約 2–4 秒。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    play = mo.ui.dropdown(
        options=[
            "什麼都不改",
            "max_depth：12 → 4",
            "max_depth：12 → 20",
            "n_estimators：50 → 200",
            "資料補 200 列（2000 → 2200）",
        ],
        value="什麼都不改",
        label="這一輪改什麼：",
    ).form(submit_button_label="執行 dvc repro")
    play
    return (play,)


@app.cell
def _(COLS, WORK, dvc, make_classification, mo, pd, play, sh, step8, term, time, yaml):
    step8
    if play.value is None:
        play_out = mo.callout("選一個改動，按「執行 dvc repro」——會在剛剛那個 repo 裡真的跑一次。", kind="info")
    else:
        _t0 = time.time()
        _reset = [sh("git checkout -- ."), dvc("checkout --force")]
        _choice = play.value
        _note = ""
        if _choice.startswith(("max_depth", "n_estimators")):
            _key, _val = ("max_depth", 4) if "→ 4" in _choice else ("max_depth", 20)
            if _choice.startswith("n_estimators"):
                _key, _val = "n_estimators", 200
            _p = yaml.safe_load((WORK / "params.yaml").read_text())
            _p["train"][_key] = _val
            (WORK / "params.yaml").write_text(yaml.safe_dump(_p, sort_keys=False))
            _steps = [dvc("repro"), dvc("params diff"), dvc("metrics diff")]
            _note = "只有 `train` 重跑——`prepare` 的依賴一個字都沒變。"
        elif _choice.startswith("資料"):
            _X, _y = make_classification(n_samples=200, n_features=12, n_informative=6, random_state=1)
            _extra = pd.DataFrame(_X, columns=COLS).assign(label=_y)
            _cur = pd.read_csv(WORK / "data" / "raw.csv")
            pd.concat([_cur, _extra], ignore_index=True).to_csv(WORK / "data" / "raw.csv", index=False)
            _steps = [dvc("add data/raw.csv"), dvc("repro"), dvc("metrics diff")]
            _note = "資料的 md5 變了 → `prepare` 重跑 → 它的產物變了 → `train` 也得重跑。整條下游全部重算。"
        else:
            _steps = [dvc("status"), dvc("repro")]
            _note = "兩個 stage 都 skip。`dvc repro` 不是「重跑」，是「檢查有沒有必要跑」。"
        play_out = mo.vstack(
            [
                term(*_reset, *_steps),
                mo.md(f"⏱️ 這一輪 **{round(time.time() - _t0, 1)} 秒**。{_note}"),
            ]
        )
    play_out
    return (play_out,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 🏆 延伸挑戰

    1. **LEVEL 1**：把 `n_estimators` 從 50 改成 200，`dvc repro` 之後用
       `dvc params diff` 與 `dvc metrics diff` 看看多花的時間換到多少 AUC。
       再進階一點：**加一個全新的參數** `min_samples_leaf`——想想要改幾個地方。
    2. **LEVEL 2**：加第三個 stage `evaluate`，讀 `model.pkl` 與 `data/test.csv`，
       把 ROC 曲線的點寫成 `plots/roc.csv`（欄位 `fpr,tpr`），並在 `dvc.yaml` 用
       `plots:` 宣告它。跑完 `dvc plots show` 看看 DVC 產出什麼。
    3. **LEVEL 3**：不用自己 clone，直接從別人的 repo 拿一份 DVC 管的資料——
       研究 `dvc get` 與 `dvc import` 的差別，並說明什麼情況下該用哪一個。

    先自己試，卡住再展開下面的參考解答。
    帶得走：下載本檔後 `uvx marimo edit --sandbox dvc-basics_ext.py`
    在自己電腦繼續玩（依賴會自動安裝）。
    """
    )
    return


@app.cell(hide_code=True)
def _(textwrap):
    # LEVEL 2 參考解答用到的兩段程式（實測跑得起來：repro 只跑 evaluate、dvc plots show 產出 HTML）
    ANSWER_EVAL_PY = textwrap.dedent("""\
        import pickle
        import pandas as pd
        from pathlib import Path
        from sklearn.metrics import roc_curve

        model = pickle.load(open("model.pkl", "rb"))
        test = pd.read_csv("data/test.csv")
        prob = model.predict_proba(test.drop(columns="label"))[:, 1]
        fpr, tpr, _ = roc_curve(test["label"], prob)

        Path("plots").mkdir(exist_ok=True)
        pd.DataFrame({"fpr": fpr, "tpr": tpr}).to_csv("plots/roc.csv", index=False)
    """)
    ANSWER_EVAL_STAGE = """  evaluate:
    cmd: python evaluate.py
    deps:
      - model.pkl
      - data/test.csv
      - evaluate.py
    plots:
      - plots/roc.csv:
          x: fpr
          y: tpr
"""
    return ANSWER_EVAL_PY, ANSWER_EVAL_STAGE


@app.cell(hide_code=True)
def _(ANSWER_EVAL_PY, ANSWER_EVAL_STAGE, block, mo):
    mo.accordion(
        {
            "💡 LEVEL 1 參考解答": mo.md(
                r"""
    改 `n_estimators` 只要動 `params.yaml` 一個地方（因為它已經在 `dvc.yaml` 的 `params:` 清單裡）：

    ```text
    # params.yaml
    train:
      max_depth: 12
      n_estimators: 200
    ```

    ```text
    dvc repro
    dvc params diff      # train.n_estimators  50 → 200
    dvc metrics diff     # auc 的變化與 Change 欄
    ```

    **加一個全新的參數要改三個地方**，少一個就出事：

    1. `params.yaml` 加 `min_samples_leaf: 3`
    2. `dvc.yaml` 的 `params:` 清單加一行 `- train.min_samples_leaf`
       ——**沒加的話 DVC 不會知道這個參數變了，改了也不會重跑**（最沉默的坑）
    3. `train.py` 把它傳給模型（本課的寫法是 `**p`，所以這一步自動完成）

    **少了第 2 步會安靜地錯給你看**（實測）：`params.yaml` 明明改了，DVC 卻說什麼都沒變——

    ```text
    $ dvc status
    Data and pipelines are up to date.

    $ dvc repro
    Stage 'train' didn't change, skipping
    Data and pipelines are up to date.
    ```

    因為 DVC 只追蹤 `dvc.yaml` 的 `params:` 清單上有的 key，沒宣告的它看不見。
    反過來，如果 `dvc.yaml` 宣告了一個 `params.yaml` 裡沒有的 key，它會直接擋下來（這個至少有錯誤訊息）：
    `ERROR: failed to reproduce 'train': Parameters 'train.learning_rate' are missing from 'params.yaml'.`
    """
            ),
            "💡 LEVEL 2 參考解答": mo.vstack(
                [
                    mo.md("新增 `evaluate.py`："),
                    block(ANSWER_EVAL_PY, "python"),
                    mo.md("`dvc.yaml` 的 `stages:` 底下，加在 `train` 後面（跟 `train` 同一層縮排）："),
                    block(ANSWER_EVAL_STAGE, "yaml"),
                    mo.md(
                        r"""
    然後 `dvc repro`。實測會看到 `prepare`、`train` 都 skip，只跑 `evaluate`
    （只有它是新的），`dvc dag` 也會多出第三個方框（`train` 與 `prepare` 一起指向它）。

    **怎麼驗證自己做對了**：`dvc plots show` 會產生一個 HTML 檔並把路徑印出來
    （實測輸出像 `file:///tmp/.../dvc_plots/index.html`），打開就是那條 ROC 曲線。
    之後改參數重跑，`dvc plots diff` 可以把新舊兩條曲線畫在同一張圖上比。
    `plots:` 跟 `metrics:` 的差別只有一個：metrics 是幾個數字，plots 是一整串點。
    """
                    ),
                ]
            ),
            "💡 LEVEL 3 提示": mo.md(
                r"""
    兩個指令都能從**別人的 repo** 拿 DVC 管的檔案，差別在「有沒有留下線索」：

    ```text
    dvc get   <repo-url> <path> -o <本地檔名>    # 只下載，什麼都不留
    dvc import <repo-url> <path> -o <本地檔名>   # 下載，並產生一個 .dvc 檔記住來源
    ```

    - **`dvc get`** ＝ 加強版的 `wget`。適合「我只是要一份資料來看看」，
      或是在 CI 腳本裡臨時抓一份東西。你的 repo 裡不會多出任何紀錄。
    - **`dvc import`** 會產生一個 `.dvc` 檔，裡面除了 md5 還記著**來源 repo、路徑、當時的 commit**。
      好處是之後可以 `dvc update <檔名>.dvc` 一鍵拉到上游的新版本——
      適合「這份資料是別的團隊維護的，我要一直跟著他們更新」。

    **怎麼驗證自己做對了**：官方的示範 repo 是 `https://github.com/iterative/dataset-registry`，
    裡面有 `get-started/data.xml`。兩個指令各跑一次（`-o` 指到不同檔名），
    然後 `ls -a` 比對：`get` 只留下資料檔，`import` 多一個 `.dvc` 檔——
    打開來看，裡面會有 `repo:` 區塊記著 `url` 與 `rev_lock`。那個 `rev_lock` 就是「當時是哪一版」。

    （這一題要連外網，molab 可以跑。）
    """
            ),
        }
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 📦 帶回你自己的專案

    在一個已經有 git 的專案裡，把資料交給 DVC 只要這樣：

    ```text
    pip install dvc                       # 要用 S3 就 pip install "dvc[s3]"
    dvc init
    dvc add data/big_file.csv             # → 產生 data/big_file.csv.dvc
    git add data/big_file.csv.dvc data/.gitignore
    git commit -m "track data with dvc"
    dvc remote add -d storage s3://your-bucket/dvcstore
    dvc push
    ```

    **三個新手最常踩的坑**（前面都遇過了，這裡收在一起）：

    1. **檔案已經被 git 追蹤了**，`dvc add` 會直接拒絕：
       `ERROR: output 'data/raw.csv' is already tracked by SCM (e.g. Git).`
       ——要先 `git rm -r --cached data/raw.csv` 把它從 git 拿掉再 add。
    2. **切了 git 版本卻忘了 `dvc checkout`**：不會有任何錯誤訊息，
       你只是安靜地拿舊資料訓練新程式。養成習慣：`git checkout` 之後接一句 `dvc status`。
    3. **只 `git push` 沒有 `dvc push`**：同事 clone 下來 `dvc pull` 會收到
       `WARNING: Some of the cache files do not exist neither locally nor on remote.`
       ——指標檔進了遠端 git，內容卻還在你的硬碟裡。

    下一課是 **ML 測試**：模型訓練出來了、資料版本也管好了，但「這個模型能不能上線」
    這件事要怎麼自動檢查？答案是用 pytest 幫模型寫行為測試。
    """
    )
    return


if __name__ == "__main__":
    app.run()
