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

# --- 1. SAYFA AYARLARI VE SABİT YAN ÇUBUK ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

# Yan çubuğu en başta tanımlıyoruz ki hiçbir hata onu yok edemesin
with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=150)
    
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
            metin = "Excel Tablo Verisi:\n" + df.to_string()
        elif isim.endswith('.pptx'):
            sunum = Presentation(dosya)
            for slayt in sunum.slides:
                for sekil in slayt.shapes:
                    if hasattr(sekil, "text"): metin += sekil.text + "\n"
        return f"\n[Yüklenen Belge İçeriği]:\n{metin}"
    except Exception as e:
        return f"\n[Dosya Okuma Hatası]: {str(e)}"

# --- 3. WEB TARAMA ---
def site_oku(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        for s in soup(["script", "style"]): s.extract()
        return soup.get_text()[:3000]
    except: return ""

# --- 4. API VE MODEL DOĞRULAMA (404 Kesin Çözüm) ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı (GOOGLE_API_KEY) bulunamadı!")
    st.stop()

# 404 hatasını önlemek için doğrudan model ismini kullanıyoruz
WORKING_MODEL = "gemini-1.5-flash"

# --- 5. ANA EKRAN VE SOHBET ---
st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Dosya Yükleme ve Giriş Alanı
with st.container(border=True):
    c1, c2 = st.columns([1, 4])
    with c1:
        yukle = st.file_uploader("Dosya Seç", type=['png','jpg','jpeg','pdf','docx','xlsx','pptx'], label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya bir soru sorun...")

# Sohbet Geçmişi
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 6. YANIT ÜRETİMİ ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"): st.markdown(soru)

    with st.chat_message("assistant"):
        durum = st.empty()
        
        # 1. Okul Bilgisi Gerekli mi? (Tetikleyici)
        site_verisi = ""
        okul_anahtar = ["okul", "eren", "müdür", "lise", "kolej", "personel"]
        if any(kelime in soru.lower() for kelime in okul_anahtar):
            durum.markdown("🔍 *Eren Koleji web sitesi inceleniyor...*")
            site_verisi = site_oku("https://eren.k12.tr/")
        
        # 2. Belge Bilgisi Gerekli mi?
        belge_verisi = ""
        if yukle and not yukle.type.startswith("image/"):
            durum.markdown("📄 *Yüklenen belge okunuyor...*")
            belge_verisi = dosya_cozucu(yukle)
        
        if not site_verisi and not belge_verisi:
            durum.markdown("🛡️ *Eren AI yanıt hazırlıyor...*")
