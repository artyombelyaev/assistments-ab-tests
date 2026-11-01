# Эффект на долю завершивших: таблицы по выборкам и расчёт z-теста и интервалов.
import numpy as np
import pandas as pd

from . import config, db, stats

N_BOOT = 10_000
# Группы несравнимы (ноутбук 02), в решения не входит.
EXCLUDED = 263057
# В E рано бросившие без пары в C: проверяю устойчивость, добавляя их в C.
SENSITIVITY_ID = 256027
MISSING_QUITTERS = 6


# Завершившие по группам в одну строку на эксперимент и выборку: all, experienced, video_viewers.
def completion_wide(con) -> pd.DataFrame:
    comp = db.run(con, "groups.sql", "completion_by_sample")
    wide = comp.pivot_table(index=["experiment_id", "sample"], columns="grp", values=["n", "n_done"]).reset_index()
    wide.columns = ["experiment_id", "sample", "n_c", "n_e", "done_c", "done_e"]
    wide[["n_c", "n_e", "done_c", "done_e"]] = wide[["n_c", "n_e", "done_c", "done_e"]].astype(int)
    return wide


# Бутстреп берёт числа из rng по порядку строк, поэтому при одном сиде и порядке результат воспроизводится.
def effects(wide: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for r in wide.itertuples():
        z, p = stats.two_prop_ztest(r.done_e, r.n_e, r.done_c, r.n_c)
        lo, hi = stats.bootstrap_diff_ci(r.done_e, r.n_e, r.done_c, r.n_c, N_BOOT, rng)
        wlo, whi = stats.diff_ci(r.done_e, r.n_e, r.done_c, r.n_c)
        rows.append({"experiment_id": r.experiment_id, "n_c": r.n_c, "n_e": r.n_e,
                     "rate_c": r.done_c / r.n_c, "rate_e": r.done_e / r.n_e,
                     "diff": r.done_e / r.n_e - r.done_c / r.n_c, "z": z, "p": p,
                     "boot_lo": lo, "boot_hi": hi, "wald_lo": wlo, "wald_hi": whi})
    return pd.DataFrame(rows)


# Доля увидевших условие и симметричен ли триггер (как в ноутбуке 02).
def trigger_table(con) -> pd.DataFrame:
    g = db.run(con, "groups.sql", "group_sizes")
    g["all_experienced"] = (g.n_exp_c == g.n_c) & (g.n_exp_e == g.n_e)
    g["trigger_p"] = [
        np.nan if full else stats.two_prop_ztest(xe, ne, xc, nc)[1]
        for full, xe, ne, xc, nc in zip(g.all_experienced, g.n_exp_e, g.n_e, g.n_exp_c, g.n_c)
    ]
    g["trigger_share"] = (g.n_exp_c + g.n_exp_e) / (g.n_c + g.n_e)
    g["symmetric"] = ~g.all_experienced & (g.trigger_p >= 0.05)
    return g


# Основная выборка и проверка 256027 в том же порядке бутстрепа, что в ноутбуке 03, чтобы интервалы совпадали.
def decision_inputs(con) -> tuple[pd.DataFrame, pd.Series]:
    wide = completion_wide(con)
    groups = trigger_table(con)
    rng = np.random.default_rng(config.SEED)
    main = effects(wide[wide["sample"] == "all"], rng)
    effects(wide[(wide["sample"] == "experienced") & wide.experiment_id.isin(groups[groups.symmetric].experiment_id)], rng)
    effects(wide[wide["sample"] == "video_viewers"], rng)
    adj = wide[(wide["sample"] == "all") & (wide.experiment_id == SENSITIVITY_ID)].copy()
    adj["n_c"] += MISSING_QUITTERS
    return main, effects(adj, rng).iloc[0]
