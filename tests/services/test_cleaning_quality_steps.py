import pandas as pd
from app.services.cleaning.pipeline import DataCleaningPipeline
from app.services.cleaning.steps_quality import OutlierIQRStep, HighNullPruneStep, ConstantColumnPruneStep

class DummyLogger:
    def __init__(self):
        self.events = []
    def info(self, msg, **ctx):
        self.events.append(('info', msg, ctx))
    def warning(self, msg, **ctx):
        self.events.append(('warning', msg, ctx))
    def error(self, msg, **ctx):
        self.events.append(('error', msg, ctx))

def test_outlier_iqr_removal():
    # Construct a dataframe with a clear outlier
    df = pd.DataFrame({'a': [10,11,9,10,500]})
    logger = DummyLogger()
    pipe = DataCleaningPipeline([OutlierIQRStep(columns=['a'], k=1.5, min_rows=3)], logger)
    result = pipe.run(df)
    # Outlier 500 should be removed
    assert result.df['a'].max() < 500
    assert any(e for e in logger.events if e[1]=='clean.outlier.removed')


def test_high_null_prune():
    df = pd.DataFrame({
        'keep': [1,2,3,4],
        'mostly_null': [None, None, None, 5],
        'all_null': [None, None, None, None]
    })
    logger = DummyLogger()
    pipe = DataCleaningPipeline([HighNullPruneStep(threshold=0.7)], logger)
    result = pipe.run(df)
    # all_null should be removed (100% null), mostly_null ratio=0.75 -> removed
    assert 'all_null' not in result.df.columns
    assert 'mostly_null' not in result.df.columns
    assert 'keep' in result.df.columns
    assert any(e for e in logger.events if e[1]=='clean.nullprune.drop')


def test_constant_column_prune():
    df = pd.DataFrame({
        'id': [1,2,3,4],
        'constant': ['x','x','x','x'],
        'mixed': ['a','a','b','b']
    })
    logger = DummyLogger()
    pipe = DataCleaningPipeline([ConstantColumnPruneStep(exclude=['id'])], logger)
    result = pipe.run(df)
    assert 'constant' not in result.df.columns
    assert 'id' in result.df.columns
    assert 'mixed' in result.df.columns
    assert any(e for e in logger.events if e[1]=='clean.constant.drop')
