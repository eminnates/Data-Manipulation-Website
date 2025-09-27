import pandas as pd
from app.services.cleaning.pipeline import DataCleaningPipeline
from app.services.cleaning.steps_text import TextNormalizeStep
from app.services.cleaning.steps_numeric import NumericImputeStep

class DummyLogger:
    def __init__(self):
        self.events = []
    def info(self, msg, **ctx):
        self.events.append(('info', msg, ctx))
    def warning(self, msg, **ctx):
        self.events.append(('warning', msg, ctx))
    def error(self, msg, **ctx):
        self.events.append(('error', msg, ctx))


def test_pipeline_basic_flow(tmp_path):
    df = pd.DataFrame({
        'name': [' Alice ', 'Bob', None],
        'age': [10, None, 30]
    })
    logger = DummyLogger()
    pipe = DataCleaningPipeline([
        TextNormalizeStep(),
        NumericImputeStep(strategy='mean')
    ], logger)
    result = pipe.run(df)
    # DataFrame dönüş kontrolü
    assert 'name' in result.df.columns
    assert result.df['name'].iloc[0] == 'alice'  # strip + lower
    # Impute çalışmış olmalı (ikinci satır age null idi)
    assert result.df['age'].isna().sum() == 0
    # Step raporu 2 kayıt
    assert len(result.steps) == 2
    assert any(e for e in logger.events if e[1] == 'clean.step.done')


def test_numeric_strategy_unknown(tmp_path):
    df = pd.DataFrame({'x':[1, None, 3]})
    logger = DummyLogger()
    pipe = DataCleaningPipeline([
        NumericImputeStep(strategy='bogus')
    ], logger)
    result = pipe.run(df)
    # NaN hala vardır çünkü strateji bilinmiyor
    assert result.df['x'].isna().sum() == 1
    assert any(e for e in logger.events if e[0]=='warning')
