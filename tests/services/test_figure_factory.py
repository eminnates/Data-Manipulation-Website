import pandas as pd
import pytest
from app.services.figure_factory import FigureFactory

@pytest.fixture
def df_sample():
    return pd.DataFrame({
        'a': [1,2,3,4],
        'b': [10,20,30,40],
        'c': ['x','y','x','y']
    })

@pytest.mark.parametrize("plot_type,y_col", [
    ("Bar", "b"),
    ("Line", "b"),
    ("Scatter", "b"),
])
def test_factory_xy_plots(df_sample, plot_type, y_col):
    fac = FigureFactory()
    fig = fac.create(plot_type, df_sample, 'a', y_col)
    assert fig is not None
    assert len(fig.data) > 0

def test_factory_histogram(df_sample):
    fac = FigureFactory()
    fig = fac.create("Histogram", df_sample, 'a', None)
    assert fig is not None
    assert len(fig.data) > 0

@pytest.mark.parametrize("plot_type", ["Bar", "Line", "Scatter"])
def test_factory_missing_y_raises(df_sample, plot_type):
    fac = FigureFactory()
    with pytest.raises(ValueError):
        fac.create(plot_type, df_sample, 'a', None)

def test_factory_invalid_plot_type(df_sample):
    fac = FigureFactory()
    with pytest.raises(ValueError):
        fac.create("Box", df_sample, 'a', 'b')
