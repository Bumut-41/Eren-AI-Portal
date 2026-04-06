import streamlit as st
import google.generativeai as genai
import PIL.Image
import os

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

# --- 2. SOL MENÜ (SIDEBAR) - MODÜL SEÇİMİ ---
with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    # Logo dosyası dizinde varsa gösterilir
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=150)
    
    st.subheader("Modül Seçin:")
    modul_secimi = st.selectbox(
        "Asistan Modu",
        ["Eren AI Asistanı", "Akademik Destek", "Veli Bilgilendirme"],
        label_visibility="collapsed"
    )
    
    st.info(f"Aktif Mod: {modul_secimi}")
    st.divider()
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

# --- 3. API ANAHTARI KONTROLÜ ---
# ÖNEMLİ: Hata almamak için Streamlit Secrets'a GOOGLE_API_KEY ekle
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Lütfen Streamlit Cloud Secrets kısmına geçerli bir API anahtarı ekleyin.")
    st.stop()

# --- 4. ANA EKRAN VE DOSYA YÜKLEME ALANI ---
st.title("🛡️ Eren AI Portalı")

# Dosya yükleme ve giriş alanı
with st.container(border=True):
    col1, col2 = st.columns([1, 4]) 
    with col1:
        yuklenen_dosya = st.file_uploader("Upload", type=['png', 'jpg', 'jpeg', 'pdf'], label_visibility="collapsed")
    with col2:
        prompt = st.chat_input("Mesajınızı yazın veya dosya ekleyin...")

# Mesaj geçmişi yönetimi
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. CEVAP ÜRETME SÜRECİ ---
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("Eren AI analiz ediyor... 🛡️")
        
        try:
            # 404 hatasını önlemek için model ismini tam yol olarak veriyoruz
            model = genai.GenerativeModel(
                model_name='models/gemini-1.5-flash',
                system_instruction=f"""
                Sen Özel Eren Fen ve Teknoloji Lisesi'nin asistanısın. 
                Aktif modun: {modul_secimi}. 
                Okul müdürü: Mert Kadıoğlu. 
                Web sitesi: www.eren.k12.tr. 
                Bilgileri bu doğrultuda ver.
                """
            )

            # İçerik birleştirme (Metin + Dosya)
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
            # Hata oluşursa kullanıcıya temiz bir mesaj göster
            st.error(f"Bir sorun oluştu. Lütfen API anahtarınızı ve internet bağlantınızı kontrol edin. (Hata: {str(e)})")
