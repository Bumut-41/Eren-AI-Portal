import streamlit as st
import google.generativeai as genai
import PIL.Image
import os

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="centered")

# --- 2. API ANAHTARI VE GÜVENLİK ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Lütfen Streamlit Secrets kısmına GOOGLE_API_KEY ekleyin!")
    st.stop()

# --- 3. YAN MENÜ ---
with st.sidebar:
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=200)
    st.title("Eren AI Menü")
    st.info("Özel Eren Fen ve Teknoloji Lisesi")
    st.divider()
    st.caption("© 2026 Eren AI")

# --- 4. MESAJ GEÇMİŞİ ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. ANA EKRAN (DOSYA YÜKLEME ALANI GERİ GELDİ) ---
st.title("🛡️ Eren AI Portalı")

# Dosya yükleme kutusunu tekrar ekliyoruz
with st.container(border=True):
    col1, col2 = st.columns([1, 4]) 
    with col1:
        yuklenen_dosya = st.file_uploader("Yükle", type=['png', 'jpg', 'jpeg', 'pdf'], label_visibility="collapsed")
    with col2:
        prompt = st.chat_input("Mesajınızı yazın veya dosya ekleyin...")

# --- 6. ANALİZ VE CEVAP ÜRETME (GÜVENLİ ARAMA) ---
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("Eren AI analiz ediyor... 🛡️")
        
        try:
            # Hata veren 'google_search' kısmını en kararlı şekilde deniyoruz
            try:
                model = genai.GenerativeModel(
                    model_name='gemini-1.5-flash',
                    tools=[{"google_search": {}}], # En güncel arama aracı ismi
                    system_instruction="""Sen Özel Eren Fen ve Teknoloji Lisesi asistanısın. Müdür Mert Kadıoğlu'dur. Bilgileri www.eren.k12.tr adresinden teyit et."""
                )
                
                # İçerik toplama
                icerik = [prompt]
                if yuklenen_dosya:
                    if yuklenen_dosya.type.startswith("image/"):
                        icerik.append(PIL.Image.open(yuklenen_dosya))
                    elif yuklenen_dosya.type == "application/pdf":
                        icerik.append({"mime_type": "application/pdf", "data": yuklenen_dosya.read()})
                
                response = model.generate_content(icerik)
            except:
                # Eğer arama motoru özelliği hata verirse, normal modda devam et
                model_alt = genai.GenerativeModel('gemini-1.5-flash')
                response = model_alt.generate_content(prompt)

            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            st.error(f"Sistemde bir hata oluştu: {str(e)}")
