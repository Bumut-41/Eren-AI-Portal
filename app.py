import streamlit as st
import google.generativeai as genai
import PIL.Image
import os
import requests
from bs4 import BeautifulSoup
import PyPDF2
from docx import Document
import pandas as pd

# --- 1. SİSTEM AYARLARI VE HIZLANDIRMA ---
st.set_page_config(page_title="Eren AI", page_icon="🛡️", layout="wide")

@st.cache_data(ttl=3600)
def okul_sitesi_oku(url):
    try:
        r = requests.get(url, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for s in soup(["script", "style", "nav", "footer"]): s.extract()
        return soup.get_text()[:2000]
    except: return ""

def belge_icerigini_al(dosya):
    try:
        isim = dosya.name.lower()
        if isim.endswith('.pdf'):
            pdf = PyPDF2.PdfReader(dosya)
            return "".join([p.extract_text() for p in pdf.pages[:3]])[:3000]
        elif isim.endswith('.docx'):
            doc = Document(dosya)
            return "\n".join([p.text for p in doc.paragraphs[:50]])
        elif isim.endswith(('.xlsx', '.xls')):
            return pd.read_excel(dosya).head(15).to_string()
        return ""
    except Exception: return "Dosya okuma hatası."

# --- 2. API VE MODEL YAPILANDIRMASI (404 ÇÖZÜMÜ) ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Lütfen Secrets kısmına GOOGLE_API_KEY ekleyin!")
    st.stop()

# Kararlı model ismi kullanımı
MODEL_ID = "models/gemini-1.5-flash"

# --- 3. ARAYÜZ VE YAN ÇUBUK ---
with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    if os.path.exists("Logo.png"): st.image("Logo.png", width=120)
    mod = st.selectbox("Asistan Modu:", ["Eren AI Asistanı", "Akademik Destek", "Veli Bilgilendirme"])
    st.divider()
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Dosya Yükleme ve Giriş Alanı
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        yuklenen_dosya = st.file_uploader("Ek", type=['png','jpg','pdf','docx','xlsx'], label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya bir soru sorun...")

# Geçmiş Mesajları Görüntüle
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 4. AKILLI İŞLEME DÖNGÜSÜ ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"): st.markdown(soru)

    with st.chat_message("assistant"):
        durum_alani = st.empty()
        durum_alani.markdown("⚡ *Yanıt hazırlanıyor...*")
        
        # Sadece okul ile ilgili sorularda siteyi tara (Hız için)
        site_bilgisi = ""
        if any(k in soru.lower() for k in ["eren", "okul", "müdür", "lider"]):
            site_bilgisi = okul_sitesi_oku("https://eren.k12.tr/")
        
        belge_bilgisi = belge_icerigini_al(yuklenen_dosya) if (yuklenen_dosya and not yuklenen_dosya.type.startswith("image/")) else ""

        try:
            model = genai.GenerativeModel(MODEL_ID)
            baglam = f"Sen Eren AI'sın. Mod: {mod}. Kaynaklar: {site_bilgisi} {belge_bilgisi}"
            
            girdi_listesi = [baglam, soru]
            if yuklenen_dosya and yuklenen_dosya.type.startswith("image/"):
                girdi_listesi.append(PIL.Image.open(yuklenen_dosya))

            yanit = model.generate_content(girdi_listesi)
            durum_alani.markdown(yanit.text)
            st.session_state.messages.append({"role": "assistant", "content": yanit.text})
            
        except Exception as e:
            durum_alani.error("Bağlantı hatası: API anahtarınızı veya kotanızı kontrol edin.")
