# 候選課 spike：ML 測試——pytest 在 notebook 內跑：資料測試、模型行為測試（不變性／方向性／最低功能）、上線前合約測試
# /// script
# requires-python = ">=3.11"
# dependencies = ["pytest", "scikit-learn", "pandas", "numpy", "mlflow>=3.0"]
# ///
import io, contextlib, tempfile, textwrap, time
from pathlib import Path
import numpy as np, pandas as pd, pytest
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
X, y = make_classification(n_samples=2000, n_features=12, n_informative=6, random_state=0)
cols=[f"f{i}" for i in range(12)]; Xdf=pd.DataFrame(X, columns=cols)
Xtr, Xte, ytr, yte = train_test_split(Xdf, y, test_size=0.25, random_state=0)
rf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=0).fit(Xtr, ytr)
W = Path(tempfile.mkdtemp()); import pickle; (W/"model.pkl").write_bytes(pickle.dumps(rf)); Xte.assign(label=yte).to_csv(W/"test.csv", index=False)
(W/"test_model.py").write_text(textwrap.dedent('''
    import pickle, numpy as np, pandas as pd, pytest
    from pathlib import Path
    HERE = Path(__file__).parent
    @pytest.fixture(scope="module")
    def model(): return pickle.loads((HERE/"model.pkl").read_bytes())
    @pytest.fixture(scope="module")
    def data(): return pd.read_csv(HERE/"test.csv")
    def test_min_performance(model, data):
        X, y = data.drop(columns="label"), data["label"]
        assert model.score(X, y) >= 0.90
    def test_prediction_shape_and_range(model, data):
        p = model.predict_proba(data.drop(columns="label"))
        assert p.shape == (len(data), 2) and ((p >= 0) & (p <= 1)).all()
    def test_invariance_noise(model, data):
        X = data.drop(columns="label").head(200)
        base = model.predict(X); noisy = model.predict(X + np.random.default_rng(0).normal(0, 0.01, X.shape))
        assert (base == noisy).mean() >= 0.98
    def test_directional_f3(model, data):
        X = data.drop(columns="label").head(200)
        p0 = model.predict_proba(X)[:, 1]; p1 = model.predict_proba(X.assign(f3=X["f3"] + 2))[:, 1]
        assert (p1 - p0).mean() != 0   # 故意鬆：只確認有影響
    def test_no_missing_columns(model, data):
        with pytest.raises(Exception):
            model.predict(data.drop(columns=["label", "f11"]))
    def test_deterministic(model, data):
        X = data.drop(columns="label").head(50)
        assert (model.predict_proba(X) == model.predict_proba(X)).all()
    @pytest.mark.parametrize("col", ["f0", "f3"])
    def test_feature_matters(model, data, col):
        X = data.drop(columns="label").head(300)
        shuffled = X.copy(); shuffled[col] = shuffled[col].sample(frac=1, random_state=0).values
        y = data["label"].head(300)
        assert model.score(X, y) - model.score(shuffled, y) > 0.0
'''))
buf = io.StringIO(); t0=time.time()
with contextlib.redirect_stdout(buf):
    code = pytest.main(["-q", "-p", "no:cacheprovider", str(W/"test_model.py")])
out = buf.getvalue(); print(out[-600:]); print("exit code", code, "in", round(time.time()-t0,1), "s")
# 讓一個失敗看看訊息
(W/"test_fail.py").write_text("def test_min_perf_strict():\n    assert 0.916 >= 0.95, 'accuracy 0.916 below gate 0.95'\n")
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    code2 = pytest.main(["-q", "-p", "no:cacheprovider", str(W/"test_fail.py")])
print(buf.getvalue()[-500:]); print("exit code", code2)
