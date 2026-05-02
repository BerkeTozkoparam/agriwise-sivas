"""
AgriWise Sivas — Ana Uygulama
Anadolu Hackathon 2026 | WeatherWise Kategorisi

Çalıştırma:
    streamlit run app.py --server.port 8000 --server.address 0.0.0.0
"""

import streamlit as st
import pandas as pd
import requests
import os
import json
from datetime import datetime
from frost_risk import zirai_don_riski, don_rengi

# ── Sayfa ayarları ─────────────────────────────────────────────────
st.set_page_config(
    page_title="AgriWise Sivas",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-title {
        font-size: 2.4rem; font-weight: 800;
        color: #1B5E20; margin-bottom: 0;
    }
    .sub-title {
        font-size: 1rem; color: #555; margin-top: 0;
    }
    .risk-box {
        padding: 1.2rem 1.5rem; border-radius: 12px;
        margin: 0.5rem 0; font-size: 1.05rem;
    }
    .metric-card {
        background: #F1F8E9; border-radius: 10px;
        padding: 1rem; text-align: center;
        border-left: 5px solid #2E7D32;
    }
    .tavsiye-box {
        background: #FFFDE7; border-left: 5px solid #F9A825;
        border-radius: 8px; padding: 1rem 1.2rem;
        font-size: 0.98rem; line-height: 1.6;
    }
    .stSelectbox label, .stSlider label { font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ── Başlık ─────────────────────────────────────────────────────────
st.markdown('<p class="main-title">🌾 AgriWise Sivas</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Sivas Bölgesi Tarım Hava Danışma Sistemi | Anadolu Hackathon 2026</p>', unsafe_allow_html=True)
st.divider()

# ── Model yükleme ──────────────────────────────────────────────────
@st.cache_resource
def load_ml_models():
    try:
        from model import load_models
        don_model, suit_model, features, le_dict = load_models()
        return don_model, suit_model, features, le_dict, True
    except Exception as e:
        return None, None, None, None, False

don_model, suit_model, features, le_dict, model_loaded = load_ml_models()

# ── Open-Meteo API ─────────────────────────────────────────────────
ISTASYONLAR = {
    "Sivas Merkez":       (39.748, 37.016, 1285),
    "Sivas Üniversitesi": (39.756, 37.025, 1295),
    "Sivas Sanayi":       (39.740, 37.010, 1270),
    "Kangal":             (39.235, 37.388, 1200),
    "Zara":               (39.898, 37.750, 1350),
    "Suşehri":            (40.161, 38.087,  900),
}

@st.cache_data(ttl=1800)
def get_weather(lat, lon):
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,"
        f"wind_gusts_10m,precipitation,cloud_cover,visibility,uv_index,weather_code"
        f"&hourly=temperature_2m,precipitation_probability,wind_speed_10m"
        f"&daily=temperature_2m_min,temperature_2m_max,precipitation_sum,"
        f"wind_speed_10m_max,snowfall_sum"
        f"&timezone=Europe/Istanbul&forecast_days=3"
    )
    try:
        resp = requests.get(url, timeout=8)
        return resp.json()
    except Exception:
        return None

def weather_code_to_condition(code):
    if code == 0:   return "clear"
    if code <= 3:   return "partly_cloudy"
    if code <= 48:  return "cloudy"
    if code <= 67:  return "rain"
    if code <= 77:  return "snow"
    if code <= 82:  return "rain"
    if code <= 99:  return "thunderstorm"
    return "clear"

def ay_to_mevsim(ay):
    if ay in (12, 1, 2):  return "winter"
    if ay in (3, 4, 5):   return "spring"
    if ay in (6, 7, 8):   return "summer"
    return "autumn"

# ── Sidebar ────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Ayarlar")
    istasyon = st.selectbox("📍 İstasyon", list(ISTASYONLAR.keys()))
    urun = st.selectbox(
        "🌱 Ürün Türü",
        ["Buğday / Arpa", "Nohut", "Patates", "Şeker Pancarı", "Genel"]
    )
    st.divider()
    st.caption("Veri kaynağı: Open-Meteo API")
    st.caption("Model: XGBoost + Kural Motoru")
    st.caption("Hackathon: Anadolu 2026")

# ── Ana içerik ─────────────────────────────────────────────────────
lat, lon, elev = ISTASYONLAR[istasyon]
weather = get_weather(lat, lon)

if weather is None:
    st.error("Hava verisi alınamadı. İnternet bağlantısını kontrol edin.")
    st.stop()

cur = weather.get("current", {})
daily = weather.get("daily", {})
now = datetime.now()
mevsim = ay_to_mevsim(now.month)

temp       = cur.get("temperature_2m", 0)
nem        = cur.get("relative_humidity_2m", 60)
ruzgar     = cur.get("wind_speed_10m", 0)
gust       = cur.get("wind_gusts_10m", 0)
yagis      = cur.get("precipitation", 0)
bulut      = cur.get("cloud_cover", 50)
uv         = cur.get("uv_index", 0)
wcode      = cur.get("weather_code", 0)
condition  = weather_code_to_condition(wcode)
temp_min   = daily.get("temperature_2m_min", [temp])[0]
temp_max   = daily.get("temperature_2m_max", [temp])[0]

# Don riski hesapla
don_sev, don_skor, don_tavsiye = zirai_don_riski(
    temperature_c=temp, humidity_pct=nem,
    wind_speed_kmh=ruzgar, cloud_cover_pct=bulut,
    hour_of_day=now.hour, season=mevsim,
    precipitation_type="snow" if wcode >= 71 else ("rain" if wcode >= 51 else "none")
)

# ML tahmini (model yüklüyse)
ml_result = None
if model_loaded:
    try:
        from model import predict
        ml_result = predict(
            {
                "temperature_c": temp, "humidity_pct": nem,
                "wind_speed_kmh": ruzgar, "wind_gust_kmh": gust,
                "precipitation_mm": yagis, "cloud_cover_pct": bulut,
                "visibility_km": cur.get("visibility", 10000) / 1000,
                "uv_index": uv, "is_thunderstorm": int(wcode >= 95),
                "hour_of_day": now.hour, "month": now.month,
                "temp_min_c": temp_min, "temp_max_c": temp_max,
                "total_precipitation_mm": daily.get("precipitation_sum", [0])[0],
                "snow_hours": daily.get("snowfall_sum", [0])[0],
                "rain_hours": 0, "max_wind_kmh": daily.get("wind_speed_10m_max", [ruzgar])[0],
                "thunderstorm_occurred": int(wcode >= 95),
                "season": mevsim, "climate_zone": "semi-arid_continental",
                "precipitation_type": "snow" if wcode >= 71 else "none",
                "dominant_condition": condition,
            },
            don_model, suit_model, features, le_dict
        )
    except Exception as e:
        ml_result = None

# ── Anlık durum satırı ────────────────────────────────────────────
st.subheader(f"📍 {istasyon} — Anlık Durum")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("🌡️ Sıcaklık", f"{temp:.1f}°C", f"Min {temp_min:.0f}° / Max {temp_max:.0f}°")
c2.metric("💧 Nem", f"%{nem:.0f}")
c3.metric("💨 Rüzgar", f"{ruzgar:.0f} km/s", f"Rüzgar gülü: {gust:.0f}")
c4.metric("🌧️ Yağış", f"{yagis:.1f} mm")
c5.metric("☁️ Bulutluluk", f"%{bulut:.0f}")

st.divider()

# ── Don riski kutusu ──────────────────────────────────────────────
col_don, col_tavsiye = st.columns([1, 2])

with col_don:
    renk = don_rengi(don_sev)
    st.markdown(f"""
    <div class="risk-box" style="background:{renk}22; border-left: 6px solid {renk};">
        <div style="font-size:1.5rem; font-weight:800; color:{renk};">
            ZİRAİ DON RİSKİ
        </div>
        <div style="font-size:2.5rem; font-weight:900; color:{renk};">
            {don_sev}
        </div>
        <div style="font-size:0.9rem; color:#555;">
            Risk Skoru: {don_skor} / 100
        </div>
    </div>
    """, unsafe_allow_html=True)

    if ml_result:
        st.markdown(f"""
        <div class="metric-card" style="margin-top:0.8rem;">
            <div style="font-size:0.8rem; color:#555;">ML Modeli — Tarım Uygunluğu</div>
            <div style="font-size:1.8rem; font-weight:800; color:#2E7D32;">
                {ml_result['tarim_uygunluk']:.1f} / 10
            </div>
        </div>
        """, unsafe_allow_html=True)

with col_tavsiye:
    st.markdown("**📋 Tavsiye**")
    st.markdown(f'<div class="tavsiye-box">{don_tavsiye}</div>', unsafe_allow_html=True)

    # Ürüne özel ek tavsiye
    urun_tavsiyeler = {
        "Nohut": {
            "KRİTİK": "🫘 Nohut filizleri 0°C altında ciddi hasar görür — örtü kullanımı zorunlu.",
            "YÜKSEK": "🫘 Nohut için don riski kritik eşikte — gece tarlayı kontrol edin.",
            "ORTA":   "🫘 Nohut hassastır — sabah erken kontrol önerilir.",
            "DÜŞÜK":  "🫘 Nohut için koşullar kabul edilebilir.",
            "YOK":    "🫘 Nohut tarım faaliyetleri için uygun hava.",
        },
        "Patates": {
            "KRİTİK": "🥔 Patates filizleri don altında 2 saatte hasar görür — acil örtü!",
            "YÜKSEK": "🥔 Patates için don riski var — toprak örtüsü değerlendirin.",
            "ORTA":   "🥔 Patates filizlerini izleyin, sabah kontrol edin.",
            "DÜŞÜK":  "🥔 Patates için koşullar uygun.",
            "YOK":    "🥔 Patates yetiştiriciliği için iyi hava.",
        },
        "Buğday / Arpa": {
            "KRİTİK": "🌾 -4°C altı buğday kardeşlenmesine zarar verir — tarlayı kontrol edin.",
            "YÜKSEK": "🌾 Buğday için don riski yüksek — özellikle genç filizleri izleyin.",
            "ORTA":   "🌾 Hafif don riski — buğday genel olarak dayanıklı ama dikkat.",
            "DÜŞÜK":  "🌾 Buğday için normal koşullar.",
            "YOK":    "🌾 Buğday/arpa faaliyetleri için uygun hava.",
        },
        "Şeker Pancarı": {
            "KRİTİK": "🔴 -5°C altı pancar dokusuna kalıcı hasar verir — acil hasat planlayın!",
            "YÜKSEK": "🔴 Şeker pancarı don riskinde — hasat zamanlamasını gözden geçirin.",
            "ORTA":   "🔴 Pancar için hafif risk — Sivas Şeker Fabrikası teslimatını planlayın.",
            "DÜŞÜK":  "🔴 Şeker pancarı için uygun koşullar.",
            "YOK":    "🔴 Şeker pancarı faaliyetleri için iyi hava.",
        },
    }

    if urun in urun_tavsiyeler:
        urun_mesaj = urun_tavsiyeler[urun].get(don_sev, "")
        if urun_mesaj:
            st.markdown(f'<div class="tavsiye-box" style="margin-top:0.5rem; border-color:#2E7D32;">{urun_mesaj}</div>', unsafe_allow_html=True)

st.divider()

# ── 3 Günlük Tahmin ───────────────────────────────────────────────
st.subheader("📅 3 Günlük Don Risk Tahmini")

dates     = daily.get("time", [])
min_temps = daily.get("temperature_2m_min", [])
max_temps = daily.get("temperature_2m_max", [])
precips   = daily.get("precipitation_sum", [])
winds     = daily.get("wind_speed_10m_max", [])

cols_3day = st.columns(min(3, len(dates)))
for i, col in enumerate(cols_3day):
    if i >= len(dates):
        break
    d_temp_min = min_temps[i] if i < len(min_temps) else 0
    d_temp_max = max_temps[i] if i < len(max_temps) else 0
    d_precip   = precips[i]   if i < len(precips)   else 0
    d_wind     = winds[i]     if i < len(winds)      else 0

    # Geceleri don riski için min sıcaklığı kullan, saat=4
    d_sev, d_skor, _ = zirai_don_riski(
        temperature_c=d_temp_min, humidity_pct=75,
        wind_speed_kmh=d_wind, cloud_cover_pct=30,
        hour_of_day=4, season=mevsim
    )
    d_renk = don_rengi(d_sev)
    gun_adi = ["Bugün", "Yarın", "Öbür Gün"][i]

    with col:
        st.markdown(f"""
        <div style="border:2px solid {d_renk}; border-radius:10px; padding:1rem; text-align:center;">
            <div style="font-weight:700; font-size:1rem;">{gun_adi}</div>
            <div style="font-size:0.8rem; color:#777;">{dates[i]}</div>
            <div style="font-size:1.5rem; margin:0.3rem 0;">
                {d_temp_min:.0f}° / {d_temp_max:.0f}°C
            </div>
            <div style="background:{d_renk}; color:white; border-radius:6px;
                        padding:0.2rem 0.5rem; font-weight:700; display:inline-block;">
                {d_sev}
            </div>
            <div style="font-size:0.82rem; margin-top:0.4rem; color:#555;">
                🌧️ {d_precip:.1f}mm &nbsp; 💨 {d_wind:.0f}km/s
            </div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# ── ML Olasılık dağılımı ──────────────────────────────────────────
if ml_result:
    st.subheader("🤖 ML Modeli — Don Riski Olasılıkları")
    proba_df = pd.DataFrame(
        list(ml_result["don_olasilik"].items()),
        columns=["Seviye", "Olasılık (%)"]
    ).set_index("Seviye")
    st.bar_chart(proba_df)

# ── Footer ────────────────────────────────────────────────────────
st.caption("AgriWise Sivas · Anadolu Hackathon 2026 · WeatherWise Kategorisi · Veri: Open-Meteo API")
