import streamlit as st
import google.generativeai as genai
import PIL.Image
import os
import requests
from bs4 import BeautifulSoup
import PyPDF2
from docx import Document
import pandas as pd

# --- 1. AYARLAR VE ÖNBELLEK ---
st.set_page_config(page_title="Eren AI", page_icon="🛡️", layout="wide")

@st.cache_data(ttl=3600)
def hizli_web_oku(url):
    try:
        r = requests.get(url, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for s in soup(["script", "style", "nav", "footer"]): s.extract()
        return soup.get_text()[:2000]
    except: return ""

def dosya_analiz_et(dosya):
    try:
        if dosya.name.lower().endswith('.pdf'):
            pdf = PyPDF2.PdfReader(dosya)
            return "".join([p.extract_text() for p in pdf.pages[:3]])[:3000]
        elif dosya.name.lower().endswith('.docx'):
            doc = Document(dosya)
            return "\n".join([p.text for p in doc.paragraphs[:50]])
        elif dosya.name.lower().endswith(('.xlsx', '.xls')):
            return pd.read_excel(dosya).head(15).to_string()
        return ""
    except: return "Dosya okunamadı."

# --- 2. API YAPILANDIRMASI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Secrets kısmına GOOGLE_API_KEY eklenmemiş!")
    st.stop()

# 404 hatasını önlemek için doğru model tanımlaması
MODEL_ID = "models/gemini-1.5-flash" 

# --- 3. YAN ÇUBUK VE ARAYÜZ ---
with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    if os.path.exists("Logo.png"): st.image("Logo.png", width=120)
    mod = st.selectbox("Mod:", ["Eren AI Asistanı", "Akademik Destek", "Veli Bilgilendirme"])
    st.divider()
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Giriş ve Dosya Alanı
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        yukle = st.file_uploader("Dosya", type=['png','jpg','pdf','docx','xlsx'], label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya bir soru sorun...")

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 4. YANIT MOTORU ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"): st.markdown(soru)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("⚡ *Yanıt hazırlanıyor...*")
        
        # Sadece gerekliyse siteyi tara (Hız için)
        site_veri = ""
        if any(k in soru.lower() for k in ["eren", "okul", "müdür"]):
            site_veri = hizli_web_oku("https://eren.k12.tr/")
        
        belge_veri = dosya_analiz_et(yukle) if (yukle and not yukle.type.startswith("image/")) else ""

        try:
            model = genai.GenerativeModel(MODEL_ID)
            baglam = f"Sen Eren AI'sın. Mod: {mod}. Veriler: {site_veri} {belge_veri}"
            
            girdi = [baglam, soru]
            if yukle and yukle.type.startswith("image/"):
                girdi.append(PIL.Image.open(yukle))

            yanit = model.generate_content(girdi)
            placeholder.markdown(yanit.text)
            st.session_state.messages.append({"role": "assistant", "content": yanit.text})
            
        except Exception as e:
            placeholder.error(f"Bağlantı hatası: Lütfen API anahtarınızı ve kotanızı kontrol edin.")
