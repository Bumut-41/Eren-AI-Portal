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

# API Anahtarı Kontrolü
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı! Lütfen Streamlit Secrets kısmını kontrol edin.")
    st.stop()

# --- DİNAMİK MODEL BAĞLANTISI ---
# Hangi versiyonun açık olduğunu otomatik bulur
@st.cache_resource
def get_working_model():
    model_list = ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro']
    for m_name in model_list:
        try:
            m = genai.GenerativeModel(m_name)
            # Test amaçlı küçük bir çağrı (Hata verirse bir sonrakine geçer)
            return m
        except:
            continue
    return genai.GenerativeModel('gemini-1.5-flash') # Varsayılan

model = get_working_model()

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

# Giriş Bölümü
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        dosya = st.file_uploader("Dosya", type=['pdf','docx','xlsx','pptx','csv','png','jpg','jpeg'], key="final_v_2026", label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya sorunuzu iletin...")

# --- İŞLEME ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        durum = st.status("🛡️ Eren AI dökümanı analiz ediyor...")
        try:
            prompt_list = [f"Sen Eren AI'sın. Mod: {mod}. Profesyonel okul asistanısın.", soru]
            
            if dosya:
                if dosya.type.startswith("image/"):
                    prompt_list.append(Image.open(dosya))
                elif dosya.type == "application/pdf":
                    reader = PdfReader(dosya)
                    metin = "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
                    if len(metin.strip()) > 50:
                        prompt_list.append(f"Döküman İçeriği:\n{metin}")
                    else:
                        # Taranmış PDF çözümü (image_cd8a45)
                        dosya.seek(0)
                        prompt_list.extend(pdf2image.convert_from_bytes(dosya.read())[:5])
                else:
                    icerik = metin_ayikla(dosya)
                    if icerik: prompt_list.append(icerik)

            # Yanıt Üretme
            response = model.generate_content(prompt_list)
            if response:
                durum.update(label="✅ İşlem Tamamlandı", state="complete")
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            durum.update(label="❌ Bağlantı Hatası", state="error")
            st.error(f"Sistem versiyonları arasında geçiş yapılırken bir hata oluştu: {str(e)}")
