import streamlit as st
import google.generativeai as genai
import PIL.Image
import os
import requests
from bs4 import BeautifulSoup
import PyPDF2
from docx import Document
import pandas as pd
from pptx import Presentation

# --- 1. AYARLAR ---
st.set_page_config(page_title="Eren AI", page_icon="🛡️", layout="wide")

# Önbelleğe alarak hızı artırıyoruz
@st.cache_data(ttl=3600)
def site_oku_hizli(url):
    try:
        r = requests.get(url, timeout=5) # Zaman aşımını 5 saniyeye düşürdük
        soup = BeautifulSoup(r.text, 'html.parser')
        # Sadece ana metin alanlarını alarak hızı artırıyoruz
        for s in soup(["script", "style", "nav", "footer"]): s.extract()
        return soup.get_text()[:2000] # Veri miktarını azalttık
    except: return ""

def dosya_oku_hizli(dosya):
    isim = dosya.name.lower()
    try:
        if isim.endswith('.pdf'):
            okuyucu = PyPDF2.PdfReader(dosya)
            return "\n".join([s.extract_text() for s in okuyucu.pages[:3]]) # İlk 3 sayfa sınırı
        elif isim.endswith('.docx'):
            doc = Document(dosya)
            return "\n".join([p.text for p in doc.paragraphs[:50]]) # İlk 50 paragraf
        elif isim.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(dosya)
            return df.head(20).to_string() # Sadece ilk 20 satır
        return ""
    except: return "Dosya hızlı okunamadı."

# --- 2. API YAPILANDIRMASI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Key eksik!")
    st.stop()

# --- 3. ARAYÜZ ---
with st.sidebar:
    st.title("🛡️ Eren AI")
    if os.path.exists("Logo.png"): st.image("Logo.png", width=120)
    modul = st.selectbox("Mod", ["Eren AI Asistanı", "Akademik", "Veli"])

st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Giriş Bölümü
c1, c2 = st.columns([1, 5])
with c1:
    yukle = st.file_uploader("Dosya", type=['png','jpg','pdf','docx','xlsx','pptx'], label_visibility="collapsed")
with c2:
    soru = st.chat_input("Hızlıca sorun...")

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 4. HIZLI YANIT DÖNGÜSÜ ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"): st.markdown(soru)

    with st.chat_message("assistant"):
        durum = st.empty()
        durum.markdown("⚡ *İşleniyor...*")
        
        site_bilgi = ""
        if any(k in soru.lower() for k in ["okul", "eren", "müdür"]):
            site_bilgi = site_oku_hizli("https://eren.k12.tr/")
        
        dosya_bilgi = ""
        if yukle and not yukle.type.startswith("image/"):
            dosya_bilgi = dosya_oku_hizli(yukle)

        try:
            # Model isminden 'models/' kısmını kesin olarak çıkardık (404 çözümü)
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            prompt_ozet = f"Sistem: {modul}. Veri: {site_bilgi} {dosya_bilgi}"
            
            girdi = [prompt_ozet, soru]
            if yukle and yukle.type.startswith("image/"):
                girdi.append(PIL.Image.open(yukle))

            yanit = model.generate_content(girdi)
            durum.markdown(yanit.text)
            st.session_state.messages.append({"role": "assistant", "content": yanit.text})
            
        except Exception as e:
            st.error(f"Hız Hatası: {e}")
