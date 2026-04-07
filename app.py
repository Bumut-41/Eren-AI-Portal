import streamlit as st
import google.generativeai as genai
import PIL.Image
import os
import requests
from bs4 import BeautifulSoup
import PyPDF2
from docx import Document
import pandas as pd

# --- 1. AYARLAR VE HIZLI ÖNBELLEK ---
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
        isim = dosya.name.lower()
        if isim.endswith('.pdf'):
            okuyucu = PyPDF2.PdfReader(dosya)
            return okuyucu.pages[0].extract_text()[:2000] # Sadece 1. sayfa (Hız için)
        elif isim.endswith('.docx'):
            return "\n".join([p.text for p in Document(dosya).paragraphs[:30]])
        elif isim.endswith(('.xlsx', '.xls')):
            return pd.read_excel(dosya).head(15).to_string()
        return ""
    except: return "Dosya okuma hatası."

# --- 2. API VE MODEL DOĞRULAMA (404 ÇÖZÜCÜ) ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Lütfen Secrets kısmına GOOGLE_API_KEY ekleyin!")
    st.stop()

@st.cache_resource
def get_safe_model():
    # 404 hatasını önlemek için çalışan model ismini saptar
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if "gemini-1.5-flash" in m.name: return m.name
        return "gemini-1.5-flash"
    except: return "gemini-1.5-flash"

MODEL_ID = get_safe_model()

# --- 3. YAN ÇUBUK ---
with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    if os.path.exists("Logo.png"): st.image("Logo.png", width=120)
    mod = st.selectbox("Mod:", ["Eren AI Asistanı", "Akademik Destek", "Veli Bilgilendirme"])
    st.divider()
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

# --- 4. ANA EKRAN ---
st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.container():
    c1, c2 = st.columns([1, 5])
    with c1:
        yukle = st.file_uploader("Dosya", type=['png','jpg','pdf','docx','xlsx'], label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya hızlıca sorun...")

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 5. İŞLEME VE YANIT ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"): st.markdown(soru)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("⚡ *Yanıt hazırlanıyor...*")
        
        # Sadece gerekliyse web tarama yap
        site_veri = hizli_site_oku("https://eren.k12.tr/") if any(k in soru.lower() for k in ["eren", "okul", "müdür"]) else ""
        ek_veri = hizli_dosya_oku(yukle) if (yukle and not yukle.type.startswith("image/")) else ""

        try:
            model = genai.GenerativeModel(MODEL_ID)
            context = f"Sen Eren AI'sın. Mod: {mod}. Veriler: {site_veri} {ek_veri}"
            
            payload = [context, soru]
            if yukle and yukle.type.startswith("image/"):
                payload.append(PIL.Image.open(yukle))

            yanit = model.generate_content(payload)
            placeholder.markdown(yanit.text)
            st.session_state.messages.append({"role": "assistant", "content": yanit.text})
            
        except Exception:
            placeholder.error("Bağlantı sorunu oluştu. Lütfen API anahtarınızı ve model erişiminizi kontrol edin.")
