import matplotlib.pyplot as plt
import pandas as pd

# Örnek veri
veri = {
    "Tarih": ["2025-03-01", "2025-03-02", "2025-03-03", "2025-03-04", "2025-03-05"],
    "Ziyaretçi": [1200, 1500, 1700, 1800, 1600]
}

# DataFrame oluştur
df = pd.DataFrame(veri)

# Tarih verisini datetime formatına çevir
df["Tarih"] = pd.to_datetime(df["Tarih"])

# Grafik çizme
plt.figure(figsize=(8, 5))
plt.plot(df["Tarih"], df["Ziyaretçi"], marker='o', linestyle='-', color='b', label="Ziyaretçi Sayısı")

# Grafik detayları
plt.xlabel("Tarih")
plt.ylabel("Ziyaretçi Sayısı")
plt.title("Günlük Web Ziyaretçi Sayıları")
plt.legend()
plt.grid(True)

# Grafiği göster
plt.xticks(rotation=45)  # Tarihleri eğik yaz
plt.show()
plt.savefig("static/graph.png")
plt.close()
