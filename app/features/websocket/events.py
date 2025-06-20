from app.features.websocket.extensions import socketio
from flask import current_app
from flask_socketio import emit

@socketio.on('connect')
def handle_connect():
    print("Bir istemci WebSocket ile bağlandı.")

def send_log_to_clients(log_message):
    socketio.emit('log_message', {'log': log_message})

@socketio.on('calculate_suitability')
def handle_suitability_check(data):
    """
    Frontend'den gelen işlem listesine göre bir uygunluk skoru hesaplar
    ve sonucu anında istemciye geri gönderir.
    """
    # 1. Frontend'den gelen işlem listesini al
    processes = data.get('processes', [])
    current_app.logger.info(f"Suitability check requested with processes: {processes}")

    # 2. PUANLAMA MANTIĞI (Bu kısmı kendi projenize göre geliştirebilirsiniz)
    # Bu, sizin "25 kolonu etkileyecek hesaplama" dediğiniz yerin basitleştirilmiş halidir.
    # Her bir işleme bir "karmaşıklık" veya "etki" puanı atayalım.
    process_scores = {
        'RemoveWhitespace': 5,
        'LowercaseColumns': 5,
        'StripSpecialChars': 10,
        'HandleMissingValues': 20, # Eksik veriyle uğraşmak önemli bir işlem
        'RemoveDuplicates': 15,
        'ChangeDataType': 10,
        # ... diğer işlemleriniz için puanlar ...
    }
    
    # Maksimum alınabilecek puanı ve kullanıcının toplam puanını hesapla
    max_possible_score = sum(process_scores.values())
    total_score = 0
    for process in processes:
        process_name = process.get('name')
        if process_name in process_scores:
            total_score += process_scores[process_name]

    # Skoru 100'lük bir yüzdeye çevir
    suitability_percentage = (total_score / max_possible_score) * 100 if max_possible_score > 0 else 0
    
    current_app.logger.info(f"Calculated suitability score: {suitability_percentage:.2f}%")

    # 3. Hesaplanan sonucu, isteği gönderen istemciye geri gönder
    # 'emit' fonksiyonu, bir olay dinleyicisi içinde çağrıldığında
    # varsayılan olarak sadece o istemciye cevap gönderir.
    emit('suitability_result', {'score': suitability_percentage})
