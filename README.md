

---
## Security (JWT Auth & Rate Limiting)

Uygulama; HTTP `/status/metrics` endpoint'i ve WebSocket olayları için opsiyonel JWT doğrulaması ve temel hız sınırlama (rate limiting) içerir.

### Konfigürasyon Değişkenleri
| Env Var | Açıklama | Varsayılan |
|---------|----------|-----------|
| `JWT_SECRET` | HS256 için imzalama sırrı | `change-me-dev-secret` |
| `JWT_ALG` | Algoritma | `HS256` |
| `JWT_EXP_SECONDS` | Token yaşam süresi (s) | `3600` |
| `WEBSOCKET_AUTH_ENABLED` | WS auth zorunlu | `1` |
| `RATE_LIMIT_ENABLED` | Rate limit aktif | `1` |
| `RATE_LIMIT_MAX` | Pencere başına istek | `60` |
| `RATE_LIMIT_WINDOW` | Pencere süresi (s) | `60` |

### JWT Token Oluşturma (Geçici Yardımcı)
Geliştirme ortamında bir shell / test context'inde:
```python
from app import create_app
from app.utils.auth import create_token
app = create_app('development')
with app.app_context():
   print(create_token('demo-user'))
```

HTTP isteklerinde header:
```
Authorization: Bearer <TOKEN>
```

WebSocket bağlantısında query param veya Authorization header kullanılabilir:
```
ws://host/socket.io/?token=<TOKEN>
```

### Rate Limiting
Sabit pencere (fixed window) yaklaşımı Redis `INCR + EXPIRE` ile uygulanır. Anahtar şablonu:
```
rl:<identity>:<scope>:<window_start_epoch>
```

Örnek HTTP yanıt header'ları:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 42
X-RateLimit-Reset: 1731234567
```

Limit aşıldığında HTTP için `429` + JSON `{ "error": "rate_limit_exceeded" }`, WebSocket için `preview_error` event'i yayınlanır.

### Güvenlik Notları
- Geliştirmede varsayılan sırrı PROD'da değiştirin.
- Token üretimi şu an basit; gerçek senaryoda kullanıcı kimlik doğrulama akışı ekleyin.
- Sabit pencere yerine ileride kayar pencere (sliding window) veya token bucket tasarımı eklenebilir.

---

# Data Manipulation Website

Welcome to the **Data Manipulation Website** repository! This project is designed to provide a powerful yet simple web-based platform for data manipulation, cleaning, and visualization.

## Table of Contents

- [About](#about)
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Setup](#setup)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

---

## About

The **Data Manipulation Website** is a user-friendly platform that allows users to upload and process various types of datasets. Whether you're a data scientist or a casual user, this platform simplifies fundamental data operations like cleaning, augmentation, and visualization.

---

## Features

- **Data Upload**: Supports file formats such as CSV, Excel, XML, and JSON.
- **Data Cleaning**: Includes outlier removal, handling missing values, and other preprocessing tools.
- **Augmentation**: Utilizes transformation techniques to enhance data quality.
- **Visualization**: Offers charting options like scatter plots, bar charts, and 3D visualizations.
- **Responsive Design**: Optimized for both desktop and mobile devices.
- **Custom Dropdowns**: Interactive UI elements for selecting data options.

---

## Technologies Used

This project primarily uses the following technologies:

- **HTML** for structure and design
- **CSS** for styling and responsive layouts
- **JavaScript** for interactivity and dynamic content
- **Python** for backend data processing (e.g., cleaning and augmentation)
- **Libraries**: 
  - **Pandas** and **NumPy** for data manipulation
  - **Matplotlib** and **Seaborn** for visualizations
  - **Scikit-learn** for preprocessing

---

## Setup

To get started with this repository, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/eminnates/Data-Manipulation-Website.git
   ```
2. Navigate into the project directory:
   ```bash
   cd Data-Manipulation-Website
   ```
3. Set up the Python environment:
   ```bash
   python3 -m venv env
   source env/bin/activate  # For Unix/Mac
   env\Scripts\activate     # For Windows
   pip install -r requirements.txt
   ```

