import streamlit as st
import google.generativeai as genai
import PIL.Image
import os

# --- 1. GÖRSEL AYARLAR VE SOL MENÜ ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=150)
    
    st.subheader("Modül Seçin:")
    modul = st.selectbox(
        "Asistan Modu",
        ["Eren AI Asistanı", "Akademik Destek", "Veli Bilgilendirme"],
        label_visibility="collapsed"
    )
    st.divider()
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

# --- 2. API BAĞLANTISI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Secrets kısmına GOOGLE_API_KEY ekleyin!")
    st.stop()

# --- 3. ANA EKRAN VE GİRİŞ ALANI ---
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

# --- 4. HATAYI ÇÖZEN ÇEKİRDEK KISIM ---
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("Yanıt hazırlanıyor... 🛡️")
        
        try:
            # KRİTİK: 'models/' ön ekini sildim. 404 hatasını bu çözecek.
            model = genai.GenerativeModel('gemini-1.5-flash') 
            
            # Okulun gerçek bilgilerini manuel ekledik (İsim uyduramaz)
            sistem_kurali = f"""
            Sen Özel Eren Fen ve Teknoloji Lisesi'nin resmi asistanısın.
            KESİN BİLGİLER:
            - Okul Müdürü: Mert Kadıoğlu
            - Müdür Yardımcısı: Damla İskender
            - Kurucu: Sadıka Ulusan
            - Web: https://eren.k12.tr
            Bu bilgiler dışında birini sorma, uydurma. Modun: {modul}.
            """

            # Verileri gönder
            icerik = [sistem_kurali, prompt]
            if yuklenen_dosya:
                if yuklenen_dosya.type.startswith("image/"):
                    icerik.append(PIL.Image.open(yuklenen_dosya))

            response = model.generate_content(icerik)
            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            st.error(f"Teknik bir aksaklık: {str(e)}")
