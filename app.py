import streamlit as st
import requests
import json
import base64
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document
from pptx import Presentation
from PIL import Image
from io import BytesIO

# --- SİSTEM AYARLARI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

# API Anahtarı Kontrolü
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("Lütfen Streamlit Secrets kısmına GOOGLE_API_KEY ekleyin!")
    st.stop()

# DOĞRUDAN API ADRESİ (v1beta hatasını önleyen kesin yol)
API_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"

# --- GELİŞMİŞ DOSYA OKUMA MOTORU ---
def dosyayi_metne_cevir(dosya):
    try:
        # PDF Okuma
        if dosya.type == "application/pdf":
            reader = PdfReader(dosya)
            return "\n".join([sayfa.extract_text() for sayfa in reader.pages if sayfa.extract_text()])
        
        # Word (DOCX) Okuma
        elif dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(dosya)
            return "\n".join([p.text for p in doc.paragraphs])
        
        # PowerPoint (PPTX) Okuma
        elif "presentationml" in dosya.type:
            sunum = Presentation(dosya)
            metinler = []
            for slide in sunum.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        metinler.append(shape.text)
            return "\n".join(metinler)
        
        # Excel (XLSX) veya CSV Okuma
        elif "spreadsheetml" in dosya.type or "csv" in dosya.type:
            df = pd.read_excel(dosya) if "spreadsheet" in dosya.type else pd.read_csv(dosya)
            return f"Tablo Verileri (İlk 50 Satır):\n{df.head(50).to_string()}"
            
        return None
    except Exception as e:
        return f"Dosya işlenirken bir hata oluştu: {e}"

# --- ARAYÜZ ---
with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    st.markdown("### Özel Eren Fen ve Teknoloji Lisesi")
    st.divider()
    mod = st.selectbox("Asistan Modu", ["Eren AI Asistanı", "Döküman Analizi", "Akademik Rehber"])
    st.caption("© 2026 Eren Eğitim Kurumları")

st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Sohbet Geçmişi
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Giriş Bölümü
with st.container():
    sol, sag = st.columns([1, 4])
    with sol:
        yukle = st.file_uploader("Dosya", type=['pdf','docx','pptx','xlsx','csv','png','jpg','jpeg'], label_visibility="collapsed")
    with sag:
        soru = st.chat_input("Eren AI'ya bir soru sorun...")

# --- YANIT ÜRETİMİ ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        cevap_alani = st.empty()
        cevap_alani.info("🛡️ Eren AI analiz ediyor...")
        
        # İstek Hazırlığı
        sistem_mesaji = f"Sen Eren AI'sın. Profesyonel bir lise asistanısın. Mod: {mod}."
        payload = {"contents": [{"parts": [{"text": f"{sistem_mesaji}\n\nSoru: {soru}"}]}]}
        
        if yukle:
            if yukle.type.startswith("image/"):
                # Görselleri Base64 olarak ekle
                img_data = base64.b64encode(yukle.read()).decode('utf-8')
                payload["contents"][0]["parts"].append({
                    "inline_data": {"mime_type": yukle.type, "data": img_data}
                })
            else:
                # Dökümanları metne çevirip ekle
                belge_metni = dosyayi_metne_cevir(yukle)
                if belge_metni:
                    payload["contents"][0]["parts"][0]["text"] += f"\n\n[BELGE İÇERİĞİ]:\n{belge_metni}"

        # API Çağrısı
        try:
            res = requests.post(API_URL, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
            veriler = res.json()
            
            if "candidates" in veriler:
                cevap = veriler["candidates"][0]["content"]["parts"][0]["text"]
                cevap_alani.markdown(cevap)
                st.session_state.messages.append({"role": "assistant", "content": cevap})
            else:
                hata = veriler.get("error", {}).get("message", "API yanıt vermedi.")
                cevap_alani.error(f"Erişim Sorunu: {hata}")
        except Exception as e:
            cevap_alani.error(f"Bağlantı Hatası: {e}")
