import os
import re
import json
import time
import html
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

class BackdoorChecker:
    def __init__(self):
        self.guvenilir_domainler = {
            'github.com',
            'raw.githubusercontent.com',
            'discord.com',
            'discordapp.com',
            'cdn.discordapp.com',
            'fivemanager.com',
            'api.fivemanager.com',
            'localhost',
            '127.0.0.1'
        }
        
        self.arkakapilar_deseni = {
            'uzaktan_calistirma': [
                r'load\s*\(\s*.*\s*\)\s*\(\s*\)',
                r'loadstring\s*\(\s*.*\s*\)',
                r'dofile\s*\(\s*.*http.*\s*\)',
                r'require\s*\(\s*.*http.*\s*\)',
                r'RunString\s*\(\s*.*\s*\)',
                r'CompileString\s*\(\s*.*\s*\)',
                r'load\s*\(\s*.*http.*\s*\)',
                r'assert\s*\(\s*load\s*\(',
                r'pcall\s*\(\s*load\s*\(',
                r'xpcall\s*\(\s*load\s*\(',
                r'getfenv\s*\(\s*\)\s*\[.*string\.char.*\]',
            ],
            
            'supleli_http_baglanti': [
                r'PerformHttpRequest\s*\(\s*["\'].*?["\']',
                r'http\.post\s*\(\s*["\'].*?["\']',
                r'http\.get\s*\(\s*["\'].*?["\']',
                r'HttpRequest\s*\(\s*["\'].*?["\']',
                r'fetch\s*\(\s*["\'].*?["\']',
                r'request\s*\(\s*["\'].*?["\']',
                r'curl\s*.*?http',
                r'wget\s*.*?http',
            ],
            
            'supleli_komutlar': [
                r'ExecuteCommand\s*\(\s*["\'].*?restart.*?["\']',
                r'ExecuteCommand\s*\(\s*["\'].*?stop.*?["\']',
                r'ExecuteCommand\s*\(\s*["\'].*?quit.*?["\']',
                r'ExecuteCommand\s*\(\s*["\'].*?refresh.*?["\']',
                r'ExecuteCommand\s*\(\s*["\'].*?ban.*?["\']',
                r'ExecuteCommand\s*\(\s*["\'].*?kick.*?["\']',
                r'TriggerServerEvent\s*\(\s*["\'].*?__cfx_internal.*?["\']',
                r'TriggerServerEvent\s*\(\s*["\'].*?rconCommand.*?["\']',
                r'rconPassword\s*=',
            ],
            
            'dosya_erisim': [
                r'io\.open\s*\(\s*["\'].*?\.exe.*?["\']',
                r'io\.popen\s*\(\s*["\'].*?cmd.*?["\']',
                r'os\.execute\s*\(\s*["\'].*?["\']',
                r'os\.remove\s*\(\s*["\'].*?\.lua.*?["\']',
                r'file\.Delete\s*\(\s*["\'].*?["\']',
                r'file\.Write\s*\(\s*["\'].*?\.lua.*?["\']',
                r'file\.Read\s*\(\s*["\'].*?config.*?["\']',
                r'LoadResourceFile\s*\(\s*.*?,\s*["\'].*?\.lua.*?["\']',
            ],
            
            'sifreli_kod': [
                r'_G\[.*?\]\s*=\s*function',
                r'getfenv\s*\(\s*\)\s*\[.*?\]',
                r'string\.char\s*\(\s*\d+(?:\s*,\s*\d+){10,}',
                r'\\x[0-9a-fA-F]{2}.*?\\x[0-9a-fA-F]{2}.*?\\x[0-9a-fA-F]{2}',
                r'base64\.decode\s*\(',
                r'fromhex\s*\(',
                r'unhex\s*\(',
                r'utf8\.char\s*\(\s*\d+(?:\s*,\s*\d+){5,}',
            ]
        }
        
        self.beyaz_liste_deseni = [
            r'--.*?backdoor',
            r'print\s*\(\s*["\'].*?backdoor.*?["\']',
            r'exports\[.*?\]',
            r'-- Example:',
            r'-- Test:',
            r'debug\.getinfo',
        ]
        
        self.url_deseni = re.compile(r'https?://([^/\s\'"]+)', re.IGNORECASE)
        
        self.tarama_sonuclari = []
        self.toplam_dosya = 0
        self.taranan_dosya = 0
        
    def beyaz_listede_mi(self, satir):
        for desen in self.beyaz_liste_deseni:
            if re.search(desen, satir, re.IGNORECASE):
                return True
        return False
    
    def url_guvenli_mi(self, url):
        try:
            parsed = urlparse(url.lower())
            domain = parsed.netloc
            
            if ':' in domain:
                domain = domain.split(':')[0]
            
            if domain.startswith('www.'):
                domain = domain[4:]
            
            return domain in self.guvenilir_domainler
        except:
            return False
    
    def http_istegi_analiz_et(self, satir):
        urls = self.url_deseni.findall(satir)
        supleli_urls = []
        
        for url in urls:
            full_url = 'http://' + url
            if not self.url_guvenli_mi(full_url):
                supleli_urls.append(url)
        
        return supleli_urls
    
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
                            if kategori == 'supleli_http_baglanti':
                                supleli_urls = self.http_istegi_analiz_et(satir)
                                if supleli_urls:
                                    tespit_detayi = "Şüpheli URL: " + ", ".join(supleli_urls)
                                    tespitler.append({
                                        'dosya': str(dosya_yolu),
                                        'satir_numarasi': satir_no,
                                        'satir_icerik': satir.strip(),
                                        'kategori': 'supleli_http_baglanti',
                                        'desen': desen,
                                        'detay': tespit_detayi,
                                        'risk_seviye': 'YUKSEK'
                                    })
                            else:
                                tespitler.append({
                                    'dosya': str(dosya_yolu),
                                    'satir_numarasi': satir_no,
                                    'satir_icerik': satir.strip(),
                                    'kategori': kategori,
                                    'desen': desen,
                                    'detay': '',
                                    'risk_seviye': self.risk_seviyesi_belirle(kategori)
                                })
            
            return tespitler
            
        except Exception as e:
            print("Hata - {} dosyası okunamadı: {}".format(dosya_yolu, e))
            return []
    
    def risk_seviyesi_belirle(self, kategori):
        yuksek_risk = ['uzaktan_calistirma', 'dosya_erisim', 'supleli_http_baglanti', 'yetki_yukseltme']
        orta_risk = ['supleli_komutlar', 'sql_enjeksiyon', 'network_manipulation']
        dusuk_risk = ['sifreli_kod']
        
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
        
        dosya_uzantilari = ['*.lua', '*.LUA']
        script_dosyalari = []
        
        for uzanti in dosya_uzantilari:
            script_dosyalari.extend(klasor.rglob(uzanti))
        
        self.toplam_dosya = len(script_dosyalari)
        print("Taranacak dosya sayısı: {}".format(self.toplam_dosya))
        print("-" * 50)
        
        for dosya_yolu in script_dosyalari:
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
        
        print("\nTOPLAM {} ŞÜPHELİ KOD TESPİT EDİLDİ!".format(len(self.tarama_sonuclari)))
        
        html_parcalari = []
        html_parcalari.append("""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FiveM Backdoor Tarama Raporu</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border: 1px solid #ddd;
        }
        h1 {
            color: #d32f2f;
            text-align: center;
            margin-bottom: 20px;
            font-size: 24px;
        }
        .stats {
            display: flex;
            justify-content: space-around;
            margin-bottom: 20px;
            padding: 15px;
            background-color: #f8f8f8;
            border: 1px solid #ddd;
        }
        .stat-item {
            text-align: center;
        }
        .stat-number {
            font-size: 20px;
            font-weight: bold;
            color: #d32f2f;
        }
        .stat-label {
            font-size: 12px;
            color: #666;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            font-size: 12px;
        }
        th {
            background-color: #333;
            color: white;
            padding: 10px 8px;
            text-align: left;
            font-weight: normal;
        }
        td {
            padding: 8px;
            border-bottom: 1px solid #ddd;
            vertical-align: top;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        .risk-high {
            background-color: #ffebee !important;
            border-left: 3px solid #f44336;
        }
        .risk-medium {
            background-color: #fff3e0 !important;
            border-left: 3px solid #ff9800;
        }
        .risk-low {
            background-color: #f3e5f5 !important;
            border-left: 3px solid #9c27b0;
        }
        .file-path {
            font-family: 'Courier New', monospace;
            font-size: 10px;
            background-color: #f0f0f0;
            padding: 2px 4px;
        }
        .code-content {
            font-family: 'Courier New', monospace;
            background-color: #f0f0f0;
            padding: 4px;
            font-size: 10px;
            max-width: 300px;
            word-break: break-all;
        }
        .category {
            padding: 2px 6px;
            font-size: 10px;
            color: white;
            border-radius: 3px;
        }
        .cat-uzaktan_calistirma { background-color: #f44336; }
        .cat-supleli_http_baglanti { background-color: #ff5722; }
        .cat-supleli_komutlar { background-color: #9c27b0; }
        .cat-dosya_erisim { background-color: #e91e63; }
        .cat-sifreli_kod { background-color: #4caf50; }
        .footer {
            margin-top: 20px;
            padding: 15px;
            background-color: #f8f8f8;
            border: 1px solid #ddd;
            font-size: 11px;
            color: #666;
        }
        .warning {
            background-color: #fff3cd;
            color: #856404;
            padding: 10px;
            border: 1px solid #ffeaa7;
            margin-bottom: 15px;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Backdoor Tarama Raporu</h1>
        
        <div class="warning">
            Bu raporda tespit edilen kodları manual olarak kontrol edin. Sistem sadece şüpheli pattern'leri tespit eder.
        </div>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-number">""" + str(self.taranan_dosya) + """</div>
                <div class="stat-label">Taranan Dosya</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">""" + str(len(self.tarama_sonuclari)) + """</div>
                <div class="stat-label">Tespit Edilen</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">""" + str(len([x for x in self.tarama_sonuclari if x['risk_seviye'] == 'YUKSEK'])) + """</div>
                <div class="stat-label">Yüksek Risk</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">""" + datetime.now().strftime('%d.%m.%Y') + """</div>
                <div class="stat-label">Tarama Tarihi</div>
            </div>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th width="25%">Dosya</th>
                    <th width="5%">Satır</th>
                    <th width="8%">Risk</th>
                    <th width="15%">Kategori</th>
                    <th width="47%">Kod İçeriği</th>
                </tr>
            </thead>
            <tbody>""")
        
        for sonuc in self.tarama_sonuclari:
            if sonuc['risk_seviye'] == 'YUKSEK':
                risk_class = 'risk-high'
            elif sonuc['risk_seviye'] == 'ORTA':
                risk_class = 'risk-medium'
            else:
                risk_class = 'risk-low'
            
            kategori_class = 'cat-' + sonuc['kategori']
            kategori_display = sonuc['kategori'].replace('_', ' ').title()
            
            dosya_yolu = sonuc['dosya'].replace('\\', '/')
            if len(dosya_yolu) > 40:
                dosya_yolu = '...' + dosya_yolu[-37:]
            
            kod_icerik = html.escape(sonuc['satir_icerik'])
            if len(kod_icerik) > 80:
                kod_icerik = kod_icerik[:77] + '...'
            
            detay_html = ""
            if sonuc.get('detay'):
                detay_html = f'<br><small style="color: #666;">{html.escape(sonuc["detay"])}</small>'
            
            html_parcalari.append(f"""
                <tr class="{risk_class}">
                    <td><span class="file-path">{html.escape(dosya_yolu)}</span></td>
                    <td style="text-align: center;">{sonuc['satir_numarasi']}</td>
                    <td style="text-align: center; font-weight: bold;">{sonuc['risk_seviye']}</td>
                    <td><span class="category {kategori_class}">{kategori_display}</span></td>
                    <td><div class="code-content">{kod_icerik}</div>{detay_html}</td>
                </tr>""")
        
        html_parcalari.append("""
            </tbody>
        </table>
        
        <div class="footer">
            <strong>Risk Seviyeleri:</strong><br>
            Yüksek Risk: Derhal kontrol edilmeli<br>
            Orta Risk: İncelenmesi önerilir<br>
            Düşük Risk: False positive olabilir<br><br>
            <strong>Not:</strong> Bu tool sadece şüpheli kod kalıplarını tespit eder. Her tespit gerçek bir tehdit olmayabilir.
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
        
        print("\n" + "="*50)
        print("DETAYLI İSTATİSTİKLER")
        print("="*50)
        print("Risk Seviyeleri:")
        for risk, sayi in sorted(risk_istatistik.items()):
            print(f"    {risk}: {sayi}")
        
        print("\nKategoriler:")
        for kategori, sayi in sorted(kategori_istatistik.items()):
            kategori_tr = kategori.replace('_', ' ').title()
            print(f"    {kategori_tr}: {sayi}")
        
        print(f"\nRaporu görüntülemek için {cikti_dosya} dosyasını tarayıcınızda açın.")

def ana_fonksiyon():
    print("FiveM Backdoor Checker")
    print("=" * 50)
    
    tarayici = BackdoorChecker()
    
    while True:
        sunucu_yolu = input("\nFiveM sunucu klasör yolunu girin (örn: C:\\fivem-server\\resources): ").strip()
        
        if not sunucu_yolu:
            print("Hata: Klasör yolu boş olamaz!")
            continue
        
        if not os.path.exists(sunucu_yolu):
            print(f"Hata: {sunucu_yolu} klasörü bulunamadı!")
            continue
        
        break
    
    print(f"\nTarama başlatılıyor: {sunucu_yolu}")
    
    baslangic_zamani = time.time()
    
    tarayici.klasor_tara(sunucu_yolu)
    
    if tarayici.tarama_sonuclari:
        print(f"\n🚨 DİKKAT: {len(tarayici.tarama_sonuclari)} şüpheli kod tespit edildi!")
        
        yuksek_risk = len([x for x in tarayici.tarama_sonuclari if x['risk_seviye'] == 'YUKSEK'])
        if yuksek_risk > 0:
            print(f"🔴 {yuksek_risk} adet YÜKSEK RİSKLİ kod tespit edildi!")
    
    tarayici.html_rapor_olustur()
    
    bitis_zamani = time.time()
    print(f"\nTarama süresi: {bitis_zamani - baslangic_zamani:.2f} saniye")
    print("Tarama tamamlandı!")

if __name__ == "__main__":
    ana_fonksiyon()
