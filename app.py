import streamlit as st
import google.generativeai as genai
import PIL.Image
import os

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="centered")

# --- 2. API ANAHTARI (SECRETS KONTROLÜ) ---
# Sızıntı (Leak) hatasını engellemek için kodda anahtar bırakmayın
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.warning("Lütfen Streamlit Secrets kısmına GOOGLE_API_KEY ekleyin.")

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

# --- 5. ANA EKRAN ---
st.title("🛡️ Eren AI Portalı")

with st.container(border=True):
    col1, col2 = st.columns([1, 4]) 
    with col1:
        yuklenen_dosya = st.file_uploader("Dosya", type=['png', 'jpg', 'jpeg', 'pdf', 'txt'], label_visibility="collapsed")
    with col2:
        prompt = st.chat_input("Mesajınızı yazın...")

# --- 6. CEVAP ÜRETME (HATASIZ ARAMA ÖZELLİĞİ) ---
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("Eren AI araştırıyor... 🛡️")
        
        try:
            # En kararlı Google Search entegrasyonu
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                tools=[{"google_search_retrieval": {}}], # Hata verirse bu satırı tamamen silebilirsiniz
                system_instruction="""
                Sen Özel Eren Fen ve Teknoloji Lisesi'nin resmi asistanı Eren AI'sın.
                Okulla ilgili soruları 'www.eren.k12.tr' sitesinden araştırarak cevapla.
                """
            )

            icerik = [prompt]
            if yuklenen_dosya:
                if yuklenen_dosya.type.startswith("image/"):
                    icerik.append(PIL.Image.open(yuklenen_dosya))
                else:
                    icerik.append(yuklenen_dosya.read().decode("utf-8")[:10000])

            response = model.generate_content(icerik)
            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            # Eğer Google Search hâlâ hata verirse (bazı bölgelerde kısıtlı olabilir), düz modda çalışır
            try:
                model_simple = genai.GenerativeModel("gemini-1.5-flash")
                response = model_simple.generate_content(icerik)
                placeholder.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except:
                st.error(f"Hata: {str(e)}")
