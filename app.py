import streamlit as st
import google.generativeai as genai
import PIL.Image
import os

# --- 1. SAYFA VE SOL MENÜ AYARLARI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

# Sol Menü (Sidebar) - Senin Olmazsa Olmazın
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

# --- 2. API ANAHTARI BAĞLANTISI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Hata: Streamlit Secrets kısmına GOOGLE_API_KEY ekleyin!")
    st.stop()

# --- 3. ANA EKRAN VE DOSYA YÜKLEME ALANI ---
st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Dosya yükleme ve giriş kutusu yan yana
with st.container(border=True):
    col1, col2 = st.columns([1, 4]) 
    with col1:
        yuklenen_dosya = st.file_uploader("Upload", type=['png', 'jpg', 'jpeg', 'pdf'], label_visibility="collapsed")
    with col2:
        prompt = st.chat_input("Mesajınızı yazın veya dosya ekleyin...")

# Mesaj geçmişini göster
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. CEVAP ÜRETME (404 HATASINI ÖNLEYEN OTOMATİK MODEL SEÇİMİ) ---
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("Eren AI analiz ediyor... 🛡️")
        
        try:
            # 404 hatasını çözmek için sistemde çalışan modeli buluyoruz
            model_list = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            # Önce flash modelini ara, yoksa listedeki ilkini kullan
            safe_model_name = next((m for m in model_list if "gemini-1.5-flash" in m), model_list[0])
            
            model = genai.GenerativeModel(
                model_name=safe_model_name,
                system_instruction=f"Sen Özel Eren Fen ve Teknoloji Lisesi asistanısın. Modun: {modul}. Müdür: Mert Kadıoğlu. Web: www.eren.k12.tr"
            )

            # İçerik hazırlama
            icerik = [prompt]
            if yuklenen_dosya:
                if yuklenen_dosya.type.startswith("image/"):
                    icerik.append(PIL.Image.open(yuklenen_dosya))
                elif yuklenen_dosya.type == "application/pdf":
                    icerik.append({"mime_type": "application/pdf", "data": yuklenen_dosya.read()})

            response = model.generate_content(icerik)
            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            st.error(f"Sistemde bir güncelleme yapılıyor. Lütfen API anahtarınızı kontrol edin. (Detay: {str(e)})")
