import os
from enum import Enum, auto
import logging
from datetime import datetime
from app.features.redis.redis_client import get_redis_client
from app.services.status_service import StatusService
from python_scripts.dataCleaning import Cleanse, Manipulation, Augmentation
from python_scripts.visualization import GraphGenerator
from flask import current_app
from app.domain.models import ProjectContext
from app.infrastructure.logging_sinks import StdLoggerSink, RedisSink, CompositeSink, LogSink
from app.pipeline.steps import (
    CleaningStep,
    ManipulationStep,
    AugmentationStep,
    VisualizationStep,
    FinalizationStep,
    StepResult,
    CLEANING_REGISTRY_SIMPLE,
    CLEANING_REGISTRY_PARAM,
    MANIPULATION_REGISTRY_SIMPLE,
    MANIPULATION_REGISTRY_PARAM,
    AUGMENTATION_REGISTRY_SIMPLE,
)

## Registry definitions moved to app.pipeline.steps to avoid circular imports


# State tanımlamaları
class DataState(Enum):
    INITIAL = auto()
    CLEANING = auto()
    MANIPULATION = auto()
    AUGMENTATION = auto()
    VISUALIZATION = auto()
    FINAL = auto()
    COMPLETE = auto()

# Logger konfigürasyonu için fonksiyon
def configure_state_logger() -> logging.Logger:
    """Sadece file/console logger döndürür. Publish sorumluluğu sink'lerde."""
    state_logger = logging.getLogger('state_machine')
    state_logger.setLevel(logging.INFO)
    if not state_logger.handlers:
        try:
            logs_folder = current_app.config['LOGS_FOLDER']
            log_file = os.path.join(logs_folder, f"state_machine_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
            handler = logging.FileHandler(log_file)
        except Exception:
            handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        state_logger.addHandler(handler)
        state_logger.propagate = False
    return state_logger

class DataStateMachine:
    # DÜZELTME: __init__ metodunu ProjectContext alacak şekilde basitleştir
    def __init__(self, context: ProjectContext, mode='full_auto', output_type='raw', processes=None, processed_data_save_path=None, visualization_params=None, log_sink: LogSink | None = None):
        self.context = context # Artık tüm proje bilgisi burada
        self.data = self.context.get_data() # Veriyi context üzerinden yükle
        self.project_name = self.context.project_name # Proje adını context'ten al
        
        self.state = DataState.INITIAL
        self.mode = mode
        self.processes = processes
        self.output_type = output_type
        self.processed_data_save_path = processed_data_save_path
        self.visualization_params = visualization_params if visualization_params else {}
        
        base_logger = configure_state_logger()
        if log_sink is None:
            # Varsayılan composite: file/std + redis (redis hataları swallow edilir)
            try:
                redis_client = get_redis_client()
                composite = CompositeSink([StdLoggerSink(base_logger), RedisSink(redis_client)])
            except Exception:
                composite = CompositeSink([StdLoggerSink(base_logger)])
            self.logger: LogSink = composite
        else:
            self.logger = log_sink
        self.logger.info("State Machine initialized", project=self.project_name, mode=self.mode)
    
    # Geri uyumluluk: Eski çağrılar için tutuldu (ileride kaldırılacak)
    def log_info(self, message, **ctx):
        self.logger.info(message, **ctx)

    def transition_to(self, new_state):
        self.logger.info("Transitioning", from_state=self.state.name, to_state=new_state.name)
        self.state = new_state

    def process(self):
        while True:
            if self.state == DataState.INITIAL:
                self.logger.info("Loading data...")
                if self.mode == 'visualize_only':
                    self.transition_to(DataState.VISUALIZATION)
                else:
                    self.transition_to(DataState.CLEANING)

            elif self.state == DataState.CLEANING:
                step = CleaningStep()
                result: StepResult = step.run(self.data, mode=self.mode, processes=self.processes, logger=self.logger)
                if result.data is not None:
                    self.data = result.data
                self.transition_to(DataState.MANIPULATION)

            elif self.state == DataState.MANIPULATION:
                step = ManipulationStep()
                result: StepResult = step.run(self.data, mode=self.mode, processes=self.processes, logger=self.logger)
                if result.data is not None:
                    self.data = result.data
                self.transition_to(DataState.AUGMENTATION)

            elif self.state == DataState.AUGMENTATION:
                step = AugmentationStep()
                result: StepResult = step.run(self.data, mode=self.mode, processes=self.processes, logger=self.logger)
                if result.data is not None:
                    self.data = result.data
                self.transition_to(DataState.VISUALIZATION)

            elif self.state == DataState.VISUALIZATION:
                step = VisualizationStep(self.project_name, self.visualization_params, self.output_type)
                result: StepResult = step.run(self.data, mode=self.mode, processes=self.processes, logger=self.logger)
                if result.data is not None:
                    self.data = result.data
                target = result.next_state or ('COMPLETE' if self.mode == 'visualize_only' else 'FINAL')
                self.transition_to(DataState[target])

            elif self.state == DataState.FINAL:
                step = FinalizationStep(self.processed_data_save_path)
                result: StepResult = step.run(self.data, mode=self.mode, processes=self.processes, logger=self.logger)
                if result.data is not None:
                    self.data = result.data
                target = result.next_state or 'COMPLETE'
                self.transition_to(DataState[target])

            elif self.state == DataState.COMPLETE:
                self.logger.info("State machine finished. No further processing.")
                # Redis flag koy
                # Flag set via StatusService (legacy key preserved for backward compatibility)
                StatusService(logger=self.logger, prefix="state_machine").set_flag("complete", value="1", ttl_seconds=60)
                break

            else:
                self.logger.error("Unknown state encountered!")
                break


