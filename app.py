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

# --- 1. AYARLAR ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

# --- 2. DOSYA OKUMA FONKSİYONLARI (YENİ!) ---
def dosya_icerigini_oku(yuklenen_dosya):
    icerik_metni = ""
    dosya_adi = yuklenen_dosya.name.lower()
    
    try:
        if dosya_adi.endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(yuklenen_dosya)
            for page in pdf_reader.pages:
                icerik_metni += page.extract_text() + "\n"
        
        elif dosya_adi.endswith('.docx'):
            doc = Document(yuklenen_dosya)
            icerik_metni = "\n".join([para.text for para in doc.paragraphs])
            
        elif dosya_adi.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(yuklenen_dosya)
            icerik_metni = "Excel Tablo Verisi:\n" + df.to_string()
            
        elif dosya_adi.endswith('.pptx'):
            prs = Presentation(yuklenen_dosya)
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        icerik_metni += shape.text + "\n"
        
        return f"\n--- Yüklenen Dosya ({dosya_adi}) İçeriği ---\n{icerik_metni}"
    except Exception as e:
        return f"\nDosya okunurken hata oluştu: {str(e)}"

# --- 3. WEB TARAMA FONKSİYONU ---
def web_sitesini_oku(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style"]): script.extract()
        metin = soup.get_text()
        return "\n".join([l.strip() for l in metin.splitlines() if l.strip()])[:4000]
    except: return ""

# --- 4. API VE MODEL ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı eksik!")
    st.stop()

@st.cache_resource
def get_model():
    return "gemini-1.5-flash" # Veya senin çalışan model ismin

# --- 5. ARAYÜZ ---
st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.container(border=True):
    col1, col2 = st.columns([1, 4]) 
    with col1:
        yuklenen_dosya = st.file_uploader("Dosya", type=['png', 'jpg', 'pdf', 'docx', 'xlsx', 'pptx'], label_visibility="collapsed")
    with col2:
        prompt = st.chat_input("Eren AI'ya bir soru sorun...")

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 6. İŞLEME ---
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        
        # Web ve Dosya Bilgisi Toplama
        site_bilgisi = ""
        if any(k in prompt.lower() for k in ["okul", "eren", "müdür"]):
            placeholder.markdown("🔍 *Okul sitesine bakılıyor...*")
            site_bilgisi = web_sitesini_oku("https://eren.k12.tr/")
        
        dosya_verisi = ""
        if yuklenen_dosya:
            placeholder.markdown("📄 *Dosya içeriği analiz ediliyor...*")
            if not yuklenen_dosya.type.startswith("image/"):
                dosya_verisi = dosya_icerigini_oku(yuklenen_dosya)

        try:
            model = genai.GenerativeModel(get_model())
            sistem_talimati = f"Sen Eren AI'sın. SİTE: {site_bilgisi} DOSYA: {dosya_verisi}"
            
            icerik = [sistem_talimati, prompt]
            if yuklenen_dosya and yuklenen_dosya.type.startswith("image/"):
                icerik.append(PIL.Image.open(yuklenen_dosya))

            response = model.generate_content(icerik)
            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Hata: {e}")
