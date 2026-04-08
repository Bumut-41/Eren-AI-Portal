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

# API Yapılandırması
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı! Lütfen Secrets kısmını kontrol edin.")
    st.stop()

# --- GELİŞMİŞ DOSYA OKUMA SİSTEMİ ---
def dosya_cozucu(dosya):
    try:
        if dosya.type == "application/pdf":
            return "\n".join([p.extract_text() for p in PdfReader(dosya).pages if p.extract_text()])
        elif dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return "\n".join([p.text for p in Document(dosya).paragraphs])
        elif "presentationml" in dosya.type:
            pptx = Presentation(dosya)
            return "\n".join([shape.text for slide in pptx.slides for shape in slide.shapes if hasattr(shape, "text")])
        elif "spreadsheet" in dosya.type or "csv" in dosya.type:
            df = pd.read_excel(dosya) if "spreadsheet" in dosya.type else pd.read_csv(dosya)
            return f"Veri Özeti:\n{df.head(100).to_string()}"
        return None
    except Exception as e:
        return f"Okuma hatası: {e}"

# --- MODEL SEÇİMİ (Gemini 3 Flash) ---
# Listenizdeki en güncel önizleme sürümünü kullanıyoruz
model = genai.GenerativeModel('gemini-3-flash-preview')

# --- ARAYÜZ ---
with st.sidebar:
    st.title("🛡️ Eren AI")
    st.markdown("### Özel Eren Fen ve Teknoloji Lisesi")
    st.divider()
    mod = st.selectbox("Asistan Modu", ["Genel Asistan", "Döküman Analizi", "Akademik Rehber"])
    st.caption("© 2026 Eren Eğitim Kurumları")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Giriş ve Dosya Yükleme
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        dosya = st.file_uploader("Dosya", type=['pdf','docx','pptx','xlsx','csv','png','jpg','jpeg'], label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya sorunuzu iletin...")

# --- YANIT SÜRECİ ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        cevap_kutusu = st.empty()
        cevap_kutusu.info("🛡️ Eren AI (Gemini 3) dökümanları ve soruyu inceliyor...")
        
        try:
            # Hazırlık
            prompt_parcalari = [f"Sen Eren AI'sın. Mod: {mod}. Profesyonel ve net yanıtlar ver.", soru]
            
            if dosya:
                if dosya.type.startswith("image/"):
                    prompt_parcalari.append(Image.open(dosya))
                else:
                    icerik = dosya_cozucu(dosya)
                    if icerik:
                        prompt_parcalari.append(f"\n[YÜKLENEN BELGE]:\n{icerik}")

            # Üretim
            response = model.generate_content(prompt_parcalari)
            
            if response.text:
                cevap_kutusu.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
        except Exception as e:
            cevap_kutusu.error(f"⚠️ Bir sorun oluştu: {str(e)}")
