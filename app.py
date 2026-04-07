import streamlit as st
import google.generativeai as genai
import PIL.Image
import os
import requests
from bs4 import BeautifulSoup
import PyPDF2
from docx import Document
import pandas as pd

# --- 1. SİSTEM AYARLARI ---
st.set_page_config(page_title="Eren AI", page_icon="🛡️", layout="wide")

@st.cache_data(ttl=3600)
def web_sitesi_oku(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        # Sadece ana içeriği alarak hızı artırıyoruz
        for s in soup(["script", "style", "nav", "footer"]): s.extract()
        return soup.get_text()[:2000]
    except: return ""

def dosya_icerigini_getir(yuklenen_dosya):
    try:
        isim = yuklenen_dosya.name.lower()
        if isim.endswith('.pdf'):
            pdf = PyPDF2.PdfReader(yuklenen_dosya)
            return "".join([p.extract_text() for p in pdf.pages[:3]])[:3000]
        elif isim.endswith('.docx'):
            doc = Document(yuklenen_dosya)
            return "\n".join([p.text for p in doc.paragraphs[:50]])
        elif isim.endswith(('.xlsx', '.xls')):
            return pd.read_excel(yuklenen_dosya).head(20).to_string()
        return ""
    except Exception: return "Dosya okunamadı."

# --- 2. API VE MODEL YAPILANDIRMASI (404 ÇÖZÜMÜ) ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Lütfen Secrets kısmına GOOGLE_API_KEY ekleyin!")
    st.stop()

# Kararlı model ismi (404 hatalarını önlemek için)
MODEL_ID = "gemini-1.5-flash"

# --- 3. ARAYÜZ TASARIMI ---
with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    if os.path.exists("Logo.png"): st.image("Logo.png", width=120)
    mod = st.selectbox("Mod:", ["Eren AI Asistanı", "Akademik Destek", "Veli Bilgilendirme"])
    st.divider()
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Giriş Alanı
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        dosya = st.file_uploader("Dosya", type=['png','jpg','pdf','docx','xlsx'], label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya bir soru sorun...")

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 4. AKILLI YANIT DÖNGÜSÜ ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"): st.markdown(soru)

    with st.chat_message("assistant"):
        durum = st.empty()
        durum.markdown("⚡ *Düşünülüyor...*")
        
        # Sadece gerekliyse web tarama yap (Performans odaklı)
        okul_verisi = ""
        if any(anahtar in soru.lower() for anahtar in ["eren", "okul", "müdür", "lider"]):
            okul_verisi = web_sitesi_oku("https://eren.k12.tr/")
        
        ek_bilgi = dosya_icerigini_getir(dosya) if (dosya and not dosya.type.startswith("image/")) else ""

        try:
            model = genai.GenerativeModel(MODEL_ID)
            kontekst = f"Sen Eren AI'sın. Mod: {mod}. Kaynaklar: {okul_verisi} {ek_bilgi}"
            
            payload = [kontekst, soru]
            if dosya and dosya.type.startswith("image/"):
                payload.append(PIL.Image.open(dosya))

            yanit = model.generate_content(payload)
            durum.markdown(yanit.text)
            st.session_state.messages.append({"role": "assistant", "content": yanit.text})
            
        except Exception as e:
            durum.error("Bağlantı hatası: Model erişimi veya API kotası kontrol edilmeli.")
