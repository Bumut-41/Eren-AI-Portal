import streamlit as st
import google.generativeai as genai
import PIL.Image
import os

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="centered")

# --- 2. API ANAHTARI ---
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

# --- 4. ANALİZ VE CEVAP ÜRETME (ARAMA MOTORU AKTİF) ---
st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Mesajınızı yazın...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("Eren AI internette araştırıyor... 🌐")
        
        try:
            # GÜNCEL ARAMA MOTORU YAPISI
            # 'google_search_retrieval' yerine en güncel 'google_search' aracını kullanıyoruz
            model = genai.GenerativeModel(
                model_name='gemini-1.5-flash',
                tools=[{"google_search": {}}], 
                system_instruction="""
                Sen Özel Eren Fen ve Teknoloji Lisesi'nin resmi asistanısın. 
                Okul müdürü, öğretmenler veya akademik takvim gibi konularda ASLA ezbere cevap verme.
                MUTLAKA 'www.eren.k12.tr' sitesini Google üzerinden tara ve oradaki güncel bilgiyi ver.
                Örneğin; okul müdürü Mert Kadıoğlu'dur.
                """
            )

            response = model.generate_content(prompt)
            
            # Yanıtı ekrana yazdır
            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            st.error(f"Hata oluştu: {str(e)}")
