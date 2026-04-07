import streamlit as st
import google.generativeai as genai
import PIL.Image
import os
import requests
from bs4 import BeautifulSoup

# --- 1. AYARLAR VE SOL MENÜ ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=150)
    modul = st.selectbox("Asistan Modu", ["Eren AI Asistanı", "Akademik Destek", "Veli Bilgilendirme"])
    st.divider()
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

# --- 2. API VE GÜVENLİ MODEL SEÇİMİ (404 ÇÖZÜCÜ) ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Secrets kısmına GOOGLE_API_KEY ekleyin!")
    st.stop()

# Sistemin kabul edeceği doğru model ismini bulan fonksiyon
@st.cache_resource
def get_safe_model():
    try:
        # Mevcut modelleri listele ve en uygun olanı seç
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for m in models:
            if "gemini-1.5-flash" in m: return m
            if "gemini-pro" in m: return m
        return "gemini-1.5-flash" # Varsayılan
    except:
        return "gemini-1.5-flash"

working_model_name = get_safe_model()

# --- 3. CANLI WEB TARAMA FONKSİYONU ---
def web_sitesini_oku(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style"]):
            script.extract()
        metin = soup.get_text()
        lines = (line.strip() for line in metin.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        return "\n".join(chunk for chunk in chunks if chunk)[:4000]
    except Exception:
        return ""

# --- 4. ANA EKRAN ---
st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.container(border=True):
    col1, col2 = st.columns([1, 4]) 
    with col1:
        yuklenen_dosya = st.file_uploader("Upload", type=['png', 'jpg', 'jpeg', 'pdf'], label_visibility="collapsed")
    with col2:
        prompt = st.chat_input("Eren AI'ya bir soru sorun...")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. AKILLI CEVAP MOTORU ---
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        
        # Akıllı Tetikleyici
        okul_terimleri = ["okul", "eren", "lise", "kolej", "müdür", "personel", "öğretmen", "kadro", "kimdir"]
        site_bilgisi = ""
        
        if any(kelime in prompt.lower() for kelime in okul_terimleri):
            placeholder.markdown("🔍 *Web sitesinden güncel bilgiler doğrulanıyor...*")
            site_bilgisi = web_sitesini_oku("https://eren.k12.tr/")
        else:
            placeholder.markdown("🛡️ *Eren AI yanıt hazırlıyor...*")

        try:
            # Doğrulanmış modeli başlat
            model = genai.GenerativeModel(working_model_name)
            
            sistem_mesaji = f"""
            Sen Özel Eren Fen ve Teknoloji Lisesi asistanısın. 
            WEB VERİSİ: {site_bilgisi if site_bilgisi else "Genel bilgi."}
            
            ÖNEMLİ: Okul kadrosu sorulursa web verisindeki isimleri kullan. 
            Cevapların kısa ve kurumsal olsun. Mod: {modul}
            """

            icerik = [sistem_mesaji, prompt]
            if yuklenen_dosya and yuklenen_dosya.type.startswith("image/"):
                icerik.append(PIL.Image.open(yuklenen_dosya))

            response = model.generate_content(icerik)
            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            st.error(f"Sistem Hatası: {str(e)}")
            st.info(f"Denenen Model: {working_model_name}")
