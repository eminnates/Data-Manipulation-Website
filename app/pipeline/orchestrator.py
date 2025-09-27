from __future__ import annotations
from typing import List, Sequence
import pandas as pd
from app.domain.models import ProjectContext
from app.infrastructure.logging_sinks import LogSink, StdLoggerSink, RedisSink, CompositeSink
from app.features.redis.redis_client import get_redis_client
from app.pipeline.steps import (
    CleaningStep, ManipulationStep, AugmentationStep,
    VisualizationStep, FinalizationStep, StepResult
)

class DataPipelineOrchestrator:
    """Lightweight orchestrator that sequences step objects.

    Responsibilities:
    - Holds ordered list of steps (constructed based on mode)
    - Iterates calling step.run()
    - Handles early completion when a step returns next_state='COMPLETE'
    - Exposes final dataframe
    """
    def __init__(self, context: ProjectContext, *, mode: str = 'full_auto', output_type: str = 'raw', processes=None, processed_data_save_path: str | None = None, visualization_params: dict | None = None, log_sink: LogSink | None = None):
        self.context = context
        self.mode = mode
        self.processes = processes
        self.output_type = output_type
        self.processed_data_save_path = processed_data_save_path
        self.visualization_params = visualization_params or {}
        self.data: pd.DataFrame = context.get_data()

        # Logging sink fallback
        if log_sink is None:
            import logging, os
            logger = logging.getLogger('pipeline_orchestrator')
            logger.setLevel(logging.INFO)
            if not logger.handlers:
                from flask import current_app
                try:
                    logs_folder = current_app.config['LOGS_FOLDER']
                    import datetime
                    log_file = os.path.join(logs_folder, f"pipeline_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
                    fh = logging.FileHandler(log_file)
                except Exception:
                    fh = logging.StreamHandler()
                fmt = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
                fh.setFormatter(fmt)
                logger.addHandler(fh)
                logger.propagate = False
            # composite sink
            try:
                redis_client = get_redis_client()
                self.logger: LogSink = CompositeSink([StdLoggerSink(logger), RedisSink(redis_client)])
            except Exception:
                self.logger = CompositeSink([StdLoggerSink(logger)])
        else:
            self.logger = log_sink

        self.steps: List = self._build_steps()
        self.logger.info('Orchestrator initialized', mode=self.mode, steps=[s.name for s in self.steps])

    def _build_steps(self) -> Sequence:
        steps: List = []
        # Visualization only modunda cleaning/manipulation/augmentation atlanır
        if self.mode != 'visualize_only':
            steps.extend([
                CleaningStep(),
                ManipulationStep(),
                AugmentationStep(),
            ])
        steps.append(VisualizationStep(self.context.project_name, self.visualization_params, self.output_type))
        # Sadece visualize_only ise finalize yok
        if self.mode != 'visualize_only':
            steps.append(FinalizationStep(self.processed_data_save_path))
        return steps

    def run(self) -> pd.DataFrame:
        self.logger.info('Pipeline run started')
        for step in self.steps:
            self.logger.info('Step start', step=step.name)
            result: StepResult = step.run(self.data, mode=self.mode, processes=self.processes, logger=self.logger)
            if result.data is not None:
                self.data = result.data
            if result.next_state == 'COMPLETE':
                self.logger.info('Early completion requested', step=step.name)
                break
        self.logger.info('Pipeline run finished')
        # Flag koy (eski state machine davranışıyla uyumlu olacak şekilde)
        try:
            redis_client = get_redis_client()
            redis_client.set('pipeline:complete', '1', ex=60)
            self.logger.info('Redis flag set', key='pipeline:complete')
        except Exception as e:
            self.logger.error('Redis flag error', exc=e)
        return self.data

__all__ = ['DataPipelineOrchestrator']
