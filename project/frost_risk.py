"""
Zirai Don Riski Hesaplama Modülü
AgriWise Sivas — Anadolu Hackathon 2026
"""

def zirai_don_riski(temperature_c, humidity_pct, wind_speed_kmh,
                    cloud_cover_pct, hour_of_day, season, precipitation_type="none"):
    """
    7 meteorolojik faktöre dayalı zirai don riski hesaplama.

    Parametreler:
        temperature_c     : Hava sıcaklığı (°C)
        humidity_pct      : Bağıl nem (%)
        wind_speed_kmh    : Rüzgar hızı (km/s)
        cloud_cover_pct   : Bulutluluk (%)
        hour_of_day       : Saat (0-23)
        season            : Mevsim (winter/spring/summer/autumn)
        precipitation_type: Yağış tipi (none/rain/snow/hail)

    Dönüş:
        seviye  : YOK / DÜŞÜK / ORTA / YÜKSEK / KRİTİK
        skor    : 0-100 arası risk skoru
        tavsiye : Çiftçiye yönelik Türkçe öneri
    """
    t = float(temperature_c)

    if t >= 4:
        return "YOK", 0, "Zirai don riski yok, normal tarım faaliyetleri sürdürülebilir."

    skor = 0

    # 1. Sıcaklık — ana kriter (0-50 puan)
    if t < -8:    skor += 50
    elif t < -5:  skor += 40
    elif t < -2:  skor += 30
    elif t < 0:   skor += 20
    elif t < 2:   skor += 10
    else:         skor += 5   # 2-4°C arası, gece düşebilir

    # 2. Nem — yüksek nem donun etkisini artırır (0-15 puan)
    nem = float(humidity_pct)
    if nem > 90:    skor += 15
    elif nem > 80:  skor += 10
    elif nem > 70:  skor += 5

    # 3. Rüzgar — sakin hava radyatif donu artırır (0-10 puan)
    ruzgar = float(wind_speed_kmh)
    if ruzgar < 5:    skor += 10
    elif ruzgar < 10: skor += 5
    elif ruzgar > 25: skor -= 5   # güçlü rüzgar sıcaklığı karıştırır

    # 4. Bulutluluk — açık gökyüzü radyatif ısı kaybına yol açar (0-10 puan)
    bulut = float(cloud_cover_pct)
    if bulut < 20:    skor += 10
    elif bulut < 40:  skor += 5

    # 5. Saat — sabah erken saatler en kritik (0-10 puan)
    saat = int(hour_of_day)
    if 3 <= saat <= 7:              skor += 10
    elif saat <= 9 or saat >= 22:   skor += 5

    # 6. Mevsim — ilkbahar donu en tehlikeli (bitkiler aktif büyümede) (0-10 puan)
    if season == "spring":   skor += 10
    elif season == "winter": skor += 3   # kış: bitkiler dormant, görece dayanıklı

    # 7. Yağış tipi — kar/dolu riski artırır (0-5 puan)
    if precipitation_type in ("snow", "hail"):  skor += 5

    # Seviye belirleme
    if skor >= 70:
        seviye = "KRİTİK"
        tavsiye = (
            "🚨 Şiddetli zirai don tehlikesi! "
            "Tarla bitkilerini ve filizleri hemen koruma altına alın. "
            "Sulama sistemlerini dondurun, seraları ısıtın, "
            "hassas ürünleri (nohut, patates) örtü ile kapatın."
        )
    elif skor >= 50:
        seviye = "YÜKSEK"
        tavsiye = (
            "⚠️ Zirai don riski yüksek. "
            "Nohut ve patates filizleri zarar görebilir. "
            "Gece geç saatlerde tarlayı kontrol edin, "
            "don tülbedi veya örtü kullanmayı değerlendirin."
        )
    elif skor >= 30:
        seviye = "ORTA"
        tavsiye = (
            "🌡️ Hafif don olasılığı mevcut. "
            "Hassas bitkiler için don tülbedi önerilir. "
            "Sabah erken saatlerde tarlayı kontrol edin."
        )
    else:
        seviye = "DÜŞÜK"
        tavsiye = (
            "✅ Don riski düşük. "
            "Standart tarım önlemleri yeterlidir, "
            "normal faaliyetlere devam edilebilir."
        )

    return seviye, skor, tavsiye


def don_rengi(seviye):
    """Streamlit arayüzü için renk kodu döner."""
    renkler = {
        "YOK":    "#4CAF50",
        "DÜŞÜK":  "#8BC34A",
        "ORTA":   "#FF9800",
        "YÜKSEK": "#F44336",
        "KRİTİK": "#B71C1C",
    }
    return renkler.get(seviye, "#888888")
