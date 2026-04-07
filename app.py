import streamlit as st
import google.generativeai as genai
import PIL.Image
import os
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document
from pptx import Presentation

# --- 1. SAYFA YAPILANDIRMASI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

# --- 2. API VE VERSİYON KİLİDİ (404 HATASI ÇÖZÜMÜ) ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı! Lütfen Secrets ayarlarını kontrol edin.")
    st.stop()

# KRİTİK DEĞİŞİKLİK: Modeli doğrudan 'v1' ana yolu üzerinden çağırıyoruz.
# Bu tanımlama, image_4e3f2a'daki beta hatasını pas geçer.
model_engine = genai.GenerativeModel(model_name='models/gemini-1.5-flash')

# --- 3. DÖKÜMAN OKUMA MOTORU ---
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
        return f"Hata: {str(e)}"

# --- 4. ARAYÜZ ---
st.title("🛡️ Eren AI Portalı")

with st.sidebar:
    st.title("🛡️ Eren AI")
    mod = st.selectbox("Mod", ["Eren AI Asistanı", "Akademik Analiz"])
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Giriş Paneli
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        yukle = st.file_uploader("Dosya", type=['pdf','docx','pptx','xlsx','csv','png','jpg'], label_visibility="collapsed")
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
        alan.markdown("⚡ *Döküman analiz ediliyor...*")
        
        try:
            # Yapay zekaya dökümanı 'görebilmesi' için metin olarak ekliyoruz
            prompt = [f"Sen Özel Eren Fen ve Teknoloji Lisesi asistanısın. Mod: {mod}.", soru]
            
            if yukle:
                if yukle.type.startswith("image/"):
                    prompt.append(PIL.Image.open(yukle))
                else:
                    icerik = dosya_oku(yukle)
                    if icerik:
                        prompt.append(f"\nBELGE İÇERİĞİ:\n{icerik}")

            yanit = model_engine.generate_content(prompt)
            if yanit.text:
                alan.markdown(yanit.text)
                st.session_state.messages.append({"role": "assistant", "content": yanit.text})
        except Exception as e:
            alan.error(f"Sistem Hatası: {str(e)}")
