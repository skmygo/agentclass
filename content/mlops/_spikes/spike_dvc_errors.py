# dvc-basics 課的錯誤原文蒐集（測驗題與 notebook 的「壞掉時長怎樣」都引用這裡的實測輸出）
# 跑法：uv run --script content/mlops/_spikes/spike_dvc_errors.py
# /// script
# requires-python = ">=3.11"
# dependencies = ["dvc>=3.50", "scikit-learn", "pandas", "numpy", "pyyaml"]
# ///
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

TMP = Path(tempfile.gettempdir())
PY = sys.executable


def make_env():
    return {
        **os.environ,
        "PATH": str(Path(PY).parent) + os.pathsep + os.environ.get("PATH", ""),
        "DVC_NO_ANALYTICS": "1",
    }


def run(cmd, cwd, show=True, limit=1200):
    r = subprocess.run(
        cmd, shell=True, cwd=cwd, capture_output=True, text=True, env=make_env(), check=False
    )
    out = (r.stdout + r.stderr).strip()
    if show:
        print(f"\n$ {cmd}\n{out[:limit]}\n  [rc={r.returncode}]")
    return out


def fresh(name, with_git=True, with_dvc=True, with_data=True):
    """開一個乾淨的暫存 repo。"""
    w = TMP / f"dvcerr-{name}"
    shutil.rmtree(w, ignore_errors=True)
    w.mkdir(parents=True)
    if with_git:
        run("git init -q", w, show=False)
        run("git config user.email a@b.c && git config user.name t", w, show=False)
    if with_dvc:
        run(f"{PY} -m dvc init -q", w, show=False)
        run(f"{PY} -m dvc config core.analytics false", w, show=False)
    if with_data:
        (w / "data").mkdir(exist_ok=True)
        import numpy as np
        import pandas as pd

        rng = np.random.default_rng(0)
        pd.DataFrame(rng.normal(size=(200, 3)), columns=list("abc")).assign(
            label=rng.integers(0, 2, 200)
        ).to_csv(w / "data" / "raw.csv", index=False)
    return w


def sec(title):
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


# ── 1. 沒有 dvc init 就 dvc add ───────────────────────────────────────────
sec("1. 沒有 dvc init 就 dvc add（只有 git，沒有 .dvc/）")
w = fresh("noinit", with_dvc=False)
run(f"{PY} -m dvc add data/raw.csv", w)

sec("1b. 連 git 都沒有就 dvc init")
w = fresh("nogit", with_git=False, with_dvc=False, with_data=False)
run(f"{PY} -m dvc init", w)

# ── 2. dvc add 一個已經被 git 追蹤的檔 ────────────────────────────────────
sec("2. dvc add 一個已經被 git 追蹤（已 commit）的檔案")
w = fresh("gittracked")
run("git add -f data/raw.csv && git commit -qm 'raw into git'", w, show=False)
run(f"{PY} -m dvc add data/raw.csv", w)
print("\n（提示：DVC 教的解法）")
run("git rm -r --cached data/raw.csv -q && git commit -qm untrack", w, show=False)
run(f"{PY} -m dvc add data/raw.csv", w)

# ── 3. dvc repro：stage 的 deps 不存在 ────────────────────────────────────
sec("3. dvc repro 時 deps 指到不存在的檔")
w = fresh("missingdep")
(w / "train.py").write_text("print('hi')\n")
(w / "dvc.yaml").write_text(
    textwrap.dedent("""
    stages:
      train:
        cmd: python train.py
        deps:
          - data/clean.csv
          - train.py
        outs:
          - model.txt
    """)
)
run(f"{PY} -m dvc repro", w)

sec("3b. stage 的 cmd 本身失敗（train.py 丟例外）")
w = fresh("cmdfail")
(w / "train.py").write_text("import pandas as pd\npd.read_csv('data/nope.csv')\n")
(w / "dvc.yaml").write_text(
    textwrap.dedent("""
    stages:
      train:
        cmd: python train.py
        deps:
          - train.py
        outs:
          - model.txt
    """)
)
run(f"{PY} -m dvc repro", w)

sec("3c. cmd 跑成功但沒有產出宣告的 outs")
w = fresh("nooutput")
(w / "train.py").write_text("print('did nothing')\n")
(w / "dvc.yaml").write_text(
    textwrap.dedent("""
    stages:
      train:
        cmd: python train.py
        deps:
          - train.py
        outs:
          - model.txt
    """)
)
run(f"{PY} -m dvc repro", w)

# ── 4. dvc.yaml 語法錯 ────────────────────────────────────────────────────
sec("4a. dvc.yaml 縮排壞掉（不是合法 YAML）")
w = fresh("badyaml")
(w / "dvc.yaml").write_text("stages:\n  train:\n  cmd: python train.py\n   deps: [a]\n")
run(f"{PY} -m dvc repro", w)

