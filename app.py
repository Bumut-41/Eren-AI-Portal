import streamlit as st
import google.generativeai as genai
from google.generativeai import client
import PIL.Image
import os
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document
from pptx import Presentation

# --- 1. API VERSİYONUNU ÇEKİRDEKTEN KİLİTLEME ---
# v1beta hatasını önlemek için SDK'yı v1 kullanmaya zorlarız
client._API_VERSION = "v1"
os.environ["GOOGLE_API_VERSION"] = "v1"

st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı!")
    st.stop()

# --- 2. GELİŞMİŞ DOSYA OKUMA SİSTEMİ ---
def dosya_cozucu(dosya):
    try:
        if dosya.type == "application/pdf":
            r = PdfReader(dosya)
            return "\n".join([p.extract_text() for p in r.pages if p.extract_text()])
        elif dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            d = Document(dosya)
            return "\n".join([p.text for p in d.paragraphs])
        elif "presentationml" in dosya.type:
            p = Presentation(dosya)
            return "\n".join([shape.text for slide in p.slides for shape in slide.shapes if hasattr(shape, "text")])
        elif "spreadsheet" in dosya.type or "csv" in dosya.type:
            df = pd.read_excel(dosya) if "spreadsheet" in dosya.type else pd.read_csv(dosya)
            return f"Tablo Verisi:\n{df.to_string()}"
        return None
    except Exception as e:
        return f"Okuma Hatası: {e}"

# --- 3. MODEL TANIMI (HATA ÖNLEYİCİ YOL) ---
# Sürüm çakışmasını önlemek için tam model yolunu kullanıyoruz
model = genai.GenerativeModel('models/gemini-1.5-flash')

# --- 4. ARAYÜZ ---
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
        belge = st.file_uploader("Dosya", type=['pdf','docx','pptx','xlsx','csv','png','jpg'], label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya sorunuzu iletin...")

# --- 5. İŞLEME ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        alan = st.empty()
        alan.info("🛡️ Eren AI v1 kanalı üzerinden analiz ediyor...")
        
        try:
            icerik = [f"Sen Eren AI'sın. Mod: {mod}.", soru]
            if belge:
                if belge.type.startswith("image/"):
                    icerik.append(PIL.Image.open(belge))
                else:
                    metin = dosya_cozucu(belge)
                    if metin:
                        icerik.append(f"\n[DÖKÜMAN İÇERİĞİ]:\n{metin}")

            yanit = model.generate_content(icerik)
            if yanit.text:
                alan.markdown(yanit.text)
                st.session_state.messages.append({"role": "assistant", "content": yanit.text})
        except Exception as e:
            alan.error(f"Erişim Hatası: {str(e)}")
