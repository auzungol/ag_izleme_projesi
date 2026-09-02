from flask import Flask, jsonify, render_template, request
import sqlite3
from monitor import ag_taramasi_yap

app = Flask(__name__)


def veritabanindan_son_durumlari_cek():
    baglanti = sqlite3.connect("ag_verileri.db")
    baglanti.row_factory = sqlite3.Row
    imlec = baglanti.cursor()
    imlec.execute('''
        SELECT c.ip_adresi, c.cihaz_adi, c.birim, p.durum, p.gecikme, p.kayip, MAX(p.zaman) as son_kontrol
        FROM cihazlar c
        LEFT JOIN ping_gecmisi p ON c.ip_adresi = p.ip_adresi
        GROUP BY c.ip_adresi
    ''')
    satirlar = imlec.fetchall()
    baglanti.close()

    cihaz_listesi = []
    for satir in satirlar:
        cihaz_listesi.append({
            "ip": satir["ip_adresi"], "cihaz_adi": satir["cihaz_adi"], "birim": satir["birim"],
            "durum": satir["durum"] or "HENÜZ TARANMADI", "gecikme": satir["gecikme"],
            "kayip": satir["kayip"], "son_kontrol": satir["son_kontrol"] or "-"
        })
    return cihaz_listesi


@app.route('/')
def ana_sayfa():
    return render_template('index.html')


@app.route('/api/cihazlar')
def cihazlari_getir():
    return jsonify(veritabanindan_son_durumlari_cek())


@app.route('/api/tara', methods=['POST'])
def tarama_tetikle():
    veri = request.json
    tarama_tipi = veri.get('tip')
    hedef_deger = veri.get('deger')

    baglanti = sqlite3.connect("ag_verileri.db")
    imlec = baglanti.cursor()

    if tarama_tipi == 'hepsi':
        imlec.execute("SELECT ip_adresi FROM cihazlar")
    elif tarama_tipi == 'birim':
        imlec.execute("SELECT ip_adresi FROM cihazlar WHERE birim = ?", (hedef_deger,))
    elif tarama_tipi == 'cihaz':
        imlec.execute("SELECT ip_adresi FROM cihazlar WHERE ip_adresi = ?", (hedef_deger,))

    hedef_ipler = [satir[0] for satir in imlec.fetchall()]
    baglanti.close()

    if not hedef_ipler:
        return jsonify({"hata": "Bu kritere uygun cihaz bulunamadı!"}), 404

    tarama_sonuclari = ag_taramasi_yap(hedef_ipler)

    return jsonify({
        "mesaj": f"{len(tarama_sonuclari)} adet cihaz başarıyla tarandı!",
        "detaylar": tarama_sonuclari
    })


@app.route('/api/gecmis/<ip>')
def gecmis_verileri_getir(ip):
    baglanti = sqlite3.connect("ag_verileri.db")
    baglanti.row_factory = sqlite3.Row
    imlec = baglanti.cursor()

    imlec.execute('''
        SELECT gecikme, zaman, durum
        FROM ping_gecmisi
        WHERE ip_adresi = ?
        ORDER BY zaman DESC
        LIMIT 15
    ''', (ip,))

    satirlar = imlec.fetchall()
    baglanti.close()

    gecmis_listesi = []
    for satir in reversed(satirlar):
        gecikme_degeri = satir["gecikme"] if satir["gecikme"] is not None else 0
        saat = satir["zaman"].split(" ")[1] if satir["zaman"] else ""

        gecmis_listesi.append({
            "gecikme": gecikme_degeri,
            "zaman": saat,
            "durum": satir["durum"]
        })

    return jsonify(gecmis_listesi)


@app.route('/api/cihaz_yonet', methods=['POST', 'DELETE'])
def cihaz_yonet():
    baglanti = sqlite3.connect("ag_verileri.db")
    imlec = baglanti.cursor()

    if request.method == 'POST':
        veri = request.json
        try:
            imlec.execute('''
                INSERT OR REPLACE INTO cihazlar (ip_adresi, cihaz_adi, birim) 
                VALUES (?, ?, ?)
            ''', (veri['ip'], veri['cihaz_adi'], veri['birim']))
            baglanti.commit()
            mesaj = "Cihaz başarıyla kaydedildi!"
        except Exception as e:
            baglanti.close()
            return jsonify({"hata": str(e)}), 500

    elif request.method == 'DELETE':
        veri = request.json
        imlec.execute("DELETE FROM cihazlar WHERE ip_adresi = ?", (veri['ip'],))
        imlec.execute("DELETE FROM ping_gecmisi WHERE ip_adresi = ?", (veri['ip'],))
        baglanti.commit()
        mesaj = "Cihaz ve geçmiş verileri sistemden tamamen silindi!"

    baglanti.close()
    return jsonify({"mesaj": mesaj})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)