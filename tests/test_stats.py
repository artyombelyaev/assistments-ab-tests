import numpy as np
import pytest

from src import stats


def test_srm_equal_groups():
    assert stats.srm_pvalue(500, 500) == pytest.approx(1.0)


def test_srm_known_value():
    # 60 против 40: хи-квадрат = 20^2 / 100 = 4, p = 2 * (1 - Ф(2))
    assert stats.srm_pvalue(60, 40) == pytest.approx(0.0455003, abs=1e-6)


def test_srm_uneven_split():
    assert stats.srm_pvalue(300, 700, share_c=0.3) == pytest.approx(1.0)


def test_two_prop_ztest_known_value():
    # общая доля 0,5, se = sqrt(0,25 * 0,02), z = 0,2 / se
    z, p = stats.two_prop_ztest(60, 100, 40, 100)
    assert z == pytest.approx(2.828427, abs=1e-6)
    assert p == pytest.approx(0.0046777, abs=1e-6)


def test_two_prop_ztest_sign():
    z, _ = stats.two_prop_ztest(40, 100, 60, 100)
    assert z < 0


def test_diff_ci_known_value():
    # se = sqrt(0,24 / 100 * 2) = 0,069282
    lo, hi = stats.diff_ci(60, 100, 40, 100)
    assert lo == pytest.approx(0.2 - 1.959964 * 0.069282, abs=1e-5)
    assert hi == pytest.approx(0.2 + 1.959964 * 0.069282, abs=1e-5)


def test_smd_known_value():
    assert stats.smd([1, 2, 3], [2, 3, 4]) == pytest.approx(-1.0)


def test_smd_ignores_nan():
    assert stats.smd([1, 2, 3, np.nan], [np.nan, 2, 3, 4]) == pytest.approx(-1.0)


def test_smd_constant_columns():
    assert stats.smd([1, 1], [1, 1]) == 0.0


def test_balance_pvalue_detects_shift():
    rng = np.random.default_rng(0)
    treated = np.repeat([True, False], 100)
    x = rng.normal(size=(200, 3))
    x[treated, 0] += 1.0
    assert stats.balance_pvalue(x, treated, 500, np.random.default_rng(1)) < 0.01


def test_balance_pvalue_random_split():
    rng = np.random.default_rng(0)
    treated = np.repeat([True, False], 100)
    x = rng.normal(size=(200, 3))
    assert stats.balance_pvalue(x, treated, 500, np.random.default_rng(1)) > 0.05


def test_bootstrap_diff_ci_degenerate():
    lo, hi = stats.bootstrap_diff_ci(50, 50, 0, 50, 1000, np.random.default_rng(0))
    assert lo == hi == 1.0


def test_bootstrap_diff_ci_close_to_wald_on_large_sample():
    boot = stats.bootstrap_diff_ci(12000, 20000, 10000, 20000, 20000, np.random.default_rng(0))
    wald = stats.diff_ci(12000, 20000, 10000, 20000)
    assert boot == pytest.approx(wald, abs=0.001)


def test_bootstrap_diff_ci_reproducible():
    a = stats.bootstrap_diff_ci(30, 70, 20, 70, 500, np.random.default_rng(42))
    b = stats.bootstrap_diff_ci(30, 70, 20, 70, 500, np.random.default_rng(42))
    assert a == b


def test_bootstrap_mean_diff_ci_constant_groups():
    lo, hi = stats.bootstrap_mean_diff_ci([2.0] * 10, [1.0] * 10, 500, np.random.default_rng(0))
    assert lo == pytest.approx(1.0) and hi == pytest.approx(1.0)


def test_bootstrap_mean_diff_ci_close_to_normal_ci():
    # средние 1 и 0, sd 1, по 5000 в группе: se = sqrt(2 / 5000) = 0,02
    rng = np.random.default_rng(0)
    a1, a0 = rng.normal(1, 1, 5000), rng.normal(0, 1, 5000)
    lo, hi = stats.bootstrap_mean_diff_ci(a1, a0, 4000, np.random.default_rng(1))
    d = a1.mean() - a0.mean()
    assert lo == pytest.approx(d - 1.96 * 0.02, abs=0.003)
    assert hi == pytest.approx(d + 1.96 * 0.02, abs=0.003)
