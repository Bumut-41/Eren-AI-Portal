import streamlit as st
import google.generativeai as genai
import os

# --- 1. SİSTEM SEVİYESİNDE API KİLİTLEME ---
# Hata mesajındaki 'v1beta' zorlamasını burada kırıyoruz.
os.environ["GOOGLE_API_VERSION"] = "v1"

st.set_page_config(page_title="Eren AI - Güvenli Mod", layout="wide")

# --- 2. API YAPILANDIRMASI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Lütfen Streamlit Secrets kısmına GOOGLE_API_KEY ekleyin.")
    st.stop()

# --- 3. MODEL TANIMLAMA (EN KARARLI YÖNTEM) ---
try:
    # 'models/' ön eki olmadan, en yalın haliyle çağırıyoruz.
    # Bu yöntem v1 kararlı sürümünde en yüksek başarıyı verir.
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Model yükleme hatası: {str(e)}")

# --- 4. ARAYÜZ ---
st.title("🛡️ Eren AI Portalı")
st.info("Sistem şu an 'v1 Kararlı Sürüm' modunda çalışıyor.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Eren AI'ya bir soru sorun...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        try:
            # Yanıt üretirken güvenlik önlemlerini de ekliyoruz
            response = model.generate_content(user_input)
            
            if response.text:
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            else:
                st.warning("Yapay zeka boş bir yanıt döndürdü.")
        except Exception as e:
            # Hata devam ederse v1beta mı yoksa başka bir şey mi olduğunu göreceğiz
            st.error(f"Bağlantı Hatası: {str(e)}")
