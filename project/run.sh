#!/bin/bash
# AgriWise Sivas — VM Başlatma Scripti
# Anadolu Hackathon 2026

set -e
cd ~/project

echo "=== AgriWise Sivas ==="
echo "Bağımlılıklar yükleniyor..."
pip install -r requirements.txt -q

echo "Model eğitiliyor..."
python model.py

echo "Uygulama başlatılıyor (port 8000)..."
streamlit run app.py \
    --server.port 8000 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false
