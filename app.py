import streamlit as st
import google.generativeai as genai
import os
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document
from pptx import Presentation
from PIL import Image

# --- SİSTEM AYARLARI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

# API Anahtarı Yapılandırması
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı!")
    st.stop()

# --- DOSYA ANALİZ MOTORLARI ---
def dosya_icerigini_oku(dosya):
    try:
        if dosya.type == "application/pdf":
            reader = PdfReader(dosya)
            return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        elif dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(dosya)
            return "\n".join([p.text for p in doc.paragraphs])
        elif "presentationml" in dosya.type:
            pptx = Presentation(dosya)
            text = [shape.text for slide in pptx.slides for shape in slide.shapes if hasattr(shape, "text")]
            return "\n".join(text)
        elif "spreadsheet" in dosya.type or "csv" in dosya.type:
            df = pd.read_excel(dosya) if "spreadsheet" in dosya.type else pd.read_csv(dosya)
            return f"Tablo Verisi Özeti:\n{df.head(100).to_string()}" # İlk 100 satır
        return None
    except Exception as e:
        return f"Dosya Okuma Hatası: {str(e)}"

# --- MODEL YAPILANDIRMASI (Yeni Nesil Flash) ---
# Listenizdeki en güncel ve stabil sürümü seçtik: gemini-2.0-flash
model = genai.GenerativeModel('gemini-2.0-flash')

# --- ARAYÜZ TASARIMI ---
with st.sidebar:
    st.title("🛡️ Eren AI")
    st.markdown("### Özel Eren Fen ve Teknoloji Lisesi")
    st.divider()
    mod = st.selectbox("Asistan Modu", ["Eren AI Asistanı", "Akademik Analiz", "Veli Rehberi"])
    st.caption("© 2026 Eren Eğitim Kurumları")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Giriş Alanı
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        belge = st.file_uploader("Dosya", type=['pdf','docx','pptx','xlsx','csv','png','jpg','jpeg'], label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya bir soru sorun...")

# --- İŞLEME ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        alan = st.empty()
        alan.info("🛡️ Eren AI (v2.0 Flash) analiz ediyor...")
        
        try:
            # Sistem Talimatı ve Kullanıcı Sorusu
            icerik_listesi = [f"Sen Eren AI'sın. Mod: {mod}. Profesyonel ve yardımcı ol.", soru]
            
            if belge:
                if belge.type.startswith("image/"):
                    icerik_listesi.append(Image.open(belge))
                else:
                    metin = dosya_icerigini_oku(belge)
                    if metin:
                        icerik_listesi.append(f"\n[DÖKÜMAN İÇERİĞİ]:\n{metin}")

            # Yanıt Üretimi
            yanit = model.generate_content(icerik_listesi)
            
            if yanit.text:
                alan.markdown(yanit.text)
                st.session_state.messages.append({"role": "assistant", "content": yanit.text})
                
        except Exception as e:
            alan.error(f"Erişim Sorunu: {str(e)}")
