import streamlit as st
import google.generativeai as genai
import PIL.Image
import os

# --- 1. AYARLAR ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

# API Anahtarı
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Secrets içinde API anahtarı bulunamadı!")
    st.stop()

# --- 2. ARAYÜZ ---
with st.sidebar:
    st.title("🛡️ Eren AI")
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=150)
    mod = st.selectbox("Mod", ["Asistan", "Akademik", "Veli"])

st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Giriş Alanı
yukle = st.file_uploader("Dosya Yükle", type=['png','jpg','pdf','docx'])
soru = st.chat_input("Mesajınızı buraya yazın...")

# Geçmişi Göster
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 3. İŞLEME MANTIĞI ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        alan = st.empty()
        alan.markdown("⚡ *İşleniyor...*")

        try:
            # En güvenli model çağırma yöntemi
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            payload = [f"Sen Eren AI'sın. Mod: {mod}", soru]
            
            if yukle and yukle.type.startswith("image/"):
                payload.append(PIL.Image.open(yukle))

            yanit = model.generate_content(payload)
            
            if yanit.text:
                alan.markdown(yanit.text)
                st.session_state.messages.append({"role": "assistant", "content": yanit.text})
            else:
                alan.error("Model boş yanıt döndürdü.")
                
        except Exception as e:
            # Eğer hata verirse alternatif ismi dene
            try:
                model = genai.GenerativeModel('models/gemini-1.5-flash')
                yanit = model.generate_content(payload)
                alan.markdown(yanit.text)
                st.session_state.messages.append({"role": "assistant", "content": yanit.text})
            except Exception as e2:
                alan.error(f"Bağlantı Hatası: {str(e2)}")
