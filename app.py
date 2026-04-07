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
        for s in soup(["script", "style", "nav", "footer"]): s.extract()
        return soup.get_text()[:1500]
    except: return ""

def hizli_dosya_oku(dosya):
    try:
        if dosya.name.lower().endswith('.pdf'):
            # Sadece ilk 2 sayfayı oku (Hız kazandırır)
            okuyucu = PyPDF2.PdfReader(dosya)
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

@st.cache_resource
def get_model_safe():
    # 404 hatasını önlemek için çalışan modeli bulur
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if "gemini-1.5-flash" in m.name: return m.name
        return "gemini-1.5-flash"
    except: return "gemini-1.5-flash"

MODEL_ID = get_model_safe()

# --- 3. ARAYÜZ ---
with st.sidebar:
    st.title("🛡️ Eren AI")
    if os.path.exists("Logo.png"): st.image("Logo.png", width=100)
    mod = st.selectbox("Mod Seçin:", ["Eren AI Asistanı", "Akademik Destek", "Veli Bilgilendirme"])
    st.divider()
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Giriş Alanı
c1, c2 = st.columns([1, 4])
with c1:
    yukle = st.file_uploader("Dosya", type=['png','jpg','pdf','docx','xlsx'], label_visibility="collapsed")
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
        
        # Gereksiz taramaları önle
        site_veri = ""
        if any(k in soru.lower() for k in ["eren", "okul", "müdür", "lise"]):
            site_veri = hizli_site_oku("https://eren.k12.tr/")
        
        belge_veri = hizli_dosya_oku(yukle) if (yukle and not yukle.type.startswith("image/")) else ""

        try:
            model = genai.GenerativeModel(MODEL_ID)
            
            # Sistem talimatını optimize et
            talimat = f"Sen Eren AI'sın. Mod: {mod}. Veri: {site_veri} {belge_veri}"
            
            payload = [talimat, soru]
            if yukle and yukle.type.startswith("image/"):
                payload.append(PIL.Image.open(yukle))

            yanit = model.generate_content(payload)
            durum.markdown(yanit.text)
            st.session_state.messages.append({"role": "assistant", "content": yanit.text})
            
        except Exception as e:
            st.error(f"Teknik bir sorun oluştu. Lütfen tekrar deneyin.")
            # Geliştirici için hata detayı (Opsiyonel)
            # st.write(f"Detay: {e}")
