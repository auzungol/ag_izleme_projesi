# Ağ Cihazları Erişilebilirlik ve Performans Analiz Sistemi

Kurum ağındaki cihazların (sunucu, switch, yazıcı vb.) erişilebilirliğini ve gecikme/paket kaybı performansını gerçek zamanlı izlemek için geliştirilmiş, Flask tabanlı hafif bir ağ izleme uygulaması. Cihazlar VLAN/birim bazlı olarak envantere eklenir, periyodik veya manuel ping taramalarıyla durumları kaydedilir ve sonuçlar bir web panelinden takip edilir.

> Bu proje, elektronik haberleşme stajı kapsamında geliştirilmektedir.

## Özellikler

- **Cihaz envanteri**: IP adresi, cihaz adı ve birim (VLAN) bilgisiyle cihaz ekleme/silme
- **Toplu ping taraması**: `ThreadPoolExecutor` ile eşzamanlı ping atarak çok sayıda cihazı hızlıca tarama
- **Esnek tarama kapsamı**: Tüm cihazları, tek bir birimi veya tek bir cihazı hedefleyerek tarama tetikleme
- **Performans metrikleri**: Her tarama için durum (başarılı/başarısız), gecikme (ms) ve paket kaybı (%) kaydı
- **Geçmiş veri sorgulama**: Bir cihazın son taramalarına ait geçmiş (grafikte kullanılmak üzere) API üzerinden alınabilir
- **REST API**: Web arayüzünün (veya başka bir istemcinin) kullanabileceği JSON uçları

## Mimari ve Teknoloji Yığını

| Katman | Teknoloji |
|---|---|
| Web sunucusu / API | Python, Flask |
| Ağ testi | `ping` (sistem komutu), `subprocess`, `concurrent.futures` |
| Veritabanı | SQLite |
| Arayüz (planlanan) | Jinja2 şablonu + Chart.js |

Proje üç ana modülden oluşur:

- **`kurulum.py`** — SQLite veritabanını ve gerekli tabloları (`cihazlar`, `ping_gecmisi`) oluşturur.
- **`monitor.py`** — Verilen IP listesine paralel ping atar, sonuçları yorumlar (başarılı/başarısız, gecikme, kayıp) ve veritabanına kaydeder.
- **`app.py`** — Flask uygulaması; cihazları listeleyen, tarama tetikleyen, geçmiş veriyi döndüren ve cihaz ekleme/silme işlemlerini yöneten REST API uçlarını sağlar.

### Veri Modeli

- `cihazlar (ip_adresi PK, cihaz_adi, birim)` — cihaz envanteri
- `ping_gecmisi (id, ip_adresi, durum, gecikme, kayip, zaman)` — her taramanın sonucu

## Kurulum

```bash
git clone https://github.com/auzungol/network_montioring.git
cd network_montioring

python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # macOS/Linux

pip install flask
```



Veritabanını oluşturmak için ilk kurulumda bir kez çalıştırın:

```bash
python kurulum.py
```

Bu komut, `ag_verileri.db` dosyasını ve gerekli tabloları oluşturur.

Uygulamayı başlatın:

```bash
python app.py
```

Sunucu varsayılan olarak `http://0.0.0.0:5000` adresinde ayağa kalkar.

> Not: `app.py`, `templates/index.html` şablonunu render eder; arayüz dosyaları depoya henüz eklenmemiştir. Panel arayüzü olmadan API uçları doğrudan test edilebilir.

## Kullanım

Cihazlar, panel üzerindeki "Yeni Cihaz Ekle" formuyla ya da doğrudan `/api/cihaz_yonet` uç noktasına istek göndererek tek tek envantere eklenir; örnek/otomatik veri üretilmez. Ağ, `10.<vlan_no>.0.0/24` şeklinde birim bazlı bir VLAN planına göre kurgulanmıştır (örn. Bilgi İşlem Dairesi Başkanlığı → `10.99.0.x`).

## API Uç Noktaları

| Yöntem | Uç Nokta | Açıklama |
|---|---|---|
| `GET` | `/` | Ana panel sayfasını döndürür |
| `GET` | `/api/cihazlar` | Tüm cihazların son durumunu (gecikme, kayıp, son kontrol zamanı) listeler |
| `POST` | `/api/tara` | Tarama tetikler. Gövde: `{"tip": "hepsi" \| "birim" \| "cihaz", "deger": "..."}` |
| `GET` | `/api/gecmis/<ip>` | İlgili IP'nin son 15 taramasına ait gecikme/durum geçmişini döndürür |
| `POST` | `/api/cihaz_yonet` | Yeni cihaz ekler veya var olanı günceller. Gövde: `{"ip": "...", "cihaz_adi": "...", "birim": "..."}` |
| `DELETE` | `/api/cihaz_yonet` | Cihazı ve ilgili ping geçmişini siler. Gövde: `{"ip": "..."}` |

### Örnek: Tüm cihazları tara

```bash
curl -X POST http://localhost:5000/api/tara \
  -H "Content-Type: application/json" \
  -d '{"tip": "hepsi"}'
```

### Örnek: Yeni cihaz ekle

```bash
curl -X POST http://localhost:5000/api/cihaz_yonet \
  -H "Content-Type: application/json" \
  -d '{"ip": "10.99.0.5", "cihaz_adi": "Sunucu-1", "birim": "Bilgi İşlem Dairesi Başkanlığı"}'
```

## Proje Yapısı

```
network_montioring/
├── app.py          # Flask uygulaması ve REST API uçları
├── monitor.py      # Paralel ping/tarama mantığı
├── kurulum.py      # Veritabanı şeması kurulumu
└── ag_verileri.db  # SQLite veritabanı (kurulum.py ile oluşturulur, repoya dahil değil)
```

## Yol Haritası

- [ ] Web arayüzü (`templates/index.html`) ve Chart.js entegrasyonu
- [ ] Anomali tespiti kuralları (ör. ardışık paket kaybı, gecikme eşiği aşımı)
- [ ] SNMP tabanlı ek metrik toplama (opsiyonel)
- [ ] `requirements.txt` ve otomatik/zamanlanmış tarama desteği

