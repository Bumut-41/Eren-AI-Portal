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
import io

# --- 1. SAYFA VE YAN ÇUBUK AYARLARI (Sidebar Sabitlendi) ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

# Yan çubuğu her zaman en başta tanımlıyoruz ki kaybolmasın
with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=150)
    else:
        st.info("Logo.png bulunamadı.")
    
    modul = st.selectbox(
        "Asistan Modu", 
        ["Eren AI Asistanı", "Akademik Destek", "Veli Bilgilendirme"]
    )
    st.divider()
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

# --- 2. DOSYA OKUMA MOTORU ---
def dosya_cozucu(dosya):
    metin = ""
    isim = dosya.name.lower()
    try:
        if isim.endswith('.pdf'):
            okuyucu = PyPDF2.PdfReader(dosya)
            for sayfa in okuyucu.pages: metin += sayfa.extract_text() + "\n"
        elif isim.endswith('.docx'):
            doc = Document(dosya)
            metin = "\n".join([p.text for p in doc.paragraphs])
        elif isim.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(dosya)
            metin = "Tablo Verileri:\n" + df.to_string()
        elif isim.endswith('.pptx'):
            sunum = Presentation(dosya)
            for slayt in sunum.slides:
                for sekil in slayt.shapes:
                    if hasattr(sekil, "text"): metin += sekil.text + "\n"
        return f"\n[Dosya İçeriği: {isim}]\n{metin}"
    except Exception as e:
        return f"\n[Dosya Okuma Hatası]: {str(e)}"

# --- 3. WEB TARAMA ---
def site_oku(url):
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        for s in soup(["script", "style"]): s.extract()
        return soup.get_text()[:3000]
    except: return ""

# --- 4. API VE MODEL DOĞRULAMA (404 Çözücü) ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Lütfen Streamlit Secrets'a GOOGLE_API_KEY ekleyin.")
    st.stop()

# Hata almamak için sistemdeki uygun model ismini buluyoruz
@st.cache_resource
def model_bul():
    return "gemini-1.5-flash" # Genel hata alan 'models/' ekini kaldırdık

# --- 5. ARAYÜZ VE SOHBET ---
st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Giriş Alanı
with st.container(border=True):
    c1, c2 = st.columns([1, 4])
    with c1:
        yukle = st.file_uploader("Dosya Seç", type=['png','jpg','pdf','docx','xlsx','pptx'], label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya sor...")

# Geçmişi Yazdır
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 6. YANIT ÜRETİMİ ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"): st.markdown(soru)

    with st.chat_message("assistant"):
        yukleme_alani = st.empty()
        
        # Bilgi Toplama
        site_bilgi = ""
        if any(x in soru.lower() for x in ["okul", "eren", "müdür"]):
            yukleme_alani.markdown("🔍 *