4. Run the web application:
   ```bash
   python app.py
   ```

5. Open your web browser and navigate to `http://127.0.0.1:5000`.

---

## Usage

1. **Upload Data**: Use the file input to upload your dataset.
2. **Manipulate Data**: Select options for cleaning, augmentation, or visualization via dropdown menus.
3. **Visualize**: View dynamic charts and 3D graphs generated from your data.
4. **Download Results**: Export your processed dataset for further use.

---

## Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository.
2. Create a new branch:
   ```bash
   git checkout -b feature-name
   ```
3. Commit your changes:
   ```bash
   git commit -m "Add a feature or fix a bug"
   ```
4. Push to the branch:
   ```bash
   git push origin feature-name
   ```
5. Open a Pull Request.

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Feedback

If you have any feedback, questions, or suggestions, feel free to open an issue or contact the repository owner.

---

## Preview Pipeline (Real-Time Cleaning Impact)

Mühendisler için hızlı özet:

Amaç: Seçilen temizlik adımlarının veriyi NASIL etkileyeceğini (satır/sütun değişimleri, etkilenen satır sayısı, null değişimleri) kalıcı işlem yapmadan önce WebSocket üzerinden anlık göstermek.

### Nasıl Çalışır?
1. Frontend, `preview_pipeline_request` event'i ile bir oturum başlatır.
2. Sunucu her adım için DataFrame kopyası üzerinde işlemi uygular (isteğe bağlı sample limit) ve metrikleri yayınlar.
3. Kullanıcı iptal isterse `preview_cancel` gönderir; runner iptal edilir ve `preview_cancelled` + final özet döner.

### Gönderilen Eventler
- `preview_ack`: İstek alındı.
- `preview_step_started`: Adım başlıyor.
- `preview_step_done`: Adım tamamlandı ve metrikler hazır.
- `preview_warning`: Örn. bilinmeyen step.
- `preview_error`: Adım ya da veri yükleme hatası.
- `preview_cancelled`: Döngü iptal edildi.
- `preview_complete`: Tüm (veya iptal anına kadar) adımlar tamamlandı; final özet.

### İstek Payload Örneği
```json
{
   "project_name": "demo_proj",
   "file_name": "data.csv",
   "steps": [
      {"name": "text.normalize", "params": {"columns": ["name"], "mode": "lower"}},
      {"name": "numeric.impute", "params": {"strategy": "mean", "columns": ["age"]}}
   ],
   "sample_limit": 500,
   "session_id": "frontend-uuid-optional"
}
```

### `preview_step_done` Metrikleri
Örnek payload alanları:
```json
{
   "session_id": "...",
   "step": "text.normalize",
   "index": 0,
   "ms": 4.12,
   "rows_before": 1000,
   "rows_after": 1000,
   "rows_delta": 0,
   "cols_before": 12,
   "cols_after": 12,
   "cols_delta": 0,
   "affected_rows": 732,
   "changed_columns": ["name"],
   "null_delta": {"name": -5}
}
```
Alan Açıklamaları:
- `affected_rows`: Satır silinmişse fark; değilse içerik değişen satır sayısı.
- `changed_columns`: İçeriği değişen (limitli) sütun listesi.
- `null_delta`: İlgili sütun için null sayısındaki net değişim.

### İptal
```json
{ "session_id": "same-session-id" }
```
`preview_cancel` gönderildiğinde mevcut adım tamamlanır, kalanlar atlanır, `preview_cancelled` ve ardından `preview_complete` gelir.

### Desteklenen Step İsimleri
- `text.normalize`
- `numeric.impute`
- `quality.outlier_iqr`
- `quality.high_null_prune`
- `quality.constant_prune`

### Tasarım Notları
- Orijinal (kalıcı) veri mutasyona uğramaz; sadece kopya üzerinde.
- Performans için isteğe bağlı `sample_limit` kullanın.
- İleride: Ek step türleri kolayca registry'ye eklenebilir.

### Hızlı Test
Pytest ile birim testleri:
```bash
pytest tests/test_preview_pipeline.py -q
```

---
