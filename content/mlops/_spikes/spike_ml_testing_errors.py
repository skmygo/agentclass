# ml-testing 課的「真實錯誤原文」spike：測驗題與教學頁的錯誤輸出全部從這裡抄，不杜撰。
# 跑法：uv run --script content/mlops/_spikes/spike_ml_testing_errors.py
# /// script
# requires-python = ">=3.11"
# dependencies = ["pytest", "numpy", "pandas", "scikit-learn"]
# ///
import contextlib
import io
import os
import shutil
import sys
import tempfile
import textwrap
from pathlib import Path

import pytest

W = Path(tempfile.gettempdir()) / "ml-testing-errors"
shutil.rmtree(W, ignore_errors=True)
W.mkdir(parents=True)
(W / "pytest.ini").write_text("[pytest]\nmarkers =\n    slow: 跑得久的測試\n")


def run(name: str, source: str, args: list[str] | None = None, target: str | None = None) -> None:
    """把一支測試檔寫進暫存目錄、跑一次 pytest，把原文印出來。"""
    path = W / name
    path.write_text(textwrap.dedent(source))
    for mod in [m for m in sys.modules if m.startswith(path.stem)]:
        del sys.modules[mod]  # 同名測試模組會被 sys.modules 快取，改內容重跑要先清掉
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = pytest.main(["-q", "-p", "no:cacheprovider", *(args or []), target or str(path)])
    rel = os.path.relpath(W, Path.cwd())
    out = buf.getvalue().replace(rel + "/", "").replace(str(W) + "/", "")
    print(f"\n{'=' * 78}\n### {name}  args={args or []}  exit={code}\n{'=' * 78}\n{out}")


# ── 1. fixture 名字打錯 ────────────────────────────────────────────────
run(
    "test_fixture_typo.py",
    '''
    import pytest

    @pytest.fixture(scope="module")
    def model():
        return "a model"

    def test_min_perf(modle):          # 少了一個字母
        assert modle is not None
    ''',
)

# ── 2. 浮點數用 == 比 ──────────────────────────────────────────────────
run(
    "test_float_eq.py",
    '''
    def test_float_equality():
        assert 0.1 + 0.2 == 0.3

    def test_metric_equality():
        auc = 0.9684000000000001
        assert auc == 0.9684
    ''',
)

# ── 3. 檔名／函式名沒有 test_ 前綴 ─────────────────────────────────────
(W / "sub").mkdir()
(W / "sub" / "checks_model.py").write_text("def test_min_auc():\n    assert 0.89 >= 0.95\n")
run("sub/_placeholder.txt", "", target=str(W / "sub"))  # 掃資料夾：檔名不對就收不到
run(
    "test_func_name.py",
    '''
    def check_min_auc():               # 函式名沒有 test_ 前綴
        assert 0.89 >= 0.95

    def test_real_one():
        assert True
    ''',
)

# ── 4. parametrize 參數數量不符 ────────────────────────────────────────
run(
    "test_param_count.py",
    '''
    import pytest

    @pytest.mark.parametrize("col,sign", [("f2", +1), ("f3", -1), "f9"])
    def test_directional(col, sign):
        assert sign in (1, -1)
    ''',
)
run(
    "test_param_missing_arg.py",
    '''
    import pytest

    @pytest.mark.parametrize("col,sign", [("f2", +1), ("f3", -1)])
    def test_directional(col):         # 少接一個參數
        assert col.startswith("f")
    ''',
)

# ── 5. pytest.raises 沒炸 ──────────────────────────────────────────────
run(
    "test_raises.py",
    '''
    import pandas as pd
    import pytest

    def test_missing_column_raises():
        df = pd.DataFrame({"f0": [1.0], "f1": [2.0]})
        with pytest.raises(ValueError, match="feature names"):
            df.drop(columns="f1")      # 這行不會拋例外
    ''',
)

# ── 6. -k 選不到任何測試 ───────────────────────────────────────────────
run(
    "test_select.py",
    '''
    def test_contract_shape():
        assert True

    def test_perf_min_auc():
        assert True
    ''',
    args=["-k", "behaviour"],
)

# ── 7. 沒註冊的 mark ───────────────────────────────────────────────────
(W / "pytest.ini").unlink()
run(
    "test_unknown_mark.py",
    '''
    import pytest

    @pytest.mark.slwo                  # 打錯的 mark
    def test_retrain():
        assert True
    ''',
    args=["-W", "default"],
)
(W / "pytest.ini").write_text("[pytest]\nmarkers =\n    slow: 跑得久的測試\n")

# ── 8. 真的模型：斷言訊息長什麼樣 ──────────────────────────────────────
run(
    "test_real_model.py",
    '''
    import numpy as np
    import pandas as pd
    from sklearn.datasets import make_classification
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import train_test_split

    def test_min_auc_bare():
        X, y = make_classification(n_samples=2000, n_features=12, n_informative=6, random_state=0)
        Xdf = pd.DataFrame(X, columns=[f"f{i}" for i in range(12)])
        Xtr, Xte, ytr, yte = train_test_split(Xdf, y, test_size=0.25, random_state=0)
        m = RandomForestClassifier(n_estimators=100, max_depth=1, random_state=0).fit(Xtr, ytr)
        auc = roc_auc_score(yte, m.predict_proba(Xte)[:, 1])
        assert auc >= 0.95                                   # 沒有訊息

    def test_min_auc_with_message():
        auc = 0.8902718926553672
        assert auc >= 0.95, f"AUC {auc:.4f} 低於上線門檻 0.95"
    ''',
)

# ── 9. 少了欄位：sklearn 的原文（合約測試要 match 的字串） ─────────────
run(
    "test_sklearn_msgs.py",
    '''
    import pandas as pd
    from sklearn.datasets import make_classification
    from sklearn.ensemble import RandomForestClassifier

    def _fitted():
        X, y = make_classification(n_samples=400, n_features=12, n_informative=6, random_state=0)
        Xdf = pd.DataFrame(X, columns=[f"f{i}" for i in range(12)])
        return RandomForestClassifier(n_estimators=10, max_depth=4, random_state=0).fit(Xdf, y), Xdf

    def test_missing_column():
        m, X = _fitted()
        m.predict(X.drop(columns="f11"))

    def test_extra_column():
        m, X = _fitted()
        m.predict(X.assign(extra=1.0))

    def test_reordered_columns():
        m, X = _fitted()
        m.predict(X[list(reversed(X.columns))])
    ''',
    args=["--tb=line"],
)

print("\n完成。所有輸出都是本機真跑 pytest", pytest.__version__, "的原文。")
