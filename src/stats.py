# Статистические функции для сравнения двух групп. Группа 1 - экспериментальная (E), группа 0 - контроль (C).

import numpy as np
from scipy import stats


# SRM: хи-квадрат согласия для размеров групп при ожидаемой доле контроля share_c.
def srm_pvalue(n_c: int, n_e: int, share_c: float = 0.5) -> float:
    n = n_c + n_e
    return stats.chisquare([n_c, n_e], [n * share_c, n * (1 - share_c)]).pvalue


# z-тест для разницы долей с объединённой дисперсией (при нулевой гипотезе доли равны).
def two_prop_ztest(x1: int, n1: int, x0: int, n0: int) -> tuple[float, float]:
    p = (x1 + x0) / (n1 + n0)
    se = np.sqrt(p * (1 - p) * (1 / n1 + 1 / n0))
    z = (x1 / n1 - x0 / n0) / se
    return z, 2 * stats.norm.sf(abs(z))


# Доверительный интервал Вальда для p1 - p0, дисперсии групп раздельно.
def diff_ci(x1: int, n1: int, x0: int, n0: int, alpha: float = 0.05) -> tuple[float, float]:
    p1, p0 = x1 / n1, x0 / n0
    se = np.sqrt(p1 * (1 - p1) / n1 + p0 * (1 - p0) / n0)
    z = stats.norm.ppf(1 - alpha / 2)
    return p1 - p0 - z * se, p1 - p0 + z * se


# Стандартизованная разница средних, пропуски не учитываются.
def smd(x1, x0) -> float:
    x1, x0 = np.asarray(x1, float), np.asarray(x0, float)
    x1, x0 = x1[~np.isnan(x1)], x0[~np.isnan(x0)]
    diff = x1.mean() - x0.mean()
    sd = np.sqrt((x1.var(ddof=1) + x0.var(ddof=1)) / 2)
    if sd == 0:
        return 0.0 if diff == 0 else np.inf
    return diff / sd


def _smd_columns(x: np.ndarray, treated: np.ndarray) -> np.ndarray:
    a, b = x[treated], x[~treated]
    sd = np.sqrt((np.nanvar(a, axis=0, ddof=1) + np.nanvar(b, axis=0, ddof=1)) / 2)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(sd > 0, (np.nanmean(a, axis=0) - np.nanmean(b, axis=0)) / sd, 0.0)


# Общая проверка баланса: насколько часто при случайной перестановке меток групп максимальный |SMD|
# по всем ковариатам не меньше наблюдаемого. Отвечает на вопрос, больше ли перекос, чем даёт случай.
def balance_pvalue(x: np.ndarray, treated: np.ndarray, n_perm: int, rng: np.random.Generator) -> float:
    x, treated = np.asarray(x, float), np.asarray(treated, bool)
    observed = np.nanmax(np.abs(_smd_columns(x, treated)))
    hits = 0
    for _ in range(n_perm):
        hits += np.nanmax(np.abs(_smd_columns(x, rng.permutation(treated)))) >= observed
    return (hits + 1) / (n_perm + 1)
