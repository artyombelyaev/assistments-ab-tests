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


# Перцентильный бутстреп для p1 - p0. Для 0/1-метрики пересэмплирование строк группы - это биномиальная выборка
# с долей группы, поэтому строки не нужны.
def bootstrap_diff_ci(x1: int, n1: int, x0: int, n0: int, n_boot: int, rng: np.random.Generator,
                      alpha: float = 0.05) -> tuple[float, float]:
    diff = rng.binomial(n1, x1 / n1, n_boot) / n1 - rng.binomial(n0, x0 / n0, n_boot) / n0
    return tuple(np.quantile(diff, [alpha / 2, 1 - alpha / 2]))


# Перцентильный бутстреп для разницы средних, строки пересэмплируются внутри каждой группы.
def bootstrap_mean_diff_ci(a1, a0, n_boot: int, rng: np.random.Generator, alpha: float = 0.05) -> tuple[float, float]:
    a1, a0 = np.asarray(a1, float), np.asarray(a0, float)
    m1 = a1[rng.integers(0, len(a1), (n_boot, len(a1)))].mean(axis=1)
    m0 = a0[rng.integers(0, len(a0), (n_boot, len(a0)))].mean(axis=1)
    return tuple(np.quantile(m1 - m0, [alpha / 2, 1 - alpha / 2]))


# Минимальный обнаружимый эффект для разницы долей при базовой доле p0 (дисперсия обеих групп по p0).
def mde_two_prop(p0: float, n1: int, n0: int, alpha: float = 0.05, power: float = 0.8) -> float:
    z = stats.norm.ppf(1 - alpha / 2) + stats.norm.ppf(power)
    return z * np.sqrt(p0 * (1 - p0) * (1 / n1 + 1 / n0))


# Размер каждой группы, чтобы заметить рост доли с p0 до p0 + d (формула Флейса без поправки на непрерывность).
def n_two_prop(p0: float, d: float, alpha: float = 0.05, power: float = 0.8) -> float:
    p1 = p0 + d
    if not 0 < p1 < 1:
        return np.nan
    pm = (p0 + p1) / 2
    za, zb = stats.norm.ppf(1 - alpha / 2), stats.norm.ppf(power)
    return ((za * np.sqrt(2 * pm * (1 - pm)) + zb * np.sqrt(p0 * (1 - p0) + p1 * (1 - p1))) / d) ** 2


# Скорректированные p-value Бенджамини-Хохберга, в исходном порядке.
def bh_adjust(p) -> np.ndarray:
    p = np.asarray(p, float)
    m = len(p)
    order = np.argsort(p)
    adj = p[order] * m / np.arange(1, m + 1)
    adj = np.minimum.accumulate(adj[::-1])[::-1]
    out = np.empty(m)
    out[order] = np.minimum(adj, 1)
    return out


def bonferroni_adjust(p) -> np.ndarray:
    p = np.asarray(p, float)
    return np.minimum(p * len(p), 1)


# Мета-анализ со случайными эффектами по DerSimonian-Laird.
def dl_meta(effects, variances, alpha: float = 0.05) -> dict:
    y, v = np.asarray(effects, float), np.asarray(variances, float)
    w = 1 / v
    fixed = np.sum(w * y) / w.sum()
    q = np.sum(w * (y - fixed) ** 2)
    df = len(y) - 1
    tau2 = max(0.0, (q - df) / (w.sum() - np.sum(w ** 2) / w.sum()))
    w_re = 1 / (v + tau2)
    est = np.sum(w_re * y) / w_re.sum()
    se = np.sqrt(1 / w_re.sum())
    z = stats.norm.ppf(1 - alpha / 2)
    # интервал предсказания: где с вероятностью 95% окажется истинный эффект нового похожего эксперимента
    t = stats.t.ppf(1 - alpha / 2, len(y) - 2)
    half = t * np.sqrt(tau2 + se ** 2)
    return {"estimate": est, "se": se, "ci": (est - z * se, est + z * se), "tau2": tau2, "q": q,
            "q_p": stats.chi2.sf(q, df), "i2": max(0.0, (q - df) / q) if q > 0 else 0.0,
            "pi": (est - half, est + half)}
