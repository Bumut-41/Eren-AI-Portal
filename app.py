import streamlit as st
import google.generativeai as genai
import PIL.Image
import os

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="centered")

# --- 2. GÜVENLİ API ANAHTARI BAĞLANTISI ---
# Kod sızıntısını önlemek için Secrets üzerinden çalışır
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Hata: Lütfen Streamlit Cloud Secrets kısmına GOOGLE_API_KEY ekleyin!")

# --- 3. YAN MENÜ VE LOGO ---
with st.sidebar:
    # Logo.png dosyasının GitHub'da aynı klasörde olduğundan emin ol
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
        # Dosya yükleyici alanı
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
            # Model Seçimi
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            target_model = next((m for m in available_models if "gemini-1.5-flash" in m), available_models[0])
            
            # --- MODEL TANIMLAMA (KİMLİK + ARAMA ÖZELLİĞİ) ---
            model = genai.GenerativeModel(
                model_name=target_model,
                # Google Arama özelliğini aktif ediyoruz
                tools=[{"google_search_retrieval": {}}],
                system_instruction="""
                Sen Özel Eren Fen ve Teknoloji Lisesi'nin resmi yapay zeka asistanısın (Eren AI). 
                Görevin okulun vizyonuna uygun bilimsel ve akademik destek vermektir. 
                Sana 'kimsin' denildiğinde Özel Eren Fen ve Teknoloji Lisesi asistanı olduğunu söylemelisin.
                
                ÖNEMLİ: Okulunla ilgili (müdür, duyurular, etkinlikler vb.) her soruyu 
                MUTLAKA 'www.eren.k12.tr' sitesinden araştırarak en güncel bilgiyi ver.
                Eğer sitede bilgi bulamazsan tahminde bulunma, kullanıcıyı okul yönetimine yönlendir.
                """
            )

            # İçerik toplama (Metin + Dosya)
            icerik = [prompt]
            if yuklenen_dosya:
                if yuklenen_dosya.type == "application/pdf":
                    icerik.append({"mime_type": "application/pdf", "data": yuklenen_dosya.read()})
                elif yuklenen_dosya.type.startswith("image/"):
                    icerik.append(PIL.Image.open(yuklenen_dosya))
                else:
                    icerik.append(yuklenen_dosya.getvalue().decode("utf-8"))

            # Yanıt üretme
            response = model.generate_content(icerik)
            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            # Sızıntı hatası durumunda kullanıcıyı uyarır
            if "403" in str(e):
                st.error("Hata: API anahtarı sızdırıldığı için iptal edilmiş. Lütfen Secrets kısmına YENİ anahtarı ekleyin.")
            else:
                st.error(f"Hata: {str(e)}")
