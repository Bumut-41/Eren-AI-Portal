import streamlit as st
import google.generativeai as genai
import PIL.Image
import os
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document
from pptx import Presentation

# --- 1. KURUMSAL KİMLİK VE AYARLAR ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

EREN_AI_KIMLIK = """
Merhaba! Ben **Eren AI**, Özel Eren Fen ve Teknoloji Lisesi için geliştirilmiş resmi yapay zeka asistanıyım. 
Akademik dökümanlarınızı (PDF, Word, Excel, PowerPoint) analiz edebilir ve sorularınızı yanıtlayabilirim.
"""

# --- 2. API VE MODEL YAPILANDIRMASI (404 ÇÖZÜMÜ) ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı! Secrets ayarlarını kontrol edin.")
    st.stop()

@st.cache_resource
def model_yukle():
    try:
        # En kararlı sürümü kullanarak 404 hatasını engeller
        return genai.GenerativeModel('gemini-1.5-flash')
    except:
        return genai.GenerativeModel('gemini-pro')

model_engine = model_yukle()

# --- 3. GELİŞMİŞ DOSYA OKUMA MOTORU ---
def dosya_icerigini_getir(dosya):
    try:
        if dosya.type == "application/pdf":
            reader = PdfReader(dosya)
            return "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
        
        elif dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(dosya)
            return "\n".join([p.text for p in doc.paragraphs])
        
        elif dosya.type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
            prs = Presentation(dosya)
            metin = []
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        metin.append(shape.text)
            return "\n".join(metin)
        
        elif dosya.type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "text/csv"]:
            df = pd.read_excel(dosya) if "spreadsheet" in dosya.type else pd.read_csv(dosya)
            return df.to_string()
            
        return None
    except Exception as e:
        return f"Okuma Hatası: {str(e)}"

# --- 4. ARAYÜZ TASARIMI ---
with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=150)
    st.divider()
    mod = st.selectbox("Asistan Modu", ["Eren AI Asistanı", "Akademik Analiz", "Veri İnceleme"])
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Dosya Yükleme Paneli
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        yukle = st.file_uploader("Belge", type=['pdf','docx','pptx','xlsx','csv','png','jpg'], label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya sorunuzu iletin...")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 5. AKILLI YANIT VE ANALİZ ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        alan = st.empty()
        
        if any(k in soru.lower() for k in ["kimsin", "adın ne"]):
            alan.markdown(EREN_AI_KIMLIK)
            st.session_state.messages.append({"role": "assistant", "content": EREN_AI_KIMLIK})
        else:
            alan.markdown("⚡ *Döküman analiz ediliyor...*")
            try:
                baglam = f"Sen Özel Eren Fen ve Teknoloji Lisesi uzman asistanısın. Mod: {mod}."
                prompt_list = [baglam, soru]
                
                # Dosya içeriğini modele enjekte et
                if yukle:
                    if yukle.type.startswith("image/"):
                        prompt_list.append(PIL.Image.open(yukle))
                    else:
                        icerik = dosya_icerigini_getir(yukle)
                        if icerik:
                            prompt_list.append(f"\n--- ANALİZ EDİLEN DOSYA İÇERİĞİ ---\n{icerik}")

                yanit = model_engine.generate_content(prompt_list)
                if yanit.text:
                    alan.markdown(yanit.text)
                    st.session_state.messages.append({"role": "assistant", "content": yanit.text})
            except Exception as e:
                alan.error(f"Sistem Hatası: {str(e)}")
