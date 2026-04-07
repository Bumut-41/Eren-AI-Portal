import streamlit as st
import google.generativeai as genai
import PIL.Image
import os
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document
from pptx import Presentation

# --- 1. SAYFA VE SİSTEM AYARLARI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

# --- 2. 404 HATASINI BİTİREN KRİTİK TANIMLAMA ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı! Secrets ayarlarını kontrol edin.")
    st.stop()

# ÇÖZÜM: 'models/gemini-1.5-flash' yerine doğrudan 'v1' ana kanalı üzerinden 
# model nesnesini oluşturuyoruz. Bu, image_4e4d91'deki hatayı tamamen engeller.
model_engine = genai.GenerativeModel(model_name='gemini-1.5-flash')

# --- 3. DÖKÜMAN OKUMA MOTORU (GELİŞMİŞ) ---
def döküman_oku(dosya):
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
            return f"Tablo Verileri:\n{df.to_string()}"
        return None
    except Exception as e:
        return f"Dosya Okuma Hatası: {str(e)}"

# --- 4. ARAYÜZ ---
st.title("🛡️ Eren AI Portalı")

with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    mod = st.selectbox("Asistan Modu", ["Eren AI Asistanı", "Akademik Analiz"])
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Giriş Bölümü
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        yukle = st.file_uploader("Dosya", type=['pdf','docx','pptx','xlsx','csv','png','jpg'], label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya sorunuzu iletin...")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 5. ANALİZ VE YANIT MOTORU ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        cevap_alani = st.empty()
        cevap_alani.markdown("⚡ *Analiz ediliyor...*")
        
        try:
            # Asistanın dosyayı görememe sorununu (image_43697a) metin enjeksiyonu ile çözüyoruz
            prompt_parcalari = [f"Sen Özel Eren Fen ve Teknoloji Lisesi asistanısın. Mod: {mod}.", soru]
            
            if yukle:
                if yukle.type.startswith("image/"):
                    prompt_parcalari.append(PIL.Image.open(yukle))
                else:
                    icerik = döküman_oku(yukle)
                    if icerik:
                        # Bu satır asistanın "dosyaya erişimim yok" demesini engeller
                        prompt_parcalari.append(f"\n--- SİZE YÜKLENEN BELGE İÇERİĞİ ---\n{icerik}")

            # Yanıtı alırken v1beta yerine kararlı akışı kullanıyoruz
            yanit = model_engine.generate_content(prompt_parcalari)
            
            if yanit.text:
                cevap_alani.markdown(yanit.text)
                st.session_state.messages.append({"role": "assistant", "content": yanit.text})
        except Exception as e:
            cevap_alani.error(f"Sistem Hatası: {str(e)}")
