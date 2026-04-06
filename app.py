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
    st.info(f"Aktif: {modul}")
    st.divider()
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

# --- 2. API BAĞLANTISI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Secrets kısmına GOOGLE_API_KEY ekleyin!")
    st.stop()

# --- 3. ANA EKRAN TASARIMI ---
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

# --- 4. HATAYI BİTİREN "GÜVENLİ" CEVAP MOTORU ---
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("Eren AI yanıt hazırlıyor... 🛡️")
        
        # Okulun gerçek bilgilerini buraya sabitliyoruz (Artık uyduramaz)
        sistem_mesaji = f"""
        Sen Özel Eren Fen ve Teknoloji Lisesi'nin resmi asistanısın.
        GERÇEK BİLGİLER:
        - Okul Müdürü: Mert Kadıoğlu
        - Müdür Yardımcısı: Damla İskender
        - Kurucu: Sadıka Ulusan
        - Web: https://eren.k12.tr
        Mod: {modul}.
        """

        success = False
        # 404 hatasını bitirmek için mevcut tüm model isimlerini sırayla deniyoruz
        for model_name in ['gemini-1.5-flash-latest', 'gemini-1.5-flash', 'models/gemini-1.5-flash']:
            try:
                model = genai.GenerativeModel(model_name)
                
                girdi = [sistem_mesaji, prompt]
                if yuklenen_dosya and yuklenen_dosya.type.startswith("image/"):
                    girdi.append(PIL.Image.open(yuklenen_dosya))

                response = model.generate_content(girdi)
                placeholder.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                success = True
                break # Biri çalışırsa döngüden çık
            except Exception:
                continue # Hata verirse bir sonrakini dene

        if not success:
            st.error("Model bağlantısı kurulamadı. Lütfen API anahtarınızı kontrol edin.")