sec("4b. dvc.yaml 是合法 YAML 但欄位打錯（dep 不是 deps）")
w = fresh("badkey")
(w / "train.py").write_text("open('model.txt','w').write('x')\n")
(w / "dvc.yaml").write_text(
    textwrap.dedent("""
    stages:
      train:
        cmd: python train.py
        dep:
          - train.py
        outs:
          - model.txt
    """)
)
run(f"{PY} -m dvc repro", w)

sec("4c. params 指到 params.yaml 裡沒有的 key")
w = fresh("badparam")
(w / "params.yaml").write_text("train:\n  max_depth: 4\n")
(w / "train.py").write_text("open('model.txt','w').write('x')\n")
(w / "dvc.yaml").write_text(
    textwrap.dedent("""
    stages:
      train:
        cmd: python train.py
        deps:
          - train.py
        params:
          - train.learning_rate
        outs:
          - model.txt
    """)
)
run(f"{PY} -m dvc repro", w)

sec("4d. repro 指定不存在的 stage 名稱")
w = fresh("badstage")
(w / "train.py").write_text("open('model.txt','w').write('x')\n")
(w / "dvc.yaml").write_text(
    textwrap.dedent("""
    stages:
      train:
        cmd: python train.py
        deps:
          - train.py
        outs:
          - model.txt
    """)
)
run(f"{PY} -m dvc repro trian", w)

# ── 5. 沒設 remote 就 dvc push / pull ─────────────────────────────────────
sec("5. 沒設 remote 就 dvc push / dvc pull")
w = fresh("noremote")
run(f"{PY} -m dvc add data/raw.csv", w, show=False)
run(f"{PY} -m dvc push", w)
run(f"{PY} -m dvc pull", w)
print("\n（設了 remote，但遠端沒有這份資料時的 pull）")
run(f"{PY} -m dvc remote add -d empty {TMP / 'dvcerr-empty-remote'}", w, show=False)
shutil.rmtree(TMP / "dvcerr-empty-remote", ignore_errors=True)
(TMP / "dvcerr-empty-remote").mkdir(parents=True)
shutil.rmtree(w / ".dvc" / "cache", ignore_errors=True)
(w / "data" / "raw.csv").unlink()
run(f"{PY} -m dvc pull", w)

# ── 6. dvc checkout 時工作區有沒 add 的修改 ───────────────────────────────
sec("6. dvc checkout 時工作區的資料被改過（還沒 dvc add）")
w = fresh("dirty")
run(f"{PY} -m dvc add data/raw.csv", w, show=False)
run("git add -A && git commit -qm v1", w, show=False)
with (w / "data" / "raw.csv").open("a") as fh:
    fh.write("9,9,9,1\n")
run(f"{PY} -m dvc status", w)
run(f"{PY} -m dvc checkout", w)
print("\n（加 --force 才會覆蓋掉工作區的修改）")
run(f"{PY} -m dvc checkout --force", w)

sec("6b. cache 被刪掉之後 dvc checkout（沒有 remote 可以拿）")
w = fresh("nocache")
run(f"{PY} -m dvc add data/raw.csv", w, show=False)
run("git add -A && git commit -qm v1", w, show=False)
shutil.rmtree(w / ".dvc" / "cache", ignore_errors=True)
(w / "data" / "raw.csv").unlink()
run(f"{PY} -m dvc checkout", w)

sec("7. 忘了 dvc checkout：git 切了版本、資料還是舊的（沉默，不報錯）")
w = fresh("forgot")
import pandas as pd  # noqa: E402

run(f"{PY} -m dvc add data/raw.csv", w, show=False)
run("git add -A && git commit -qm v1", w, show=False)
df = pd.read_csv(w / "data" / "raw.csv")
df.loc[0, "label"] = 1 - int(df.loc[0, "label"])
df.to_csv(w / "data" / "raw.csv", index=False)
run(f"{PY} -m dvc add data/raw.csv", w, show=False)
run("git commit -qam v2", w, show=False)
print("目前工作區第 0 列 label:", pd.read_csv(w / "data" / "raw.csv").loc[0, "label"])
run("git checkout -q HEAD~1", w)
print("git checkout HEAD~1 之後，指標檔 md5:")
print((w / "data" / "raw.csv.dvc").read_text().strip())
print("→ 但工作區檔案的第 0 列 label 還是:", pd.read_csv(w / "data" / "raw.csv").loc[0, "label"])
run(f"{PY} -m dvc status", w)
run(f"{PY} -m dvc checkout", w)
print("→ dvc checkout 之後才變成:", pd.read_csv(w / "data" / "raw.csv").loc[0, "label"])

print("\n\n全部錯誤情境跑完。")
