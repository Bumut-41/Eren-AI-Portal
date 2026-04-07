import streamlit as st
import google.generativeai as genai
import PIL.Image
import os
import requests
from bs4 import BeautifulSoup
import PyPDF2
from docx import Document

# --- 1. AYARLAR ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

@st.cache_data(ttl=3600)
def web_sitesi_oku(url):
    try:
        r = requests.get(url, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for s in soup(["script", "style", "nav", "footer"]): s.extract()
        return soup.get_text()[:1500]
    except Exception:
        return ""

def belge_oku(dosya):
    try:
        metin = ""
        if dosya.name.lower().endswith('.pdf'):
            pdf = PyPDF2.PdfReader(dosya)
            for sayfa in pdf.pages[:3]:
                metin += sayfa.extract_text()
        elif dosya.name.lower().endswith('.docx'):
            doc = Document(dosya)
            metin = "\n".join([p.text for p in doc.paragraphs[:50]])
        return metin[:3000]
    except Exception:
        return ""

# --- 2. API YAPILANDIRMASI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Secrets içinde GOOGLE_API_KEY bulunamadı!")
    st.stop()

# --- 3. ARAYÜZ ---
with st.sidebar:
    st.title("🛡️ Eren AI")
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=150)
    mod = st.selectbox("Mod", ["Asistan", "Akademik", "Veli"])

st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Giriş Alanı
c1, c2 = st.columns([1, 4])
with c1:
    yukle = st.file_uploader("Dosya", type=['png','jpg','pdf','docx'], label_visibility="collapsed")
with c2:
    soru = st.chat_input("Mesajınızı yazın...")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 4. YANIT MOTORU ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("⚡ *Düşünülüyor...*")
        
        # Veri toplama
        site_v = web_sitesi_oku("https://eren.k12.tr/") if "eren" in soru.lower() else ""
        belge_v = belge_oku(yukle) if (yukle and not yukle.type.startswith("image/")) else ""

        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            komut = f"Sen Eren AI'sın. Mod: {mod}. Veriler: {site_v} {belge_v}"
            
            icerik = [komut, soru]
            if yukle and yukle.type.startswith("image/"):
                icerik.append(PIL.Image.open(yukle))

            yanit = model.generate_content(icerik)
            
            if yanit:
                placeholder.markdown(yanit.text)
                st.session_state.messages.append({"role": "assistant", "content": yanit.text})
        except Exception as e:
            placeholder.error(f"Hata oluştu: {str(e)}")
