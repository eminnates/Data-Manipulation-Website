from flask import Blueprint, jsonify
import os
import time

logs_blueprint = Blueprint('logs', __name__)

def is_meaningful_log(line):
    return (
        "State Machine initialized" in line or
        "Transitioning" in line or
        "Performing data" in line or
        ("INFO -" in line and "127.0.0.1" not in line)
    )

def is_process_complete(lines):
    """İşlemin tamamlanıp tamamlanmadığını kontrol eder"""
    for line in reversed(lines):  # En son satırlardan başla
        if "Final state reached" in line or "Processing complete" in line:
            return True
    return False

@logs_blueprint.route('/latest', methods=['GET'])
def get_latest_log():
    logs_dir = os.path.join(os.getcwd(), 'logs')
    if not os.path.isdir(logs_dir):
        return jsonify({'log': '', 'complete': False})
        
    log_files = sorted(
        [f for f in os.listdir(logs_dir) if f.startswith('state_machine_')],
        reverse=True
    )
    
    if not log_files:
        return jsonify({'log': '', 'complete': False})
    
    log_path = os.path.join(logs_dir, log_files[0])

    # Tamamlanma durumunu kontrol etmek için bekleme
    timeout = 5  # saniye - süreyi artırdım
    interval = 0.3  # tekrar aralığı
    waited = 0
    filtered = []
    is_complete = False
    
    while waited < timeout:
        try:
            with open(log_path, encoding='utf-8') as f:
                lines = f.readlines()
            
            # İşlem tamamlanmış mı kontrol et
            is_complete = is_process_complete(lines)
            
            # HTTP isteklerini filtrele
            filtered = [line for line in lines if is_meaningful_log(line)]
            
            # Zaten tamamlanmışsa çık
            if is_complete and filtered:
                break
                
        except Exception as e:
            print(f"Log okuma hatası: {e}")
            
        time.sleep(interval)
        waited += interval

    # Satır sonlarını düzgün ekleyerek verileri formatlayın
    formatted_logs = []
    for line in filtered:
        if line and not line.endswith('\n'):
            formatted_logs.append(line + '\n')
        else:
            formatted_logs.append(line)
            
    return jsonify({
        'log': ''.join(formatted_logs), 
        'complete': is_complete
    })