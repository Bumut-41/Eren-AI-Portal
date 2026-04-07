import streamlit as st
import google.generativeai as genai
import PIL.Image
import os
import requests
from bs4 import BeautifulSoup
import PyPDF2
from docx import Document
import pandas as pd

# --- 1. AYARLAR VE ÖNBELLEK (HIZ İÇİN) ---
st.set_page_config(page_title="Eren AI", page_icon="🛡️", layout="wide")

@st.cache_data(ttl=3600)
def hizli_site_oku(url):
    try:
        r = requests.get(url, timeout=3)
        soup = BeautifulSoup(r.text, 'html.parser')
        # Gereksiz kodları temizleyerek hızı artırıyoruz
        for s in soup(["script", "style", "nav", "footer"]): s.extract()
        return soup.get_text()[:1500] 
    except: return ""

def hizli_dosya_oku(dosya):
    try:
        if dosya.name.lower().endswith('.pdf'):
            okuyucu = PyPDF2.PdfReader(dosya)
            # Sadece ilk 2 sayfayı oku (İşlem yükünü azaltır)
            metin = ""
            for i in range(min(2, len(okuyucu.pages))):
                metin += okuyucu.pages[i].extract_text()
            return metin[:2000]
        elif dosya.name.lower().endswith('.docx'):
            return "\n".join([p.text for p in Document(dosya).paragraphs[:30]])
        elif dosya.name.lower().endswith(('.xlsx', '.xls')):
            return pd.read_excel(dosya).head(10).to_string()
        return ""
    except: return "Dosya okuma atlandı."

# --- 2. API VE MODEL DOĞRULAMA (404 ÇÖZÜCÜ) ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Key eksik!")
    st.stop()

# 404 hatasını önlemek için doğrudan kararlı model ismi kullanımı
MODEL_ID = "gemini-1.5-flash"

# --- 3. ARAYÜZ VE YAN ÇUBUK ---
with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    if os.path.exists("Logo.png"): st.image("Logo.png", width=120)
    mod = st.selectbox("Mod Seçin:", ["Eren AI Asistanı", "Akademik Destek", "Veli Bilgilendirme"])
    st.divider()
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Giriş Bölümü
c1, c2 = st.columns([1, 4])
with c1:
    yukle = st.file_uploader("Ek", type=['png','jpg','pdf','docx','xlsx'], label_visibility="collapsed")
with c2:
    soru = st.chat_input("Eren AI'ya hızlıca sorun...")

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 4. AKILLI İŞLEME DÖNGÜSÜ ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"): st.markdown(soru)

    with st.chat_message("assistant"):
        durum = st.empty()
        durum.markdown("⚡ *İşleniyor...*")
        
        # Gereksiz taramaları önlemek için sadece ilgili sorularda siteye bakıyoruz
        site_veri = ""
        if any(k in soru.lower() for k in ["eren", "okul", "müdür", "lise"]):
            site_veri = hizli_site_oku("https://eren.k12.tr/")
        
        belge_veri = hizli_dosya_oku(yukle) if (yukle and not yukle.type.startswith("image/")) else ""

        try:
            model = genai.GenerativeModel(MODEL_ID)
            
            # Bağlam ve talimatlar
            talimat = f"Sen Eren AI'sın. Mod: {mod}. Veri: {site_veri} {belge_veri}"
            
            payload = [talimat, soru]
            if yukle and yukle.type.startswith("image/"):
                payload.append(PIL.Image.open(yukle))

            yanit = model.generate_content(payload)
            durum.markdown(yanit.text)
            st.session_state.messages.append({"role": "assistant", "content": yanit.text})
            
        except Exception:
            durum.error("Bağlantı sorunu oluştu. Lütfen API anahtarınızı kontrol edin.")
