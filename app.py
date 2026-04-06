import streamlit as st
import google.generativeai as genai
import os

# --- 1. SAYFA VE SOL MENÜ AYARLARI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

# Sol menüyü (Sidebar) oluşturuyoruz
with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=150)
    st.info("Özel Eren Fen ve Teknoloji Lisesi")
    st.divider()
    st.caption("© 2026 Eren AI")

# --- 2. API ANAHTARI BAĞLANTISI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Hata: Streamlit Cloud'da 'Secrets' kısmına GOOGLE_API_KEY eklemelisin!")
    st.stop()

# --- 3. ANA EKRAN VE MESAJLAŞMA ---
st.title("Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Buraya yazın...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # 404 hatasını önlemek için sistemdeki en sağlam modeli buluyoruz
            model_list = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            model_name = "models/gemini-1.5-flash" if "models/gemini-1.5-flash" in model_list else model_list[0]
            
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction="Sen Özel Eren Fen ve Teknoloji Lisesi asistanısın. Okul müdürü Mert Kadıoğlu'dur. Web sitesi: www.eren.k12.tr"
            )
            
            response = model.generate_content(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            st.error(f"Sistem Hatası: {str(e)}")
