import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import pandas as pd
from docx import Document
from pptx import Presentation
from PIL import Image

# --- SİSTEM AYARLARI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

# API Yapılandırması
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı eksik!")
    st.stop()

# --- GELİŞMİŞ METİN AYIKLAYICI ---
def metni_cikar(dosya):
    try:
        if dosya.type == "application/pdf":
            return "\n".join([p.extract_text() for p in PdfReader(dosya).pages if p.extract_text()])
        elif dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return "\n".join([p.text for p in Document(dosya).paragraphs])
        elif "spreadsheet" in dosya.type or "csv" in dosya.type:
            df = pd.read_excel(dosya) if "spreadsheet" in dosya.type else pd.read_csv(dosya)
            return df.to_string()
        return None
    except Exception as e:
        return f"Okuma Hatası: {e}"

# --- MODEL ---
model = genai.GenerativeModel('gemini-3-flash-preview')

# --- ARAYÜZ ---
with st.sidebar:
    st.title("🛡️ Eren AI")
    st.markdown("### Özel Eren Fen ve Teknoloji Lisesi")
    st.divider()
    mod = st.selectbox("Asistan Modu", ["Döküman Analizi", "Genel Asistan"])

# Sohbet Geçmişi
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Giriş Alanı
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        # ANAHTAR DEĞİŞİKLİK: 'key' parametresi eklendi
        belge = st.file_uploader("Dosya", type=['pdf','docx','xlsx','csv','png','jpg'], key="file_input", label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya bir soru sorun...")

# --- İŞLEME VE YANIT ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        cevap_kutusu = st.empty()
        cevap_kutusu.info("🛡️ Eren AI dosyayı ve soruyu analiz ediyor...")
        
        try:
            # 1. DOSYAYI ANLIK OLARAK YAKALA
            belge_metni = ""
            gorsel = None
            
            if belge:
                if belge.type.startswith("image/"):
                    gorsel = Image.open(belge)
                else:
                    belge_metni = metni_cikar(belge)

            # 2. PROMPT'U TEK BİR PAKET HALİNE GETİR
            # Modelin "dosya yok" demesini engelleyen yapı
            talimat = f"Sen Eren AI'sın. Profesyonel okul asistanısın. Mod: {mod}."
            
            if belge_metni:
                # Dosya içeriğini sorunun hemen üzerine 'mühürlüyoruz'
                hazir_soru = f"{talimat}\n\n[SİSTEM: AŞAĞIDAKİ METİN YÜKLENEN DOSYADAN OKUNDU]\n{belge_metni}\n\n[SORU]: {soru}"
            else:
                hazir_soru = f"{talimat}\n\n[SORU]: {soru}"

            # 3. YANIT ÜRET
            if gorsel:
                res = model.generate_content([talimat, soru, gorsel])
            else:
                res = model.generate_content(hazir_soru)
            
            if res.text:
                cevap_kutusu.markdown(res.text)
                st.session_state.messages.append({"role": "assistant", "content": res.text})
            
        except Exception as e:
            cevap_kutusu.error(f"⚠️ Hata oluştu: {str(e)}")
