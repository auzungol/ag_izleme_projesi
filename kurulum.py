import sqlite3

# Ağ, 99 daireye/birime bölünmüş bir VLAN planına göre kurulur: 10.<vlan_no>.0.0/24
# (örn. Bilgi İşlem Dairesi Başkanlığı -> 10.99.0.x). Cihazlar bu şemaya göre
# panel üzerindeki "Yeni Cihaz Ekle" ile tek tek elle eklenir; burada örnek/otomatik
# veri üretilmez.


def veritabanini_guncelle():
    baglanti = sqlite3.connect("ag_verileri.db")
    imlec = baglanti.cursor()

    # 1. Cihaz Envanteri Tablosunu Oluştur
    imlec.execute('''
        CREATE TABLE IF NOT EXISTS cihazlar (
            ip_adresi TEXT PRIMARY KEY,
            cihaz_adi TEXT,
            birim TEXT
        )
    ''')

    # 2. Ping Geçmişi Tablosunu Oluştur (monitor.py buraya yazar, app.py buradan okur)
    imlec.execute('''
        CREATE TABLE IF NOT EXISTS ping_gecmisi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_adresi TEXT,
            durum TEXT,
            gecikme REAL,
            kayip INTEGER,
            zaman DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    baglanti.commit()
    baglanti.close()
    print("[BAŞARILI] Veritabanı hazır: 'cihazlar' ve 'ping_gecmisi' tabloları boş olarak oluşturuldu.")


if __name__ == "__main__":
    veritabanini_guncelle()
