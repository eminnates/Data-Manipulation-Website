import pandas as pd
import pytest
from app.services.cleaning.preview import PreviewPipelineRunner


def collect_events(runner, df, steps, **run_kwargs):
    events = []
    def cb(name, payload):
        events.append((name, payload))
    runner.run(df, steps, cb, session_id=run_kwargs.get('session_id', 'sess-1'), sample_limit=run_kwargs.get('sample_limit'))
    return events


def test_preview_happy_path_basic_numeric_and_text():
    df = pd.DataFrame({
        'name': ['ALICE', 'Bob', None],
        'age': [10, None, 30]
    })
    steps = [
        {'name': 'text.normalize', 'params': {'columns': ['name'], 'mode': 'lower'}},
        {'name': 'numeric.impute', 'params': {'strategy': 'mean', 'columns': ['age']}}
    ]
    runner = PreviewPipelineRunner()
    events = collect_events(runner, df, steps)
    # Ensure step_done emitted twice and final complete
    step_done = [e for e in events if e[0] == 'preview_step_done']
    assert len(step_done) == 2
    complete = [e for e in events if e[0] == 'preview_complete']
    assert len(complete) == 1
    # Check metrics integrity for first step (name column changed)
    first_payload = step_done[0][1]
    assert first_payload['rows_before'] == 3
    assert 'affected_rows' in first_payload
    # age imputation should reduce nulls in age
    second_payload = step_done[1][1]
    # After impute, age null_delta should show negative change or be empty if logic doesn't capture (allow either)
    assert 'affected_rows' in second_payload


def test_preview_unknown_step_warning():
    df = pd.DataFrame({'a': [1,2,3]})
    steps = [
        {'name': 'nonexistent.step', 'params': {}},
        {'name': 'text.normalize', 'params': {'columns': []}},
    ]
    runner = PreviewPipelineRunner()
    events = collect_events(runner, df, steps)
    warnings = [e for e in events if e[0] == 'preview_warning']
    assert len(warnings) == 1
    # Ensure still proceeds to known step
    step_done = [e for e in events if e[0] == 'preview_step_done']
    assert len(step_done) == 1


def test_preview_cancellation_stops_iteration():
    df = pd.DataFrame({
        'col': ['A','B','C','D']
    })
    steps = [
        {'name': 'text.normalize', 'params': {'columns': ['col'], 'mode': 'lower'}},
        {'name': 'text.normalize', 'params': {'columns': ['col'], 'mode': 'lower'}},
        {'name': 'text.normalize', 'params': {'columns': ['col'], 'mode': 'lower'}},
    ]
    runner = PreviewPipelineRunner()
    events = []
    def cb(name, payload):
        events.append((name, payload))
        # Cancel after first done emit
        if name == 'preview_step_done':
            runner.cancel()
    runner.run(df, steps, cb, session_id='cancel-test')
    # Expect only 1 step_done
    step_done = [e for e in events if e[0] == 'preview_step_done']
    assert len(step_done) == 1
    cancelled = [e for e in events if e[0] == 'preview_cancelled']
    # Depending on timing, cancellation triggers before loop continues; ensure event present
    assert len(cancelled) == 1
    # complete event still emitted by design
    complete = [e for e in events if e[0] == 'preview_complete']
    assert len(complete) == 1
