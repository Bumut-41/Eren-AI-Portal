import streamlit as st
import google.generativeai as genai
import PIL.Image
import os
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document
from pptx import Presentation

# --- 1. SAYFA VE KİMLİK AYARLARI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

# --- 2. KRİTİK: VERSİYON HATASINI BİTİREN KİLİT ---
if "GOOGLE_API_KEY" in st.secrets:
    # Kütüphaneyi doğrudan kararlı (v1) sürümle çalışmaya zorluyoruz.
    # Bu ayar image_4de588'deki beta hatasını tamamen engeller.
    os.environ["GOOGLE_API_VERSION"] = "v1" 
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı! Lütfen Secrets kısmını kontrol edin.")
    st.stop()

# Modeli en kararlı ismiyle tanımlıyoruz
model_engine = genai.GenerativeModel('gemini-1.5-flash')

# --- 3. DÖKÜMAN OKUMA FONKSİYONU ---
def dosya_oku(dosya):
    try:
        if dosya.type == "application/pdf":
            reader = PdfReader(dosya)
            return "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
        elif dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(dosya)
            return "\n".join([p.text for p in doc.paragraphs])
        elif dosya.type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
            prs = Presentation(dosya)
            metin = [shape.text for slide in prs.slides for shape in slide.shapes if hasattr(shape, "text")]
            return "\n".join(metin)
        elif dosya.type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "text/csv"]:
            df = pd.read_excel(dosya) if "spreadsheet" in dosya.type else pd.read_csv(dosya)
            return df.to_string()
        return None
    except Exception as e:
        return f"Dosya okuma hatası: {str(e)}"

# --- 4. ARAYÜZ ---
st.title("🛡️ Eren AI Portalı")

with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    mod = st.selectbox("Asistan Modu", ["Eren AI Asistanı", "Akademik Analiz"])
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Giriş Alanları
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        yukle = st.file_uploader("Belge", type=['pdf','docx','pptx','xlsx','csv','png','jpg'], label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya sorunuzu iletin...")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 5. YANIT ÜRETİMİ ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        alan = st.empty()
        alan.markdown("⚡ *İşleniyor...*")
        
        try:
            # Yapay zekaya döküman içeriğini hazır olarak sunuyoruz
            prompt = [f"Sen Özel Eren Fen ve Teknoloji Lisesi asistanısın. Mod: {mod}.", soru]
            
            if yukle:
                if yukle.type.startswith("image/"):
                    prompt.append(PIL.Image.open(yukle))
                else:
                    metin = dosya_oku(yukle)
                    if metin:
                        prompt.append(f"\nBELGE İÇERİĞİ:\n{metin}")

            yanit = model_engine.generate_content(prompt)
            if yanit.text:
                alan.markdown(yanit.text)
                st.session_state.messages.append({"role": "assistant", "content": yanit.text})
        except Exception as e:
            alan.error(f"Sistem Hatası: {str(e)}")
