# Jurnal Rasa

Web catatan harian dengan mood tracker. Backend: Python (Flask + SQLite). Frontend: HTML + CSS + sedikit JavaScript.

## Cara menjalankan
```
pip install -r requirements.txt
python app.py
```
Buka http://127.0.0.1:5000 di browser. File database `diary.db` dibuat otomatis.

## Struktur
```
jurnal-rasa/
├── app.py              # backend Flask: route, database, validasi
├── requirements.txt
├── templates/index.html
└── static/
    ├── style.css
    └── script.js
```
