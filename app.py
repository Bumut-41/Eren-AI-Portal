import streamlit as st
import google.generativeai as genai
import PIL.Image
import os
import requests
from bs4 import BeautifulSoup
import PyPDF2
from docx import Document
import pandas as pd

# --- 1. AYARLAR VE ÖNBELLEK (HIZ İÇİN KRİTİK) ---
st.set_page_config(page_title="Eren AI", page_icon="🛡️", layout="wide")

# Okul sitesini her seferinde taramamak için önbelleğe alıyoruz
@st.cache_data(ttl=3600)
def hizli_site_oku(url):
    try:
        r = requests.get(url, timeout=3)
        soup = BeautifulSoup(r.text, 'html.parser')
        # Gereksiz kısımları temizle
        for s in soup(["script", "style", "nav", "footer"]): s.extract()
        return soup.get_text()[:1500] # Sadece ilk 1500 karakter (Hız için)
    except: return ""

def hizli_dosya_oku(dosya):
    try:
        if dosya.name.lower().endswith('.pdf'):
            okuyucu = PyPDF2.PdfReader(dosya)
            # Sadece ilk sayfayı oku (İşlem süresini kısaltır)
            return okuyucu.pages[0].extract_text()[:2000]
        elif dosya.name.lower().endswith('.docx'):
            return "\n".join([p.text for p in Document(dosya).paragraphs[:30]])
        elif dosya.name.lower().endswith(('.xlsx', '.xls')):
            return pd.read_excel(dosya).head(15).to_string()
        return ""
    except Exception:
        return "Dosya okuma atlandı."

# --- 2. API VE MODEL DOĞRULAMA (404 ÇÖZÜCÜ) ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Lütfen Streamlit Secrets'a 'GOOGLE_API_KEY' ekleyin!")
    st.stop()

# 404 hatasını önleyen güvenli model seçici
MODEL_ID = "gemini-1.5-flash" 

# --- 3. YAN ÇUBUK VE ARAYÜZ ---
with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=120)
    
    mod = st.selectbox("Mod Seçin:", ["Eren AI Asistanı", "Akademik Destek", "Veli Bilgilendirme"])
    st.divider()
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Giriş ve Dosya Alanı
with st.container():
    c1, c2 = st.columns([1, 5])
    with c1:
        yukle = st.file_uploader("Dosya", type=['png','jpg','pdf','docx','xlsx'], label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya hızlıca sorun...")

# Sohbet Geçmişini Göster
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 4. AKILLI YANIT MOTORU ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"): st.markdown(soru)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("⚡ *Yanıt hazırlanıyor...*")
        
        # Sadece ilgili sorularda web taraması yap (Performans için)
        okul_site_verisi = ""
        if any(k in soru.lower() for k in ["eren", "okul", "müdür", "lise"]):
            okul_site_verisi = hizli_site_oku("https://eren.k12.tr/")
        
        # Belge içeriği
        belge_verisi = hizli_dosya_oku(yukle) if (yukle and not yukle.type.startswith("image/")) else ""

        try:
            model = genai.GenerativeModel(MODEL_ID)
            
            # Sistem talimatı
            context = f"Sen Eren AI'sın. Mod: {mod}. Veriler: {okul_site_verisi} {belge_verisi}"
            
            girdi = [context, soru]
            if yukle and yukle.type.startswith("image/"):
                girdi.append(PIL.Image.open(yukle))

            yanit = model.generate_content(girdi)
            placeholder.markdown(yanit.text)
            st.session_state.messages.append({"role": "assistant", "content": yanit.text})
            
        except Exception as e:
            st.error("Bağlantı sorunu oluştu. Lütfen API anahtarınızı ve model erişiminizi kontrol edin.")
            # st.write(f"Hata Detayı: {e}") # Gerektiğinde hata detayını görmek için açılabilir
