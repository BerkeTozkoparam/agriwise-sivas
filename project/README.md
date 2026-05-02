# AgriWise Sivas
**Anadolu Hackathon 2026 | WeatherWise Kategorisi**

Sivas bölgesi çiftçileri için hava verisini tarım tavsiyesine dönüştüren AI sistemi.

---

## Kurulum

```bash
pip install -r requirements.txt
```

## Modeli Eğit

```bash
python model.py
```

## Uygulamayı Başlat

```bash
# Lokal geliştirme
streamlit run app.py

# VM'de (port 8000 — hackathon gereksinimi)
bash run.sh
```

## Proje Yapısı

```
project/
├── app.py            # Streamlit arayüzü (port 8000)
├── model.py          # XGBoost model eğitimi ve tahmin
├── frost_risk.py     # Zirai don riski algoritması (7 faktör)
├── requirements.txt  # Bağımlılıklar
├── run.sh            # VM başlatma scripti
└── data/
    └── agriwise_model_dataset.csv  # Temizlenmiş eğitim verisi
```

## Model Performansı

| Model | Metrik | Sonuç |
|---|---|---|
| Don Sınıflandırma (XGBoost) | Accuracy | **%98.6** |
| Don Sınıflandırma (XGBoost) | F1 (weighted) | **0.986** |
| Tarım Uygunluk (XGBoost) | MAE | **0.198** |

## Geliştirici Ekip

| | |
|---|---|
| **Berke Baran Tozkoparan** | Model geliştirme, backend |
| **Aliyenur Bulduk** | Geliştirme |

---

## VM Deploy (Hackathon)

```bash
scp agriwise_sivas_full.zip user@vm:~/
ssh user@vm
unzip agriwise_sivas_full.zip
cd project
bash run.sh
# → http://VM_IP:8000
```
