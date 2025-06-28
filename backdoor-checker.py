import os
import re
import json
import time
import html
from datetime import datetime
from pathlib import Path

class BackdoorChecker:
    def __init__(self):
        self.arkakapilar_deseni = {
            'uzaktan_calistirma': [
                r'load\s*\(\s*.*\s*\)\s*\(\s*\)',
                r'loadstring\s*\(\s*.*\s*\)',
                r'dofile\s*\(\s*.*http.*\s*\)',
                r'require\s*\(\s*.*http.*\s*\)',
                r'RunString\s*\(\s*.*\s*\)',
                r'CompileString\s*\(\s*.*\s*\)',
            ],
            
            'harici_baglanti': [
                r'PerformHttpRequest\s*\(\s*["\'].*?discord\.com.*?["\']',
                r'PerformHttpRequest\s*\(\s*["\'].*?pastebin\.com.*?["\']',
                r'PerformHttpRequest\s*\(\s*["\'].*?bit\.ly.*?["\']',
                r'PerformHttpRequest\s*\(\s*["\'].*?tinyurl\.com.*?["\']',
                r'http\.post\s*\(\s*["\'].*?discord\.com.*?["\']',
                r'http\.get\s*\(\s*["\'].*?pastebin\.com.*?["\']',
            ],
            
            'supleli_komutlar': [
                r'ExecuteCommand\s*\(\s*["\'].*?restart.*?["\']',
                r'ExecuteCommand\s*\(\s*["\'].*?stop.*?["\']',
                r'ExecuteCommand\s*\(\s*["\'].*?quit.*?["\']',
                r'ExecuteCommand\s*\(\s*["\'].*?refresh.*?["\']',
                r'TriggerServerEvent\s*\(\s*["\'].*?__cfx_internal.*?["\']',
            ],
            
            'dosya_erisim': [
                r'io\.open\s*\(\s*["\'].*?\.exe.*?["\']',
                r'io\.popen\s*\(\s*["\'].*?cmd.*?["\']',
                r'os\.execute\s*\(\s*["\'].*?["\']',
                r'os\.remove\s*\(\s*["\'].*?\.lua.*?["\']',
                r'file\.Delete\s*\(\s*["\'].*?["\']',
            ],
            
            'sifreli_kod': [
                r'_G\[.*?\]\s*=\s*function',
                r'getfenv\s*\(\s*\)\s*\[.*?\]',
                r'string\.char\s*\(\s*\d+(?:\s*,\s*\d+){10,}',
                r'\\x[0-9a-fA-F]{2}.*?\\x[0-9a-fA-F]{2}.*?\\x[0-9a-fA-F]{2}',
                r'base64\.decode\s*\(',
            ]
        }
        
        self.beyaz_liste_deseni = [
            r'--.*?backdoor',
            r'print\s*\(\s*["\'].*?backdoor.*?["\']',
        ]
        
        self.tarama_sonuclari = []
        self.toplam_dosya = 0
        self.taranan_dosya = 0
        
    def beyaz_listede_mi(self, satir):
        for desen in self.beyaz_liste_deseni:
            if re.search(desen, satir, re.IGNORECASE):
                return True
        return False
    
    def dosya_tara(self, dosya_yolu):
        try:
            with open(dosya_yolu, 'r', encoding='utf-8', errors='ignore') as f:
                icerik = f.read()
                satirlar = icerik.split('\n')
                
            tespitler = []
            
            for satir_no, satir in enumerate(satirlar, 1):
                if self.beyaz_listede_mi(satir):
                    continue
                    
                for kategori, desenler in self.arkakapilar_deseni.items():
                    for desen in desenler:
                        if re.search(desen, satir, re.IGNORECASE):
                            tespitler.append({
                                'dosya': str(dosya_yolu),
                                'satir_numarasi': satir_no,
                                'satir_icerik': satir.strip(),
                                'kategori': kategori,
                                'desen': desen,
                                'risk_seviye': self.risk_seviyesi_belirle(kategori)
                            })
            
            return tespitler
            
        except Exception as e:
            print("Hata - {} dosyası okunamadı: {}".format(dosya_yolu, e))
            return []
    
    def risk_seviyesi_belirle(self, kategori):
        yuksek_risk = ['uzaktan_calistirma', 'dosya_erisim']
        orta_risk = ['harici_baglanti', 'supleli_komutlar']
        
        if kategori in yuksek_risk:
            return 'YUKSEK'
        elif kategori in orta_risk:
            return 'ORTA'
        else:
            return 'DUSUK'
    
    def klasor_tara(self, klasor_yolu):
        klasor = Path(klasor_yolu)
        
        if not klasor.exists():
            print("Hata: {} klasörü bulunamadı!".format(klasor_yolu))
            return
        
        lua_dosyalari = []
        for uzanti in ['*.lua', '*.LUA']:
            lua_dosyalari.extend(klasor.rglob(uzanti))
        
        self.toplam_dosya = len(lua_dosyalari)
        print("Taranacak dosya sayısı: {}".format(self.toplam_dosya))
        print("-" * 50)
        
        for dosya_yolu in lua_dosyalari:
            self.taranan_dosya += 1
            print("Taranıyor [{}/{}]: {}".format(self.taranan_dosya, self.toplam_dosya, dosya_yolu.name))
            
            tespitler = self.dosya_tara(dosya_yolu)
            if tespitler:
                self.tarama_sonuclari.extend(tespitler)
    
    def html_rapor_olustur(self, cikti_dosya='backdoor-rapor.html'):
        if not self.tarama_sonuclari:
            print("\nHiçbir Backdoor tespit edilmedi!")
            return
        
        risk_sirasi = {'YUKSEK': 0, 'ORTA': 1, 'DUSUK': 2}
        self.tarama_sonuclari.sort(key=lambda x: risk_sirasi.get(x['risk_seviye'], 3))
        
        print("\nTOPLAM {} BACKDOOR TESPİT EDİLDİ!".format(len(self.tarama_sonuclari)))
        
        html_parcalari = []
        
        html_parcalari.append("""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FiveM Arkakapı Tarama Raporu</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        h1 {
            color: #d32f2f;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
        }
        .istatistikler {
            display: flex;
            justify-content: space-around;
            margin-bottom: 30px;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
        }
        .istatistik-kutu {
            text-align: center;
            padding: 15px;
        }
        .istatistik-sayi {
            font-size: 2em;
            font-weight: bold;
            color: #d32f2f;
        }
        .istatistik-etiket {
            color: #666;
            margin-top: 5px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            font-size: 14px;
        }
        th {
            background-color: #d32f2f;
            color: white;
            padding: 15px 10px;
            text-align: left;
            font-weight: bold;
        }
        td {
            padding: 12px 10px;
            border-bottom: 1px solid #ddd;
            vertical-align: top;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .risk-yuksek {
            background-color: #ffebee !important;
            color: #c62828;
            font-weight: bold;
        }
        .risk-orta {
            background-color: #fff3e0 !important;
            color: #f57c00;
            font-weight: bold;
        }
        .risk-dusuk {
            background-color: #f3e5f5 !important;
            color: #7b1fa2;
            font-weight: bold;
        }
        .dosya-yol {
            font-family: 'Courier New', monospace;
            background: #f5f5f5;
            padding: 2px 4px;
            border-radius: 3px;
            font-size: 12px;
        }
        .kod-icerik {
            font-family: 'Courier New', monospace;
            background: #f8f8f8;
            padding: 8px;
            border-left: 3px solid #d32f2f;
            font-size: 12px;
            max-width: 400px;
            word-break: break-all;
        }
        .kategori {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
            color: white;
        }
        .kat-uzaktan_calistirma { background-color: #d32f2f; }
        .kat-harici_baglanti { background-color: #f57c00; }
        .kat-supleli_komutlar { background-color: #7b1fa2; }
        .kat-dosya_erisim { background-color: #c62828; }
        .kat-sifreli_kod { background-color: #388e3c; }
        .kat-yetki_yukseltme { background-color: #1976d2; }
        .kat-sql_enjeksiyon { background-color: #e91e63; }
        .altbilgi {
            text-align: center;
            margin-top: 30px;
            color: #666;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>FiveM Backdoor Tarama Raporu</h1>
        
        <div class="istatistikler">
            <div class="istatistik-kutu">
                <div class="istatistik-sayi">""" + str(self.taranan_dosya) + """</div>
                <div class="istatistik-etiket">Taranan Dosya</div>
            </div>
            <div class="istatistik-kutu">
                <div class="istatistik-sayi">""" + str(len(self.tarama_sonuclari)) + """</div>
                <div class="istatistik-etiket">Tespit Edilen Backdoor</div>
            </div>
            <div class="istatistik-kutu">
                <div class="istatistik-sayi">""" + datetime.now().strftime('%d.%m.%Y') + """</div>
                <div class="istatistik-etiket">Tarama Tarihi</div>
            </div>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th style="width: 35%">Dosya Yolu</th>
                    <th style="width: 8%">Satır</th>
                    <th style="width: 12%">Risk</th>
                    <th style="width: 15%">Kategori</th>
                    <th style="width: 30%">Kod</th>
                </tr>
            </thead>
            <tbody>""")
        
        for sonuc in self.tarama_sonuclari:
            risk_sinifi = 'risk-yuksek' if sonuc['risk_seviye'] == 'YUKSEK' else 'risk-orta' if sonuc['risk_seviye'] == 'ORTA' else 'risk-dusuk'
            kategori_sinifi = 'kat-' + sonuc['kategori']
            kategori_gosterimi = sonuc['kategori'].replace('_', ' ').title()
            
            dosya_yolu = sonuc['dosya'].replace('\\', '/')
            if len(dosya_yolu) > 50:
                dosya_yolu = '...' + dosya_yolu[-47:]
            
            kod_icerik = html.escape(sonuc['satir_icerik'])
            if len(kod_icerik) > 80:
                kod_icerik = kod_icerik[:77] + '...'
            
            html_parcalari.append("""
                <tr>
                    <td><span class="dosya-yol">""" + html.escape(dosya_yolu) + """</span></td>
                    <td style="text-align: center; font-weight: bold;">""" + str(sonuc['satir_numarasi']) + """</td>
                    <td class=\"""" + risk_sinifi + """\" style="text-align: center;">""" + sonuc['risk_seviye'] + """</td>
                    <td><span class="kategori """ + kategori_sinifi + """">""" + kategori_gosterimi + """</span></td>
                    <td><div class="kod-icerik">""" + kod_icerik + """</div></td>
                </tr>""")
        
        html_parcalari.append("""
            </tbody>
        </table>
        
        <div class="altbilgi">
            <p>Şüpheli dosyaları sunucudan kaldırmadan önce tekrar kontrol edin.</p>
        </div>
    </div>
</body>
</html>""")
        
        html_icerik = ''.join(html_parcalari)
        with open(cikti_dosya, 'w', encoding='utf-8') as f:
            f.write(html_icerik)
        
        print("HTML raporu kaydedildi: {}".format(cikti_dosya))
        
        risk_istatistik = {}
        kategori_istatistik = {}
        
        for sonuc in self.tarama_sonuclari:
            risk = sonuc['risk_seviye']
            kategori = sonuc['kategori']
            
            risk_istatistik[risk] = risk_istatistik.get(risk, 0) + 1
            kategori_istatistik[kategori] = kategori_istatistik.get(kategori, 0) + 1
        
        print("\nÖZET İSTATİSTİKLER:")
        print("Risk Seviyeleri:")
        for risk, sayi in risk_istatistik.items():
            print("  {}: {}".format(risk, sayi))
        
        print("\nKategoriler:")
        for kategori, sayi in kategori_istatistik.items():
            print("  {}: {}".format(kategori, sayi))
        print("\nRaporu görüntülemek için {} dosyasını tarayıcınızda açın.".format(cikti_dosya))

def ana_fonksiyon():
    print("FiveM Backdoor Checker")
    print("=" * 40)
    
    tarayici = BackdoorChecker()
    
    sunucu_yolu = input("FiveM sunucu klasör yolunu girin (örn: C:\\fivem-server\\resources): ")
    
    if not sunucu_yolu:
        print("Hata: Klasör yolu boş olamaz!")
        return
    
    print("\nTarama başlatılıyor: {}".format(sunucu_yolu))
    baslangic_zamani = time.time()
    
    tarayici.klasor_tara(sunucu_yolu)
    
    tarayici.html_rapor_olustur()
    
    bitis_zamani = time.time()
    print("\nTarama süresi: {:.2f} saniye".format(bitis_zamani - baslangic_zamani))

if __name__ == "__main__":
    ana_fonksiyon()
