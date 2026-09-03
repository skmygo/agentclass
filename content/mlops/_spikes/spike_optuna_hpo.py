# 候選課 spike：Optuna 自動調參 × MLflow（每個 trial 一個 nested run）
# /// script
# requires-python = ">=3.11"
# dependencies = ["optuna>=4.0", "mlflow>=3.0", "scikit-learn", "pandas", "numpy"]
# ///
import logging, tempfile, time, warnings
from pathlib import Path
import mlflow, optuna, pandas as pd
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, train_test_split
warnings.filterwarnings("ignore"); logging.getLogger("mlflow").setLevel(logging.ERROR); optuna.logging.set_verbosity(optuna.logging.WARNING)
print("optuna", optuna.__version__)
W = Path(tempfile.mkdtemp()); mlflow.set_tracking_uri(f"sqlite:///{W}/m.db")
mlflow.create_experiment("hpo", artifact_location=str(W/"art")); mlflow.set_experiment("hpo")
X, y = make_classification(n_samples=2000, n_features=12, n_informative=6, random_state=0)
Xdf = pd.DataFrame(X, columns=[f"f{i}" for i in range(12)])
Xtr, Xte, ytr, yte = train_test_split(Xdf, y, test_size=0.25, random_state=0)

def objective(trial):
    params = {"n_estimators": trial.suggest_int("n_estimators", 20, 200, step=20),
              "max_depth": trial.suggest_int("max_depth", 2, 16),
              "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 10),
              "max_features": trial.suggest_categorical("max_features", ["sqrt", "log2", None])}
    with mlflow.start_run(run_name=f"trial-{trial.number}", nested=True):
        mlflow.log_params(params)
        score = cross_val_score(RandomForestClassifier(random_state=0, **params), Xtr, ytr, cv=3, scoring="roc_auc").mean()
        mlflow.log_metric("cv_auc", score)
        trial.set_user_attr("mlflow_run", mlflow.active_run().info.run_id)
    return score

t0 = time.time()
study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=0), study_name="rf-hpo")
with mlflow.start_run(run_name="optuna-study") as parent:
    study.optimize(objective, n_trials=25)
    mlflow.log_params({f"best_{k}": v for k, v in study.best_params.items()}); mlflow.log_metric("best_cv_auc", study.best_value)
print(f"25 trials in {time.time()-t0:.1f}s; best {study.best_value:.4f} params {study.best_params}")
df = study.trials_dataframe()[["number", "value", "params_max_depth", "params_n_estimators", "state"]]
print(df.sort_values("value", ascending=False).head(5).to_string())
print("importance:", {k: round(v, 3) for k, v in optuna.importance.get_param_importances(study).items()})
# pruning demo
def objective_prune(trial):
    n = trial.suggest_int("n_estimators", 20, 200, step=20); d = trial.suggest_int("max_depth", 2, 16)
    for step in range(1, 4):
        m = RandomForestClassifier(n_estimators=n * step // 3, max_depth=d, random_state=0).fit(Xtr, ytr)
        s = m.score(Xte, yte); trial.report(s, step)
        if trial.should_prune(): raise optuna.TrialPruned()
    return s
st2 = optuna.create_study(direction="maximize", pruner=optuna.pruners.MedianPruner(n_startup_trials=5), sampler=optuna.samplers.TPESampler(seed=0))
t0 = time.time(); st2.optimize(objective_prune, n_trials=20)
pruned = sum(t.state == optuna.trial.TrialState.PRUNED for t in st2.trials)
print(f"pruning: {pruned}/20 pruned in {time.time()-t0:.1f}s, best {st2.best_value:.4f}")
runs = mlflow.search_runs(experiment_names=["hpo"], filter_string=f"tags.mlflow.parentRunId = '{parent.info.run_id}'", order_by=["metrics.cv_auc DESC"])
print("mlflow child runs:", len(runs), "top:", runs.iloc[0]["tags.mlflow.runName"], round(runs.iloc[0]["metrics.cv_auc"], 4))
# storage sqlite for study persistence
st3 = optuna.create_study(study_name="persist", storage=f"sqlite:///{W}/optuna.db", direction="maximize", load_if_exists=True)
st3.optimize(lambda t: t.suggest_float("x", -1, 1) ** 2, n_trials=5)
print("persisted trials:", len(optuna.load_study(study_name="persist", storage=f"sqlite:///{W}/optuna.db").trials))
