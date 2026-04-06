import streamlit as st
import google.generativeai as genai
import PIL.Image
import os

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="centered")

# --- 2. GÜVENLİ API ANAHTARI BAĞLANTISI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Hata: Lütfen Streamlit Cloud Secrets kısmına GOOGLE_API_KEY ekleyin!")

# --- 3. YAN MENÜ VE LOGO ---
with st.sidebar:
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=200)
    st.title("Eren AI Menü")
    st.info("Özel Eren Fen ve Teknoloji Lisesi Resmi Asistanı")
    st.divider()
    st.caption("© 2026 Eren AI")

# --- 4. MESAJ GEÇMİŞİ ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. ANA EKRAN VE GİRİŞ ALANI ---
st.title("🛡️ Eren AI Portalı")

with st.container(border=True):
    col1, col2 = st.columns([1, 4]) 
    with col1:
        yuklenen_dosya = st.file_uploader("Dosya", type=['png', 'jpg', 'jpeg', 'pdf', 'txt'], label_visibility="collapsed")
    with col2:
        prompt = st.chat_input("Mesajınızı yazın...")

# --- 6. ANALİZ VE CEVAP ÜRETME ---
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("Eren AI araştırıyor ve analiz ediyor... 🛡️")
        
        try:
            # --- MODEL VE DOĞRU ARAÇ TANIMLAMA ---
            # Hata 400 Çözümü: 'google_search_retrieval' yerine sadece 'google_search' kullanıyoruz
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                tools=[{"google_search": {}}], 
                system_instruction="""
                Sen Özel Eren Fen ve Teknoloji Lisesi'nin resmi yapay zeka asistanısın (Eren AI). 
                Görevin okulun vizyonuna uygun bilimsel ve akademik destek vermektir. 
                Sana 'kimsin' denildiğinde Özel Eren Fen ve Teknoloji Lisesi asistanı olduğunu söylemelisin.
                
                ÖNEMLİ: Okulunla ilgili her soruyu MUTLAKA 'www.eren.k12.tr' sitesinden araştırarak yanıtla.
                """
            )

            # İçerik toplama
            icerik = [prompt]
            if yuklenen_dosya:
                if yuklenen_dosya.type == "application/pdf":
                    icerik.append({"mime_type": "application/pdf", "data": yuklenen_dosya.read()})
                elif yuklenen_dosya.type.startswith("image/"):
                    icerik.append(PIL.Image.open(yuklenen_dosya))

            # Yanıt üretme
            response = model.generate_content(icerik)
            
            # Yanıtın metin kısmını al
            if response.text:
                full_response = response.text
            else:
                full_response = "Üzgünüm, bu konuda bilgi bulamadım."
                
            placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"Hata oluştu: {str(e)}")
