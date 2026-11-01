# Витрина experiment_summary. Бутстреп и p-value считает Python, остальное - sql/mart.sql.
from . import config, db, effects


def build(con) -> None:
    main, sens = effects.decision_inputs(con)
    stats_df = main[["experiment_id", "p", "boot_lo", "boot_hi"]].copy()
    stats_df["sens_boot_hi"] = stats_df.experiment_id.map({effects.SENSITIVITY_ID: sens.boot_hi})
    con.register("stats_df", stats_df)
    con.execute("create or replace table effect_stats as select * from stats_df")
    con.unregister("stats_df")
    con.execute(f"set variable excluded = {effects.EXCLUDED}")
    con.execute(db.read("mart.sql"))


if __name__ == "__main__":
    con = db.connect()
    build(con)
    out = config.DATA_DIR / "experiment_summary.csv"
    con.execute(f"copy experiment_summary to '{out}' (header)")
    print(con.sql("select experiment_id, effect, ci_lo, ci_hi, p_bh, decision from experiment_summary"))
    print("сохранено в", out)
