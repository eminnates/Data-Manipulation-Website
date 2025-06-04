import os
from enum import Enum, auto
import logging
from datetime import datetime
from python_scripts.dataCleaning import Cleanse, Manipulation, Augmentation
from python_scripts.visualization import Project
from flask import current_app


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
def configure_state_logger():
    state_logger = logging.getLogger('state_machine')
    state_logger.setLevel(logging.INFO)
    
    # Handler'ı yalnızca ilk kez eklemek için kontrol
    if not state_logger.handlers:
        try:
            # Uygulama bağlamı içinde çalıştırılmalı
            logs_folder = current_app.config['LOGS_FOLDER']
            log_file = os.path.join(logs_folder, f"state_machine_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
            handler = logging.FileHandler(log_file)
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            state_logger.addHandler(handler)
            
            # Mesajların root logger'a geçmesini engelle
            state_logger.propagate = False
            print(f"State logger dosyaya yapılandırıldı: {log_file}")
        except Exception as e:
            print(f"State logger hatası: {str(e)}")
            # Fallback olarak konsola log
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            state_logger.addHandler(handler)
            state_logger.warning("Running outside app context - using console logger")
    
    return state_logger

class DataStateMachine:
    def __init__(self, data, mode='full_auto', output_type='raw', processes=None, processed_data_save_path=None):
        self.data = data
        self.state = DataState.INITIAL
        self.mode = mode
        self.processes = processes
        self.output_type = output_type
        self.processed_data_save_path = processed_data_save_path
        
        # Logger'ı başlat
        self.logger = configure_state_logger()
        self.logger.info(f"State Machine initialized. Mode: {self.mode}, Save Path: {self.processed_data_save_path}")

    def transition_to(self, new_state):
        self.logger.info(f"Transitioning from {self.state.name} to {new_state.name}")
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
                self.logger.info("Performing data cleaning...")
                cl = Cleanse(self.data)
                if self.mode == 'full_manual' and self.processes:
                    for proc in self.processes:
                        name = proc.get("name")
                        if name == "RemoveWhitespace":
                            cl.RemoveWhitespace()
                        elif name == "StripSpecialChars":
                            cl.StripSpecialChars()
                        elif name == "LowercaseColumns":
                            cl.LowercaseColumns()
                        elif name == "FixNumericColumn":
                            col = proc.get("FixNumericColumn_param")
                            if col: cl.FixNumericColumn(col)
                        elif name == "AutoFixNumericColumns":
                            cl.AutoFixNumericColumns()
                        elif name == "FillMissing":
                            column = proc.get("column")
                            method = proc.get("method", "mean")
                            value_to_fill = proc.get("value")
                            if column:
                                if method == 'value' and value_to_fill is not None:
                                    cl.FillMissing(column, method=method, value=value_to_fill)
                                elif method != 'value':
                                    cl.FillMissing(column, method=method)
                        elif name == "RemoveHighNullColumns":
                            threshold = float(proc.get("RemoveHighNullColumns_param", 0.8))
                            cl.RemoveHighNullColumns(threshold=threshold)
                        elif name == "DeleteDupValues":
                            cl.DeleteDupValues()
                        elif name == "RemoveConstantColumns":
                            cl.RemoveConstantColumns()
                        elif name == "DropColumn":
                            col = proc.get("DropColumn_param")
                            if col: cl.DropColumn(col)
                        elif name == "CleanEmails":
                            cl.CleanEmails()
                        elif name == "NormalizeColumnValues":
                            cl.NormalizeColumnValues()
                        elif name == "AutoRemoveDigitsFromStringColumns":
                            cl.AutoRemoveDigitsFromStringColumns()
                        elif name == "FilterRows":
                            cond = proc.get("FilterRows_param")
                            if cond:
                                cl.FilterRows(cond)
                                self.data = cl.data
                        elif name == "DynamicFilter":
                            cond = proc.get("DynamicFilter_param")
                            if cond:
                                parts = cond.split()
                                if len(parts) == 3:
                                    cl.DynamicFilter({parts[0]: f"{parts[1]} {parts[2]}"})
                else:
                    cl.RemoveWhitespace()
                    cl.StripSpecialChars()
                    cl.LowercaseColumns()
                    cl.AutoFixNumericColumns()
                    for col in cl.data.select_dtypes(include=['object']).columns:
                        cl.FillMissing(col, method='mode')
                    cl.RemoveHighNullColumns(threshold=0.8)
                    cl.DeleteDupValues()
                    cl.RemoveConstantColumns()
                    cl.detectAndDeleteOutliers()
                    cl.CleanEmails()
                    cl.NormalizeColumnValues()
                    cl.AutoRemoveDigitsFromStringColumns()
                self.data = cl.data
                self.transition_to(DataState.MANIPULATION)

            elif self.state == DataState.MANIPULATION:
                self.logger.info("Performing data manipulation...")
                cl = Manipulation(self.data)
                if self.mode == 'full_manual' and self.processes:
                    for proc in self.processes:
                        name = proc.get("name")
                        if name == "detectAndDeleteOutliers":
                            cl.detectAndDeleteOutliers()
                        elif name == "logTransform":
                            column = proc.get("logTransform_param")
                            if column: cl.logTransform(column)
                        elif name == "combineColumns":
                            columns_str = proc.get("combineColumns_param")
                            new_col = proc.get("combineColumns_new", "combined")
                            if columns_str:
                                columns = [col.strip() for col in columns_str.split(",")]
                                if hasattr(cl, 'combineColumns'):
                                    cl.combineColumns(columns, new_col)
                else:
                    ops = Manipulation.choose_column_operations(cl.data)
                    for col, actions in ops.items():
                        if 'outlier' in actions:
                            cl.detectAndDeleteOutliers()
                        if 'log' in actions:
                            cl.logTransform(col)
                self.data = cl.data
                self.transition_to(DataState.AUGMENTATION)

            elif self.state == DataState.AUGMENTATION:
                self.logger.info("Performing data augmentation...")
                cl = Augmentation(self.data)
                if self.mode == 'full_manual' and self.processes:
                    for proc in self.processes:
                        name = proc.get("name")
                        if name == "sortValues":
                            col = proc.get("sortValues_param")
                            if col: cl.sortValues(col)
                        elif name == "addNoise":
                            column = proc.get("column")
                            noise_level = float(proc.get("noise_level", 0.1))
                            if column: cl.addNoise(column, noise_level)
                        elif name == "generateSyntheticData":
                            num = int(proc.get("generateSyntheticData_param", 10))
                            cl.generateSyntheticData(num_samples=num)
                        elif name == "categoricalToNumeric":
                            col = proc.get("categoricalToNumeric_param")
                            if col: cl.categoricalToNumeric(col)
                        elif name == "combineColumns":
                            cols = proc.get("combineColumns_param")
                            new_col = proc.get("combineColumns_new")
                            if cols and new_col:
                                col_list = [c.strip() for c in cols.split(",")]
                                cl.combineColumns(col_list, new_col)
                        elif name == "timeSeriesShift":
                            col = proc.get("timeSeriesShift_param")
                            period = int(proc.get("timeSeriesShift_period", 1))
                            if col: cl.timeSeriesShift(col, periods=period)
                else:
                    ops = cl.suggest_operations()
                    for col, actions in ops.items():
                        if 'add_noise' in actions:
                            cl.addNoise(col)
                        if 'categorical_to_numeric' in actions:
                            cl.categoricalToNumeric(col)
                        if 'generate_synthetic_data' in actions:
                            cl.generateSyntheticData(num_samples=10)
                self.data = cl.data
                self.transition_to(DataState.VISUALIZATION)

            elif self.state == DataState.VISUALIZATION:
                self.logger.info("Entering VISUALIZATION state...")
                try:
                    cl = Project(output_type=self.output_type, data=self.data)
                    cl.visualize()
                except Exception as e:
                    self.logger.error(f"Visualization error details: {str(e)}")
                    import traceback
                    self.logger.error(f"Traceback: {traceback.format_exc()}")
                self.transition_to(DataState.FINAL)

            elif self.state == DataState.FINAL:
                self.logger.info("Finalizing data processing...")
                try:
                    import os
                    save_path = self.processed_data_save_path
                    if not save_path:
                        temp_dir = os.path.join(os.getcwd(), 'app/static/temp')
                        if not os.path.exists(temp_dir):
                            os.makedirs(temp_dir)
                        save_path = os.path.join(temp_dir, 'processed_data.csv')
                    save_dir = os.path.dirname(save_path)
                    if not os.path.exists(save_dir):
                        os.makedirs(save_dir)
                    self.data.to_csv(save_path, index=False)
                    self.logger.info(f"Processed data saved to {save_path}")
                except Exception as e:
                    self.logger.error(f"Error saving processed data: {e}")
                self.transition_to(DataState.COMPLETE)

            elif self.state == DataState.COMPLETE:
                self.logger.info("State machine finished. No further processing.")
                break

            else:
                self.logger.error("Unknown state encountered!")
                break


