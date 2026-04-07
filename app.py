import streamlit as st
import google.generativeai as genai
import PIL.Image
import os
import requests
from bs4 import BeautifulSoup

# --- 1. GÖRSEL AYARLAR VE SOL MENÜ ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=150)
    
    modul = st.selectbox(
        "Asistan Modu",
        ["Eren AI Asistanı", "Akademik Destek", "Veli Bilgilendirme"],
        label_visibility="collapsed"
    )
    st.divider()
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

# --- 2. API VE MODEL DOĞRULAMA ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Secrets kısmına GOOGLE_API_KEY ekleyin!")
    st.stop()

# Sisteme en uygun modeli otomatik seçer (Hata önleyici)
@st.cache_resource
def get_model_name():
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'gemini-1.5-flash' in m.name: return m.name
        return "gemini-1.5-flash"
    except:
        return "gemini-1.5-flash"

working_model = get_model_name()

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
    except Exception as e:
        return f"Siteye ulaşılamadı: {str(e)}"

# --- 4. ANA EKRAN VE GİRİŞ ---
st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.container(border=True):
    col1, col2 = st.columns([1, 4]) 
    with col1:
        yuklenen_dosya = st.file_uploader("Upload", type=['png', 'jpg', 'jpeg', 'pdf'], label_visibility="collapsed")
    with col2:
        prompt = st.chat_input("Mesajınızı yazın...")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. AKILLI TETİKLEYİCİ VE CEVAP MOTORU ---
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        
        # Akıllı Tetikleyici Kontrolü
        okul_terimleri = ["okul", "eren", "lise", "kolej", "müdür", "personel", "öğretmen", "kadro"]
        site_bilgisi = ""
        
        if any(kelime in prompt.lower() for kelime in okul_terimleri):
            placeholder.markdown("🔍 *Eren Koleji web sitesi inceleniyor...*")
            site_bilgisi = web_sitesini_oku("https://eren.k12.tr/")
        else:
            placeholder.markdown("🛡️ *Eren AI yanıt hazırlıyor...*")

        try:
            model = genai.GenerativeModel(working_model)
            
            sistem_mesaji = f"""
            Sen Özel Eren Fen ve Teknoloji Lisesi'nin resmi AI asistanısın.
            
            CANLI WEB VERİSİ (EĞER VARSA):
            {site_bilgisi if site_bilgisi else "Okul dışı genel bir soru."}
            
            TALİMATLAR:
            1. Sadece okul hakkındaki sorularda yukarıdaki canlı veriyi temel al.
            2. Okul personeli sorulursa canlı verideki güncel isimleri kullan.
            3. Her cevabın sonuna müdür listesi ekleme, sadece sorulursa bilgi ver.
            4. Cevapların kısa, net ve kurumsal bir dille olsun. Mod: {modul}
            """

            icerik = [sistem_mesaji, prompt]
            if yuklenen_dosya and yuklenen_dosya.type.startswith("image/"):
                icerik.append(PIL.Image.open(yuklenen_dosya))

            response = model.generate_content(icerik)
            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            st.error(f"Bağlantı hatası: {str(e)}")
