# 候選課 spike：DVC 資料版本控制與 dvc.yaml 管線（在暫存 git repo 內用 CLI）
# /// script
# requires-python = ">=3.11"
# dependencies = ["dvc>=3.50", "scikit-learn", "pandas", "numpy", "pyyaml"]
# ///
import os, subprocess, sys, tempfile, textwrap, time
from pathlib import Path
W = Path(tempfile.mkdtemp(prefix="dvc-")); os.chdir(W)
def sh(cmd, check=True):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False)
    out = (r.stdout + r.stderr).strip()
    print(f"$ {cmd}\n{out[:400]}" if out else f"$ {cmd}")
    if check and r.returncode != 0: raise SystemExit(f"failed: {cmd}")
    return out
t0 = time.time()
sh("git init -q && git config user.email a@b.c && git config user.name t")
sh(f"{sys.executable} -m dvc init -q")
import pandas as pd, numpy as np
from sklearn.datasets import make_classification
X, y = make_classification(n_samples=2000, n_features=12, n_informative=6, random_state=0)
Path("data").mkdir(); pd.DataFrame(X, columns=[f"f{i}" for i in range(12)]).assign(label=y).to_csv("data/raw.csv", index=False)
sh(f"{sys.executable} -m dvc add data/raw.csv")
print("raw.csv.dvc:", Path("data/raw.csv.dvc").read_text()[:200])
print(".gitignore:", Path("data/.gitignore").read_text().strip())
Path("params.yaml").write_text("train:\n  max_depth: 4\n  n_estimators: 50\n")
Path("train.py").write_text(textwrap.dedent('''
    import json, yaml, pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import roc_auc_score
    p = yaml.safe_load(open("params.yaml"))["train"]
    df = pd.read_csv("data/raw.csv"); X, y = df.drop(columns="label"), df["label"]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=0)
    m = RandomForestClassifier(random_state=0, **p).fit(Xtr, ytr)
    json.dump({"auc": roc_auc_score(yte, m.predict_proba(Xte)[:, 1])}, open("metrics.json", "w"))
'''))
Path("dvc.yaml").write_text(textwrap.dedent('''
    stages:
      train:
        cmd: python train.py
        deps: [data/raw.csv, train.py]
        params: [train.max_depth, train.n_estimators]
        metrics: [metrics.json]
'''))
sh(f"{sys.executable} -m dvc repro")
sh("git add -A && git commit -qm v1")
sh(f"{sys.executable} -m dvc repro")   # 沒改 → skip
Path("params.yaml").write_text("train:\n  max_depth: 12\n  n_estimators: 50\n")
sh(f"{sys.executable} -m dvc repro")
sh(f"{sys.executable} -m dvc params diff")
sh(f"{sys.executable} -m dvc metrics diff")
sh(f"{sys.executable} -m dvc dag")
print("cache files:", sum(1 for _ in Path(".dvc/cache").rglob("*") if _.is_file()))
print("elapsed", round(time.time() - t0, 1), "s")
