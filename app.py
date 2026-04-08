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
    st.error("Lütfen Secrets kısmına GOOGLE_API_KEY ekleyin!")
    st.stop()

# DOĞRUDAN API YOLU (Hata vermesi imkansız adres)
API_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"

# --- GELİŞMİŞ DOSYA OKUMA SİSTEMİ ---
def dosya_icerigini_metne_dok(dosya):
    try:
        if dosya.type == "application/pdf":
            return "\n".join([p.extract_text() for p in PdfReader(dosya).pages if p.extract_text()])
        elif dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return "\n".join([p.text for p in Document(dosya).paragraphs])
        elif "presentationml" in dosya.type:
            pptx = Presentation(dosya)
            text = [shape.text for slide in pptx.slides for shape in slide.shapes if hasattr(shape, "text")]
            return "\n".join(text)
        elif "spreadsheet" in dosya.type or "csv" in dosya.type:
            df = pd.read_excel(dosya) if "spreadsheet" in dosya.type else pd.read_csv(dosya)
            return f"Tablo Verileri:\n{df.to_string()}"
        return None
    except Exception as e:
        return f"Dosya okuma hatası: {e}"

# --- ARAYÜZ TASARIMI ---
with st.sidebar:
    st.title("🛡️ Eren AI")
    # Logo hatasını engellemek için metin tabanlı başlık
    st.markdown("### Özel Eren Fen ve Teknoloji Lisesi")
    st.divider()
    mod = st.selectbox("Asistan Modu", ["Eren AI Asistanı", "Akademik Analiz", "Veli Rehberi"])
    st.caption("© 2026 Eren Eğitim Kurumları")

st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Mesaj Geçmişi
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Giriş Alanları
with st.container():
    sol, sag = st.columns([1, 4])
    with sol:
        yuklenen_dosya = st.file_uploader("Dosya", type=['pdf','docx','pptx','xlsx','csv','jpg','png','jpeg'], label_visibility="collapsed")
    with sag:
        kullanici_sorusu = st.chat_input("Eren AI'ya sorunuzu iletin...")

# --- İŞLEME VE REST API ÇAĞRISI ---
if kullanici_sorusu:
    st.session_state.messages.append({"role": "user", "content": kullanici_sorusu})
    with st.chat_message("user"):
        st.markdown(kullanici_sorusu)

    with st.chat_message("assistant"):
        cevap_alani = st.empty()
        cevap_alani.info("🛡️ Eren AI v1 kanalı üzerinden verileri analiz ediyor...")
        
        # API Payload Hazırlığı
        prompt_full = f"Sen Eren AI'sın. Mod: {mod}. Profesyonel ve yardımcı bir asistan ol. Soru: {kullanici_sorusu}"
        payload = {"contents": [{"parts": [{"text": prompt_full}]}]}
        
        if yuklenen_dosya:
            if yuklenen_dosya.type.startswith("image/"):
                # Görseli Base64 formatına çevirip doğrudan gönderiyoruz
                img_b64 = base64.b64encode(yuklenen_dosya.read()).decode('utf-8')
                payload["contents"][0]["parts"].append({
                    "inline_data": {"mime_type": yuklenen_dosya.type, "data": img_b64}
                })
            else:
                # Dökümanları metne çevirip prompt'a ekliyoruz
                metin_icerik = dosya_icerigini_metne_dok(yuklenen_dosya)
                if metin_icerik:
                    payload["contents"][0]["parts"][0]["text"] += f"\n\n[BELGE İÇERİĞİ]:\n{metin_icerik}"

        # API İstek Gönderimi
        try:
            response = requests.post(API_URL, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
            data = response.json()
            
            if "candidates" in data:
                ai_yaniti = data["candidates"][0]["content"]["parts"][0]["text"]
                cevap_alani.markdown(ai_yaniti)
                st.session_state.messages.append({"role": "assistant", "content": ai_yaniti})
            else:
                hata_detay = data.get("error", {}).get("message", "Bilinmeyen API hatası")
                cevap_alani.error(f"Erişim Hatası: {hata_detay}")
        except Exception as e:
            cevap_alani.error(f"Bağlantı Hatası: {e}")
