from flask import Blueprint, request, jsonify, current_app, abort
import os
import pandas as pd
import threading
from python_scripts.state_machine import DataStateMachine
import json
import uuid 
from app.domain.models import ProjectContext

state_blueprint = Blueprint('state', __name__)

# 1. Bağımsız iş mantığı fonksiyonu
def run_state_machine_logic(config, logger, root_path, file_name, ext, mode, output_type, process_list, project_title, visualization_params, project_context_cls=ProjectContext, data_state_machine_cls=DataStateMachine):
    try:
        # Deprecation emission (legacy state machine entry)
        try:
            from app.infrastructure.deprecation import DeprecationEmitter  # type: ignore
            DeprecationEmitter.emit(
                key="state_machine.legacy.entry",
                sink=logger,
                message="DataStateMachine direct usage deprecated; use DataPipelineOrchestrator or LegacyStateMachineAdapter",
                level='warning',
                extra={"mode": mode, "project": project_title}
            )
        except Exception:
            pass
        project_context = project_context_cls(project_name=project_title, file_name=file_name)
        data_df = project_context.get_data()
        logger.info(f"Dosya başarıyla okundu: {project_context.active_file_path}")

        temp_dir = os.path.join(root_path, config['TEMP_FOLDER'])
        unique_filename = f"processed_{uuid.uuid4().hex}.csv"
        output_processed_file_path = os.path.join(temp_dir, unique_filename)

        machine = data_state_machine_cls(
            context=project_context,
            mode=mode,
            output_type=output_type,
            processes=process_list,
            processed_data_save_path=output_processed_file_path,
            visualization_params=visualization_params
        )
        machine.process()
        logger.info(f"State machine işlemi tamamlandı. İşlenmiş veri şuraya kaydedildi: {output_processed_file_path}")
    except Exception as e:
        logger.error(f"State machine arka plan görevi sırasında hata: {e}", exc_info=True)

# 2. Arka plan fonksiyonu
def run_state_machine_background(app, file_name, ext, mode='full_auto', output_type='raw', process_list=None, project_title="default_project", visualization_params=None):
    with app.app_context():
        run_state_machine_logic(
            app.config,
            app.logger,
            app.root_path,
            file_name,
            ext,
            mode,
            output_type,
            process_list,
            project_title,
            visualization_params
        )