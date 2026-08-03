import numpy as np
import pandas as pd
import pytest

from diagnostico_ols.config import ModelSpec
from diagnostico_ols.modeling import fit_model, vif_table


def test_recovers_exact_coefficients_without_noise():
    x1 = np.arange(1.0, 11.0)
    x2 = np.array([0.0, 1.0] * 5)
    y = 3.0 + 2.0 * x1 - 1.5 * x2
    data = pd.DataFrame({"y": y, "x1": x1, "x2": x2})
    fitted = fit_model(data, ModelSpec("exact", "y", ("x1", "x2")))
    assert fitted.conventional.params["const"] == pytest.approx(3.0)
    assert fitted.conventional.params["x1"] == pytest.approx(2.0)
    assert fitted.conventional.params["x2"] == pytest.approx(-1.5)


def test_hc3_changes_standard_errors_under_heteroskedasticity():
    rng = np.random.default_rng(4)
    x = np.linspace(0.1, 5.0, 80)
    y = 1.0 + 2.0 * x + rng.normal(0, x * 0.5)
    fitted = fit_model(pd.DataFrame({"y": y, "x": x}), ModelSpec("hetero", "y", ("x",)))
    assert not np.allclose(fitted.conventional.bse, fitted.robust.bse)


def test_vif_detects_collinearity():
    x1 = np.arange(1.0, 21.0)
    x2 = x1 * 1.001 + 0.001 * np.sin(x1)
    y = 2 + x1
    fitted = fit_model(pd.DataFrame({"y": y, "x1": x1, "x2": x2}), ModelSpec("vif", "y", ("x1", "x2")))
    table = vif_table(fitted)
    assert table["vif"].max() > 1000
