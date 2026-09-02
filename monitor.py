import subprocess
import platform
import re
import sqlite3
from concurrent.futures import ThreadPoolExecutor


def sonuclari_veritabanina_kaydet(sonuclar):
    baglanti = sqlite3.connect("ag_verileri.db")
    imlec = baglanti.cursor()
    for veri in sonuclar:
        imlec.execute('''
            INSERT INTO ping_gecmisi (ip_adresi, durum, gecikme, kayip)
            VALUES (?, ?, ?, ?)
        ''', (veri['ip'], veri['durum'], veri['gecikme'], veri['kayip']))
    baglanti.commit()
    baglanti.close()


def ping_ve_analiz_et(ip_adresi):
    is_windows = platform.system().lower() == 'windows'
    parametre = '-n' if is_windows else '-c'
    timeout_parametre = '-w' if is_windows else '-W'
    timeout_deger = '1000' if is_windows else '1'

    komut = ['ping', parametre, '1', timeout_parametre, timeout_deger, ip_adresi]

    try:
        sonuc = subprocess.run(komut, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        gecikme = None
        kayip = 100
        durum = "BAŞARISIZ"

        if sonuc.returncode == 0:
            durum = "BAŞARILI"
            cikti = sonuc.stdout
            gecikme_eslesme = re.search(r"time[=<](\d+)ms", cikti)
            if gecikme_eslesme: gecikme = float(gecikme_eslesme.group(1))
            kayip_eslesme = re.search(r"\((\d+)%\s*loss\)", cikti)
            if kayip_eslesme: kayip = int(kayip_eslesme.group(1))

        return {"ip": ip_adresi, "durum": durum, "gecikme": gecikme, "kayip": kayip}
    except Exception:
        return {"ip": ip_adresi, "durum": "HATA", "gecikme": None, "kayip": 100}


def ag_taramasi_yap(hedef_ipler):
    """Flask API tarafından tetiklenecek ana tarama fonksiyonu"""
    sonuclar = []
    with ThreadPoolExecutor(max_workers=50) as calistirici:
        for sonuc in calistirici.map(ping_ve_analiz_et, hedef_ipler):
            sonuclar.append(sonuc)

    sonuclari_veritabanina_kaydet(sonuclar)
    return sonuclar