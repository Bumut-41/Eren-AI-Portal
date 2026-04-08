import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import pandas as pd
from docx import Document
from pptx import Presentation
from PIL import Image

# --- SİSTEM AYARLARI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

# API Anahtarı Doğrulama
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı!")
    st.stop()

# --- DOSYA OKUMA MOTORU ---
def dosya_icerigini_al(belge):
    try:
        if belge.type == "application/pdf":
            reader = PdfReader(belge)
            return "\n".join([sayfa.extract_text() for sayfa in reader.pages if sayfa.extract_text()])
        elif belge.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return "\n".join([p.text for p in Document(belge).paragraphs])
        elif "spreadsheet" in belge.type or "csv" in belge.type:
            df = pd.read_excel(belge) if "spreadsheet" in belge.type else pd.read_csv(belge)
            return df.to_string()
        elif "presentationml" in belge.type:
            pptx = Presentation(belge)
            return "\n".join([shape.text for slide in pptx.slides for shape in slide.shapes if hasattr(shape, "text")])
        return None
    except Exception as e:
        return f"HATA: {str(e)}"

# --- MODEL (Gemini 3 Preview) ---
model = genai.GenerativeModel('gemini-3-flash-preview')

# --- ARAYÜZ ---
with st.sidebar:
    st.title("🛡️ Eren AI")
    st.markdown("### Özel Eren Fen ve Teknoloji Lisesi")
    st.divider()
    mod = st.selectbox("Asistan Modu", ["Genel Asistan", "Döküman Analizi"])

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Giriş Bölümü
with st.container():
    col1, col2 = st.columns([1, 4])
    with col1:
        yuklenen_dosya = st.file_uploader("Dosya", type=['pdf','docx','pptx','xlsx','csv','png','jpg','jpeg'], label_visibility="collapsed")
    with col2:
        kullanici_sorusu = st.chat_input("Eren AI'ya sorunuzu iletin...")

# --- ASIL İŞLEM ---
if kullanici_sorusu:
    st.session_state.messages.append({"role": "user", "content": kullanici_sorusu})
    with st.chat_message("user"):
        st.markdown(kullanici_sorusu)

    with st.chat_message("assistant"):
        bildirim = st.empty()
        bildirim.info("🛡️ Eren AI analiz başlatıyor...")
        
        try:
            # 1. Dosyayı Metne Dönüştür
            final_prompt = []
            sistem_mesaji = f"Sen Eren AI'sın. Mod: {mod}. Profesyonel bir okul asistanısın."
            
            if yuklenen_dosya:
                if yuklenen_dosya.type.startswith("image/"):
                    final_prompt.append(sistem_mesaji)
                    final_prompt.append(Image.open(yuklenen_dosya))
                    final_prompt.append(kullanici_sorusu)
                else:
                    metin = dosya_icerigini_al(yuklenen_dosya)
                    if metin:
                        # ÖNEMLİ: Dosya metnini direkt sorunun başına ekliyoruz
                        birlesik_mesaj = f"{sistem_mesaji}\n\n[DÖKÜMAN]:\n{metin}\n\n[SORU]: {kullanici_sorusu}"
                        final_prompt.append(birlesik_mesaj)
                        bildirim.success("✅ Dosya başarıyla okundu!")
                    else:
                        final_prompt.append(f"{sistem_mesaji}\n{kullanici_sorusu}")
            else:
                final_prompt.append(f"{sistem_mesaji}\n{kullanici_sorusu}")

            # 2. Yanıt Al
            yanit = model.generate_content(final_prompt)
            
            if yanit.text:
                bildirim.markdown(yanit.text)
                st.session_state.messages.append({"role": "assistant", "content": yanit.text})
            else:
                bildirim.error("Yanıt oluşturulamadı.")
                
        except Exception as e:
            bildirim.error(f"Sistem Hatası: {str(e)}")
