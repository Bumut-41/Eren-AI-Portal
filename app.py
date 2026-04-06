import streamlit as st
import google.generativeai as genai
import PIL.Image
import os

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="centered")

# --- 2. API ANAHTARI GÜVENLİK KONTROLÜ (KRİTİK) ---
# Kodun içine anahtar yazsanız bile sızmaması için önce Secrets kontrol edilir.
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    # Burası sadece yerel testler içindir, GitHub'da burayı boş bırakabilirsiniz.
    api_key = "BURAYA_ANAHTAR_YAZMA_SECRETS_KULLAN"

genai.configure(api_key=api_key)

# --- 3. YAN MENÜ ---
with st.sidebar:
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=200)
    st.title("Eren AI Menü")
    st.info("Özel Eren Fen ve Teknoloji Lisesi resmi asistanıdır.")
    st.divider()
    st.caption("© 2026 Eren AI")

# --- 4. ANA EKRAN VE MESAJ GEÇMİŞİ ---
st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. GİRİŞ ALANI ---
with st.container(border=True):
    col1, col2 = st.columns([1, 4]) 
    with col1:
        yuklenen_dosya = st.file_uploader("Dosya", type=['png', 'jpg', 'jpeg', 'pdf', 'txt'], label_visibility="collapsed")
    with col2:
        prompt = st.chat_input("Mesajınızı buraya yazın...")

# --- 6. ANALİZ VE OKUL KİMLİĞİ ---
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("Eren AI analiz ediyor... 🛡️")
        
        try:
            # Model ve Sistem Talimatı (Okul Kimliği)
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            target_model = next((m for m in available_models if "gemini-1.5-flash" in m), available_models[0])
            
            model = genai.GenerativeModel(
                model_name=target_model,
                system_instruction="""
                Sen Özel Eren Fen ve Teknoloji Lisesi'nin resmi yapay zeka asistanısın (Eren AI). 
                Görevin okulun vizyonuna uygun bilimsel ve akademik destek vermektir. 
                Sana 'kimsin' denildiğinde Özel Eren Fen ve Teknoloji Lisesi asistanı olduğunu belirtmelisin.
                """
            )

            # İçerik toplama
            icerik = [prompt]
            if yuklenen_dosya:
                if yuklenen_dosya.type == "application/pdf":
                    icerik.append({"mime
