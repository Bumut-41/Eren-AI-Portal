import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from PIL import Image
import pdf2image
import pandas as pd
from docx import Document
from pptx import Presentation
import io

# --- SİSTEM AYARLARI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

# API Yapılandırması
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı eksik!")
    st.stop()

# --- MODEL TANIMLAMA (Gemini 3 Flash) ---
# En güncel ve sorunsuz versiyon
model = genai.GenerativeModel('gemini-3-flash-preview')

# --- DOSYA İŞLEME FONKSİYONLARI ---
def metin_ayikla(dosya):
    try:
        if dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return "\n".join([p.text for p in Document(dosya).paragraphs])
        elif "spreadsheet" in dosya.type or "csv" in dosya.type:
            df = pd.read_excel(dosya) if "spreadsheet" in dosya.type else pd.read_csv(dosya)
            return f"Tablo Verileri:\n{df.to_string()}"
        elif "presentationml" in dosya.type:
            prs = Presentation(dosya)
            return "\n".join([shape.text for slide in prs.slides for shape in slide.shapes if hasattr(shape, "text")])
        return None
    except Exception as e:
        return f"Okuma Hatası: {e}"

# --- ARAYÜZ ---
with st.sidebar:
    st.title("🛡️ Eren AI")
    st.markdown("### Özel Eren Fen ve Teknoloji Lisesi")
    st.divider()
    mod = st.selectbox("Asistan Modu", ["Döküman Analizi", "Genel Asistan"])

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Giriş Paneli
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        dosya = st.file_uploader("Dosya", type=['pdf','docx','xlsx','pptx','csv','png','jpg','jpeg'], key="eren_v3_flash", label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya sorunuzu iletin...")

# --- İŞLEME ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        durum = st.status("🛡️ Eren AI analiz ediyor...")
        try:
            # Gemini 3 Flash için içerik listesi
            icerik_listesi = [f"Sen Eren AI'sın. Mod: {mod}. Profesyonel okul asistanısın.", soru]
            
            if dosya:
                if dosya.type.startswith("image/"):
                    icerik_listesi.append(Image.open(dosya))
                elif dosya.type == "application/pdf":
                    reader = PdfReader(dosya)
                    pdf_metni = "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
                    
                    if len(pdf_metni.strip()) > 50:
                        icerik_listesi.append(f"PDF Metni:\n{pdf_metni}")
                    else:
                        # Taranmış PDF'i görsele çevir (image_cd8a45 çözümü)
                        dosya.seek(0)
                        sayfalar = pdf2image.convert_from_bytes(dosya.read())
                        icerik_listesi.extend(sayfalar[:5])
                else:
                    ek_metin = metin_ayikla(dosya)
                    if ek_metin: icerik_listesi.append(ek_metin)

            # Yanıt Üretimi
            response = model.generate_content(icerik_listesi)
            if response.text:
                durum.update(label="✅ Analiz Tamamlandı", state="complete")
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            durum.update(label="❌ Hata", state="error")
            st.error(f"Sistem Hatası: {str(e)}")
