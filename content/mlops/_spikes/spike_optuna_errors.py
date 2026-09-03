# 課程測驗題用的「真實錯誤原文」蒐集器（optuna-hpo 課）
# 跑法：uv run --script content/mlops/_spikes/spike_optuna_errors.py
# /// script
# requires-python = ">=3.11"
# dependencies = ["optuna>=4.0", "scikit-learn", "numpy"]
# ///
import logging
import tempfile
import warnings
from pathlib import Path

import optuna

warnings.filterwarnings("ignore")
optuna.logging.set_verbosity(optuna.logging.WARNING)
logging.getLogger("optuna").setLevel(logging.WARNING)
print("optuna", optuna.__version__)
W = Path(tempfile.mkdtemp())


def show(title, fn):
    print(f"\n=== {title} ===")
    try:
        out = fn()
        print("NO ERROR ->", out)
    except Exception as e:  # noqa: BLE001
        print(f"{type(e).__name__}: {e}")


# 1) suggest_int 的 low > high
def _bad_range():
    s = optuna.create_study()
    return s.optimize(lambda t: t.suggest_int("max_depth", 16, 2), n_trials=1)


show("suggest_int low > high", _bad_range)


# 2) 同一個參數名在不同 trial 用了兩種 distribution
def _mixed_dist():
    s = optuna.create_study(sampler=optuna.samplers.TPESampler(seed=0))

    def obj(t):
        if t.number == 0:
            return t.suggest_int("lr", 1, 10)
        return t.suggest_float("lr", 0.0, 1.0)

    return s.optimize(obj, n_trials=2)


show("same param, two distributions", _mixed_dist)


# 2b) 同一個 trial 內同名參數換範圍
def _same_trial_change():
    s = optuna.create_study(sampler=optuna.samplers.TPESampler(seed=0))

    def obj(t):
        a = t.suggest_int("n", 1, 10)
        b = t.suggest_int("n", 1, 100)
        return a + b

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        s.optimize(obj, n_trials=1)
    return (f"params={s.trials[0].params}; warnings="
            f"{[str(w.message)[:120] for w in caught]}")


show("same trial, same name different range", _same_trial_change)


# 3) objective 回傳 None（不會拋錯——trial 靜靜變 FAIL）
def _return_none():
    s = optuna.create_study()
    s.optimize(lambda t: None, n_trials=2)
    states = [t.state.name for t in s.trials]
    try:
        best = s.best_value
    except Exception as e:  # noqa: BLE001
        best = f"{type(e).__name__}: {e}"
    return f"states={states}; best_value -> {best}"


show("objective returns None", _return_none)


# 3b) objective 回傳 NaN（不會拋錯，但 trial 變 FAIL）
def _return_nan():
    s = optuna.create_study(direction="maximize")
    s.optimize(lambda t: float("nan"), n_trials=2)
    print("states:", [t.state.name for t in s.trials])
    return s.best_value


show("objective returns NaN then best_value", _return_nan)


# 3c) objective 回傳字串
def _return_str():
    s = optuna.create_study()
    return s.optimize(lambda t: "0.97", n_trials=1)


show("objective returns str", _return_str)


# 4) direction 打錯字
def _bad_direction():
    return optuna.create_study(direction="maximise")


show("direction typo 'maximise'", _bad_direction)


# 5) 同名 study 撞 storage（load_if_exists=False）
DB = f"sqlite:///{W}/dup.db"


def _dup_study():
    optuna.create_study(study_name="rf-hpo", storage=DB)
    return optuna.create_study(study_name="rf-hpo", storage=DB)


show("duplicate study_name in storage", _dup_study)


def _dup_ok():
    s = optuna.create_study(study_name="rf-hpo", storage=DB, load_if_exists=True)
    return f"loaded, n_trials={len(s.trials)}"


show("same name with load_if_exists=True", _dup_ok)


def _load_missing():
    return optuna.load_study(study_name="not-there", storage=DB)


show("load_study on missing name", _load_missing)


# 6) 多目標 study 上呼叫 best_trial / best_value
def _multi_best():
    s = optuna.create_study(directions=["maximize", "minimize"], sampler=optuna.samplers.TPESampler(seed=0))
    s.optimize(lambda t: (t.suggest_float("a", 0, 1), t.suggest_int("n", 1, 100)), n_trials=6)
    return s.best_trial


show("best_trial on multi-objective study", _multi_best)


def _multi_ok():
    s = optuna.create_study(directions=["maximize", "minimize"], sampler=optuna.samplers.TPESampler(seed=0))
    s.optimize(lambda t: (t.suggest_float("a", 0, 1), t.suggest_int("n", 1, 100)), n_trials=12)
    front = [(round(t.values[0], 3), t.values[1]) for t in s.best_trials]
    return f"{len(s.best_trials)} pareto trials: {sorted(front)}"


show("best_trials on multi-objective study", _multi_ok)


def _multi_single_return():
    s = optuna.create_study(directions=["maximize", "minimize"])
    s.optimize(lambda t: t.suggest_float("a", 0, 1), n_trials=1)
    return f"states={[t.state.name for t in s.trials]}"


show("multi-objective study but objective returns one value", _multi_single_return)


# 7) 單目標 study 回傳 tuple
def _single_tuple():
    s = optuna.create_study(direction="maximize")
    s.optimize(lambda t: (t.suggest_float("a", 0, 1), 1.0), n_trials=1)
    return f"states={[t.state.name for t in s.trials]}"


show("single-objective study but objective returns tuple", _single_tuple)


# 8) pruning 沒有 report 就 should_prune
def _prune_no_report():
    s = optuna.create_study(pruner=optuna.pruners.MedianPruner(n_startup_trials=0))

    def obj(t):
        x = t.suggest_float("x", 0, 1)
        if t.should_prune():
            raise optuna.TrialPruned
        return x

    s.optimize(obj, n_trials=5)
    return f"states={[t.state.name for t in s.trials]}"


show("should_prune without report", _prune_no_report)


# 9) importance 在 trial 太少 / 全部同分時
def _importance_one():
    s = optuna.create_study(direction="maximize")
    s.optimize(lambda t: t.suggest_float("a", 0, 1) + t.suggest_int("b", 1, 5), n_trials=1)
    return optuna.importance.get_param_importances(s)


show("get_param_importances with 1 trial", _importance_one)


def _importance_constant():
    s = optuna.create_study(direction="maximize")
    s.optimize(lambda t: 0.5 + 0 * t.suggest_float("a", 0, 1), n_trials=8)
    return optuna.importance.get_param_importances(s)


show("get_param_importances with constant objective", _importance_constant)


# 10) 搜尋空間動態改變後 best_params 只含實際用到的鍵
def _conditional_space():
    s = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=0))

    def obj(t):
        kind = t.suggest_categorical("kind", ["rf", "logreg"])
        if kind == "rf":
            return 0.9 + 0.001 * t.suggest_int("max_depth", 2, 16)
        return 0.8 + 0.01 * t.suggest_float("C", 0.1, 1.0)

    s.optimize(obj, n_trials=8)
    return f"best_params={s.best_params}; all keys seen={sorted({k for t in s.trials for k in t.params})}"


show("conditional search space best_params", _conditional_space)
print("\nDONE")
