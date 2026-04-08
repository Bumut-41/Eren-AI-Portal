import streamlit as st
import requests
import json
import PIL.Image
import base64
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document
from pptx import Presentation
from io import BytesIO

# --- 1. SİSTEM AYARLARI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("API Anahtarı bulunamadı!")
    st.stop()

# Doğrudan v1 adresini kullanıyoruz, v1beta hatası imkansız hale geliyor
API_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"

# --- 2. GELİŞMİŞ DOSYA OKUYUCU ---
def dosya_oku(dosya):
    try:
        if dosya.type == "application/pdf":
            return "\n".join([p.extract_text() for p in PdfReader(dosya).pages if p.extract_text()])
        elif dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return "\n".join([p.text for p in Document(dosya).paragraphs])
        elif "presentationml" in dosya.type:
            return "\n".join([s.text for sl in Presentation(dosya).slides for s in sl.shapes if hasattr(s, "text")])
        elif "spreadsheet" in dosya.type or "csv" in dosya.type:
            df = pd.read_excel(dosya) if "spreadsheet" in dosya.type else pd.read_csv(dosya)
            return df.to_string()
        return None
    except Exception as e:
        return f"Hata: {e}"

# --- 3. ARAYÜZ ---
with st.sidebar:
    st.title("🛡️ Eren AI")
    st.image("https://eren.k12.tr/wp-content/uploads/2021/05/ozel-eren-logo-1.png", width=180)
    st.divider()
    mod = st.selectbox("Mod", ["Eren AI Asistanı", "Akademik Analiz"])
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        belge = st.file_uploader("Belge", type=['pdf','docx','pptx','xlsx','csv','png','jpg'], label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya sorun...")

# --- 4. REST API İLE YANIT ÜRETİMİ ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        alan = st.empty()
        alan.info("🛡️ Eren AI doğrudan v1 kanalıyla bağlanıyor...")
        
        # İçerik Hazırlama
        prompt_text = f"Sen Eren AI'sın. Özel Eren Fen ve Teknoloji Lisesi asistanısın. Mod: {mod}. Soru: {soru}"
        payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
        
        if belge:
            if belge.type.startswith("image/"):
                img_data = base64.b64encode(belge.read()).decode('utf-8')
                payload["contents"][0]["parts"].append({
                    "inline_data": {"mime_type": belge.type, "data": img_data}
                })
            else:
                metin = dosya_oku(belge)
                if metin:
                    payload["contents"][0]["parts"][0]["text"] += f"\n\nBelge İçeriği:\n{metin}"

        # API Çağrısı (REST üzerinden)
        try:
            headers = {'Content-Type': 'application/json'}
            response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
            result = response.json()
            
            if "candidates" in result:
                cevap = result["candidates"][0]["content"]["parts"][0]["text"]
                alan.markdown(cevap)
                st.session_state.messages.append({"role": "assistant", "content": cevap})
            else:
                alan.error(f"API Hatası: {result.get('error', {}).get('message', 'Bilinmeyen hata')}")
        except Exception as e:
            alan.error(f"Bağlantı Hatası: {e}")
