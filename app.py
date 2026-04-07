import streamlit as st
import google.generativeai as genai
import PIL.Image
import os
import requests
from bs4 import BeautifulSoup
import PyPDF2
from docx import Document
import pandas as pd

# --- 1. AYARLAR VE ÖNBELLEK (PERFORMANS İÇİN) ---
st.set_page_config(page_title="Eren AI", page_icon="🛡️", layout="wide")

@st.cache_data(ttl=3600) # Siteyi 1 saat boyunca hafızada tutar
def hizli_site_tara(url):
    try:
        r = requests.get(url, timeout=3)
        soup = BeautifulSoup(r.text, 'html.parser')
        # Sadece metin içeriğini al, scriptleri temizle
        for s in soup(["script", "style", "nav", "footer"]): s.extract()
        return soup.get_text()[:1500] 
    except: return ""

def hizli_belge_oku(dosya):
    try:
        if dosya.name.lower().endswith('.pdf'):
            reader = PyPDF2.PdfReader(dosya)
            # Sadece ilk 2 sayfayı oku (İşlem yükünü azaltır)
            return "".join([p.extract_text() for p in reader.pages[:2]])[:2000]
        elif dosya.name.lower().endswith('.docx'):
            return "\n".join([p.text for p in Document(dosya).paragraphs[:30]])
        elif dosya.name.lower().endswith(('.xlsx', '.xls')):
            return pd.read_excel(dosya).head(10).to_string()
        return ""
    except Exception:
        return "Belge okuma hatası."

# --- 2. API VE MODEL DOĞRULAMA (404 ÇÖZÜCÜ) ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Lütfen Secrets bölümüne GOOGLE_API_KEY ekleyin!")
    st.stop()

# 404 hatasını önlemek için model ismini doğrudan tanımlıyoruz
MODEL_ID = "gemini-1.5-flash" 

# --- 3. YAN ÇUBUK TASARIMI ---
with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    if os.path.exists("Logo.png"): st.image("Logo.png", width=120)
    mod = st.selectbox("Asistan Modu:", ["Eren AI Asistanı", "Akademik Destek", "Veli Rehberi"])
    st.divider()
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

# --- 4. ANA ARAYÜZ ---
st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Giriş ve Dosya Yükleme
c1, c2 = st.columns([1, 5])
with c1:
    dosya = st.file_uploader("Ek", type=['png','jpg','pdf','docx','xlsx'], label_visibility="collapsed")
with c2:
    soru = st.chat_input("Eren AI'ya bir şey sorun...")

# Geçmişi Göster
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 5. İŞLEME VE YANIT DÖNGÜSÜ ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"): st.markdown(soru)

    with st.chat_message("assistant"):
        durum_alani = st.empty()
        durum_alani.markdown("⚡ *İşleniyor...*")
        
        # Sadece okul ile ilgiliyse siteye git (Hız tasarrufu)
        site_veri = ""
        if any(k in soru.lower() for k in ["eren", "okul", "müdür"]):
            site_veri = hizli_site_tara("https://eren.k12.tr/")
        
        belge_veri = hizli_belge_oku(dosya) if (dosya and not dosya.type.startswith("image/")) else ""

        try:
            model = genai.GenerativeModel(MODEL_ID)
            
            # Bağlamı oluştur
            baglam = f"Sen Eren AI'sın. Mod: {mod}. Veriler: {site_veri} {belge_veri}"
            
            komut = [baglam, soru]
            if dosya and dosya.type.startswith("image/"):
                komut.append(PIL.Image.open(dosya))

            yanit = model.generate_content(komut)
            durum_alani.markdown(yanit.text)
            st.session_state.messages.append({"role": "assistant", "content": yanit.text})
            
        except Exception as e:
            durum_alani.error("Teknik bir aksaklık oluştu, lütfen tekrar deneyin.")
