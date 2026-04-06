import streamlit as st
import google.generativeai as genai
import PIL.Image
import os

# --- 1. SAYFA VE SOL MENÜ AYARLARI ---
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
    st.info(f"Aktif Mod: {modul}")
    st.divider()
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

# --- 2. API VE ARAÇ (TOOL) AYARLARI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Secrets kısmına GOOGLE_API_KEY ekleyin!")
    st.stop()

# --- 3. ANA EKRAN ---
st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Dosya yükleme ve giriş alanı
with st.container(border=True):
    col1, col2 = st.columns([1, 4]) 
    with col1:
        yuklenen_dosya = st.file_uploader("Upload", type=['png', 'jpg', 'jpeg', 'pdf'], label_visibility="collapsed")
    with col2:
        prompt = st.chat_input("Mesajınızı yazın veya dosya ekleyin...")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. CANLI WEB ANALİZİ VE CEVAP ÜRETME ---
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("Eren AI web sitesini analiz ediyor... 🌐")
        
        try:
            # Web arama özelliğini modele 'tools' olarak ekliyoruz
            model = genai.GenerativeModel(
                model_name='models/gemini-1.5-flash',
                tools=[{'google_search_retrieval': {}}], # Web tarama yeteneği açıldı
                system_instruction=f"""
                Sen Özel Eren Fen ve Teknoloji Lisesi asistanısın. 
                KURAL 1: Okulla ilgili bir soru geldiğinde MUTLAKA https://eren.k12.tr sitesini tara.
                KURAL 2: Asla isim veya tarih uydurma. Sitede yoksa 'bilmiyorum' de ve link ver.
                Müdür: Mert Kadıoğlu, Müdür Yardımcısı: Damla İskender (Bilgileri siteden teyit et).
                """
            )

            # İçerik hazırlama
            icerik = [prompt]
            if yuklenen_dosya:
                if yuklenen_dosya.type.startswith("image/"):
                    icerik.append(PIL.Image.open(yuklenen_dosya))
                elif yuklenen_dosya.type == "application/pdf":
                    icerik.append({"mime_type": "application/pdf", "data": yuklenen_dosya.read()})

            # Cevap üretme (Arama yaparak)
            response = model.generate_content(icerik)
            
            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant",
