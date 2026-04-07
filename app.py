import streamlit as st
import google.generativeai as genai
import PIL.Image
import os

# --- 1. AYARLAR ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️")

# API Anahtarı
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Secrets içinde API anahtarı bulunamadı!")
    st.stop()

# --- 2. MODELİ OTOMATİK BUL (404 HATASINI BİTİREN KISIM) ---
@st.cache_resource
def model_yukle():
    # Sistemde çalışan tüm modelleri listele ve içinden flash olanı seç
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            if 'gemini-1.5-flash' in m.name:
                return genai.GenerativeModel(m.name)
    # Eğer özel isim bulunamazsa en temel olanı döndür
    return genai.GenerativeModel('gemini-pro')

model = model_yukle()

# --- 3. ARAYÜZ ---
st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

yukle = st.file_uploader("Dosya Seç", type=['png', 'jpg', 'jpeg', 'pdf', 'docx'])
soru = st.chat_input("Mesajınızı buraya yazın...")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 4. İŞLEME ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        try:
            payload = [f"Sen Eren AI'sın.", soru]
            if yukle and yukle.type.startswith("image/"):
                payload.append(PIL.Image.open(yukle))
            
            yanit = model.generate_content(payload)
            st.markdown(yanit.text)
            st.session_state.messages.append({"role": "assistant", "content": yanit.text})
            
        except Exception as e:
            st.error(f"Hata detayı: {str(e)}")
