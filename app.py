import streamlit as st
import google.generativeai as genai
import PIL.Image
import os
import requests
from bs4 import BeautifulSoup
import PyPDF2
from docx import Document

# --- 1. AYARLAR ---
st.set_page_config(page_title="Eren AI", page_icon="🛡️", layout="wide")

@st.cache_data(ttl=3600)
def siteyi_tara(url):
    try:
        r = requests.get(url, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for s in soup(["script", "style", "nav", "footer"]): s.extract()
        return soup.get_text()[:1500]
    except: return ""

def belge_oku(dosya):
    try:
        if dosya.name.lower().endswith('.pdf'):
            reader = PyPDF2.PdfReader(dosya)
            return "".join([p.extract_text() for p in reader.pages[:3]])[:3000]
        elif dosya.name.lower().endswith('.docx'):
            return "\n".join([p.text for p in Document(dosya).paragraphs[:50]])
        return ""
    except: return "Belge okunamadı."

# --- 2. API YAPILANDIRMASI (ARTIK AKTİF!) ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Secrets kısmına API anahtarınızı ekleyin!")
    st.stop()

MODEL_ID = "gemini-1.5-flash"

# --- 3. ARAYÜZ ---
with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    if os.path.exists("Logo.png"): st.image("Logo.png", width=120)
    mod = st.selectbox("Mod:", ["Eren AI Asistanı", "Akademik Destek"])
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Dosya ve Soru Girişi
c1, c2 = st.columns([1, 4])
with c1:
    dosya = st.file_uploader("Dosya", type=['png','jpg','pdf','docx'], label_visibility="collapsed")
with c2:
    soru = st.chat_input("Eren AI'ya bir soru sorun...")

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 4. YANIT ÜRETİMİ ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"): st.markdown(soru)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("⚡ *Bağlantı kuruluyor...*")
        
        # Okul verisi ve Belge verisi hazırlığı
        site_verisi = siteyi_tara("https://eren.k12.tr/") if "eren" in soru.lower() else ""
        belge_verisi = belge_oku(dosya) if (dosya and not dosya.type.startswith("image/")) else ""

        try:
            model = genai.GenerativeModel(MODEL_ID)
            baglam = f"Sen Eren AI'sın. Veriler: {site_verisi} {belge_verisi}"
            
            payload = [baglam, soru]
            if dosya and dosya.type.startswith("image/"):
                payload.append(PIL.Image.open(dosya))

            yanit = model.generate_content(payload)
            placeholder.markdown(yanit.text)
            st.session_state.messages.append({"role": "assistant", "content": yanit.text})
            
        except Exception:
            placeholder.error("Bağlantı başarılı ancak yanıt üretilirken bir hata oluştu. Sayfayı yenileyip tekrar deneyin.")
