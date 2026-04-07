import streamlit as st
import google.generativeai as genai
import PIL.Image
import os

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

# API Yapılandırması
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Secrets içinde API anahtarı bulunamadı!")
    st.stop()

# --- 2. MODELİ DOĞRUDAN ÇAĞIR (EN SAĞLAM YÖNTEM) ---
def model_getir():
    # Denenecek model isimleri
    modeller = ['gemini-1.5-flash', 'models/gemini-1.5-flash', 'gemini-pro']
    
    for m_ad in modeller:
        try:
            model = genai.GenerativeModel(m_ad)
            # Test amaçlı küçük bir çağrı yap (isteğe bağlı ama güvenli)
            return model
        except:
            continue
    return genai.GenerativeModel('gemini-1.5-flash') # En son ihtimal

model = model_getir()

# --- 3. TASARIM VE YAN ÇUBUK ---
with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=150)
    
    st.divider()
    mod = st.selectbox("Asistan Modu", ["Eren AI Asistanı", "Akademik Destek", "Veli Bilgilendirme"])
    st.divider()
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 4. GİRİŞ ALANLARI ---
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        yukle = st.file_uploader("Dosya", type=['png','jpg','jpeg','pdf','docx'], label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya bir soru sorun...")

# Geçmişi Yazdır
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 5. YANIT MOTORU ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("⚡ *Bağlantı kuruluyor...*")
        
        try:
            # İçerik paketini hazırla
            icerik = [f"Sen Eren AI'sın. Mod: {mod}. Yardımcı bir dille yanıt ver.", soru]
            
            if yukle and yukle.type.startswith("image/"):
                img = PIL.Image.open(yukle)
                icerik.append(img)

            # Yanıtı üret
            yanit = model.generate_content(icerik)
            
            if yanit and yanit.text:
                placeholder.markdown(yanit.text)
                st.session_state.messages.append({"role": "assistant", "content": yanit.text})
            else:
                placeholder.error("Model yanıt döndürmedi. Lütfen tekrar deneyin.")
                
        except Exception as e:
            placeholder.error(f"Sistem Hatası: {str(e)}")
