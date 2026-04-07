import streamlit as st
import google.generativeai as genai
import PIL.Image
import os
import requests
from bs4 import BeautifulSoup
import PyPDF2
from docx import Document

# --- 1. SAYFA VE HIZ AYARLARI ---
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

def belge_cozucu(dosya):
    try:
        metin = ""
        if dosya.name.lower().endswith('.pdf'):
            pdf = PyPDF2.PdfReader(dosya)
            for sayfa in pdf.pages[:3]: # Hız için ilk 3 sayfa
                metin += sayfa.extract_text()
        elif dosya.name.lower().endswith('.docx'):
            doc = Document(dosya)
            metin = "\n".join([p.text for p in doc.paragraphs[:50]])
        return metin[:3000]
    except Exception:
        return "Belge okunamadı."

# --- 2. API YAPILANDIRMASI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("HATA: Streamlit Secrets içinde GOOGLE_API_KEY bulunamadı!")
    st.stop()

# En kararlı model ismi
MODEL_ID = "gemini-1.5-flash"

# --- 3. YAN ÇUBUK (SIDEBAR) ---
with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=150)
    
    secilen_mod = st.selectbox(
        "Asistan Modu", 
        ["Eren AI Asistanı", "Akademik Destek", "Veli Bilgilendirme"]
    )
    st.divider()
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

# --- 4. ANA ARAYÜZ VE SOHBET GEÇMİŞİ ---
st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Giriş Alanları
with st.container(border=True):
    col1, col2 = st.columns([1, 4])
    with col1:
        yukleme = st.file_uploader("Dosya", type=['png','jpg','pdf','docx'], label_visibility="collapsed")
    with col2:
        kullanici_sorusu = st.chat_input("Eren AI'ya bir soru sorun...")

# Sohbeti Ekrana Bas
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 5. YANIT ÜRETİM MANTIĞI ---
if kullanici_sorusu:
    # Kullanıcı mesajını ekle
    st.session_state.messages.append({"role": "user", "content": kullanici_sorusu})
    with st.chat_message("user"):
        st.markdown(kullanici_sorusu)

    with st.chat_message("assistant"):
        cevap_alani = st.empty()
        cevap_alani.markdown("⚡ *Bağlantı kuruluyor...*")
        
        # Ek veri toplama
        site_bilgisi = ""
        if "eren" in kullanici_sorusu.lower() or "okul" in kullanici_sorusu.lower():
            site_bilgisi = web_sitesi_oku("https://eren.k12.tr/")
        
        belge_bilgisi = ""
        if yukleme and not yukleme.type.startswith("image/"):
            belge_bilgisi = belge_cozucu(yukleme)

        # AI Yanıtı
        try:
            model = genai.GenerativeModel(MODEL_ID)
            
            sistem_komutu = f"Sen Eren AI'sın. Mod: {secilen_mod}. Web Verisi: {site_bilgisi}. Belge Verisi: {belge_bilgisi}"
            
            icerik_paketi = [sistem_komutu, kullanici_sorusu]
            
            if yukleme and yukleme.type.startswith("image/"):
                icerik_paketi.append(PIL.Image.open(yukleme))

            yanit = model.generate_content(icerik_paketi)
            
            if yanit.text:
                cevap_alani.markdown(yanit.text)
                st.session_state.messages.append({"role": "assistant", "content": yanit.text})
            else:
                cevap_alani.error("AI boş yanıt döndürdü, lütfen soruyu tekrar iletin.")
                
        except Exception as e:
            cevap_alani.error(f"Sistem Hatası: API erişimi sağlanamadı. Detay: {str(e)}")
