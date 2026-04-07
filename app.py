import streamlit as st
import google.generativeai as genai
import PIL.Image
import os
import requests
from bs4 import BeautifulSoup
import PyPDF2
from docx import Document
import pandas as pd

# --- 1. HIZ VE SAYFA AYARLARI ---
st.set_page_config(page_title="Eren AI", page_icon="🛡️", layout="wide")

@st.cache_data(ttl=3600) # Okul sitesini 1 saat hafızada tut (Hız kazandırır)
def hizli_site_oku(url):
    try:
        r = requests.get(url, timeout=3)
        soup = BeautifulSoup(r.text, 'html.parser')
        for s in soup(["script", "style", "nav", "footer"]): s.extract()
        return soup.get_text()[:1500]
    except: return ""

def hizli_dosya_oku(dosya):
    try:
        if dosya.name.lower().endswith('.pdf'):
            return PyPDF2.PdfReader(dosya).pages[0].extract_text()[:2000] # Sadece 1. sayfa (Hız için)
        elif dosya.name.lower().endswith('.docx'):
            return "\n".join([p.text for p in Document(dosya).paragraphs[:20]])
        elif dosya.name.lower().endswith(('.xlsx', '.xls')):
            return pd.read_excel(dosya).head(10).to_string()
        return ""
    except: return "Dosya okuma atlandı."

# --- 2. 404 HATASINI BİTİREN MODEL BULUCU ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Secrets kısmına API KEY ekleyin!")
    st.stop()

@st.cache_resource
def get_working_model():
    # Mevcut hesabındaki çalışan model ismini otomatik seçer
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if "gemini-1.5-flash" in m.name: return m.name
        return "models/gemini-1.5-flash"
    except: return "gemini-1.5-flash"

MODEL_NAME = get_working_model()

# --- 3. ARAYÜZ ---
with st.sidebar:
    st.title("🛡️ Eren AI")
    if os.path.exists("Logo.png"): st.image("Logo.png", width=100)
    mod = st.selectbox("Mod", ["Asistan", "Akademik", "Veli"])

st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Giriş Alanları
c1, c2 = st.columns([1, 5])
with c1:
    dosya = st.file_uploader("Ek", type=['png','jpg','pdf','docx','xlsx'], label_visibility="collapsed")
with c2:
    soru = st.chat_input("Sorunuzu buraya yazın...")

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 4. İŞLEME DÖNGÜSÜ ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"): st.markdown(soru)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("⚡ *Yanıt hazırlanıyor...*")
        
        # Sadece okul ile ilgiliyse siteyi oku
        site = hizli_site_oku("https://eren.k12.tr/") if any(k in soru.lower() for k in ["eren", "okul", "müdür"]) else ""
        ek_icerik = hizli_dosya_oku(dosya) if (dosya and not dosya.type.startswith("image/")) else ""

        try:
            model = genai.GenerativeModel(MODEL_NAME)
