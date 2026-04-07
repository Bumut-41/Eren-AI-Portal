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
def hizli_web_tara(url):
    try:
        r = requests.get(url, timeout=3)
        soup = BeautifulSoup(r.text, 'html.parser')
        for s in soup(["script", "style", "nav", "footer"]): s.extract()
        return soup.get_text()[:1500]
    except: return ""

def dosya_oku_hizli(dosya):
    try:
        if dosya.name.lower().endswith('.pdf'):
            reader = PyPDF2.PdfReader(dosya)
            return "".join([p.extract_text() for p in reader.pages[:2]])[:2000]
        elif dosya.name.lower().endswith('.docx'):
            return "\n".join([p.text for p in Document(dosya).paragraphs[:30]])
        elif dosya.name.lower().endswith(('.xlsx', '.xls')):
            return pd.read_excel(dosya).head(10).to_string()
        return ""
    except Exception:
        return "Dosya okuma atlandı."

# --- 2. API VE MODEL (FATURANDIRMA DÜZELDİĞİ İÇİN ARTIK ÇALIŞACAK) ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Lütfen Secrets kısmına GOOGLE_API_KEY ekleyin!")
    st.stop()

MODEL_ID = "gemini-1.5-flash" 

# --- 3. YAN ÇUBUK ---
with st.sidebar:
    st.title("🛡️ Eren AI")
    if os.path.exists("Logo.png"): st.image("Logo.png", width=120)
    mod = st.selectbox("Mod:", ["Eren AI Asistanı", "Akademik Destek", "Veli Bilgilendirme"])
    st.divider()
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

# --- 4. ANA EKRAN ---
st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

c1, c2 = st.columns([1, 5])
with c1:
    yukle = st.file_uploader("Ek", type=['png','jpg','pdf','docx','xlsx'], label_visibility="collapsed")
with c2:
    soru = st.chat_input("Eren AI'ya bir soru sorun...")

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 5. İŞLEME DÖNGÜSÜ ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"): st.markdown(soru)

    with st.chat_message("assistant"):
        durum = st.empty()
        durum.markdown("⚡ *İşleniyor...*")
        
        site_bilgi = ""
        if any(k in soru.lower() for k in ["eren", "okul", "müdür"]):
            site_bilgi = hizli_web_tara("https://eren.k12.tr/")
        
        belge_bilgi = dosya_oku_hizli(yukle) if (yukle and not yukle.type.startswith("image/")) else ""

        try:
            model = genai.GenerativeModel(MODEL_ID)
            kontekst = f"Sen Eren AI'sın. Mod: {mod}. Veriler: {site_bilgi} {belge_bilgi}"
            
            payload = [kontekst, soru]
            if yukle and yukle.type.startswith("image/"):
                payload.append(PIL.Image.open(yukle))

            yanit = model.generate_content(payload)
            durum.markdown(yanit.text)
            st.session_state.messages.append({"role": "assistant", "content": yanit.text})
            
        except Exception as e:
            durum.error("Bağlantı başarılı ancak yanıt üretilemedi. Lütfen tekrar deneyin.")
