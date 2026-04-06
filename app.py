import streamlit as st
import google.generativeai as genai
import PIL.Image
import os

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="centered")

# --- 2. API ANAHTARI VE GÜVENLİK ---
# Eğer Secrets kısmına GOOGLE_API_KEY eklemediysen uygulama çalışmaz.
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

# --- 5. ANA EKRAN ---
st.title("🛡️ Eren AI Portalı")

with st.container(border=True):
    col1, col2 = st.columns([1, 4]) 
    with col1:
        yuklenen_dosya = st.file_uploader("Dosya", type=['png', 'jpg', 'jpeg', 'pdf'], label_visibility="collapsed")
    with col2:
        prompt = st.chat_input("Mesajınızı yazın...")

# --- 6. ANALİZ VE CEVAP ÜRETME (404 HATASINI ÖNLEYEN YAPI) ---
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("Eren AI araştırıyor... 🛡️")
        
        try:
            # 404 hatasını aşmak için sistemde aktif olan ilk uygun modeli seçiyoruz
            model_list = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            # Önce flash modelini dene, yoksa listedeki ilk modeli al
            safe_model_name = next((m for m in model_list if "gemini-1.5-flash" in m), model_list[0])
            
            model = genai.GenerativeModel(
                model_name=safe_model_name,
                # Arama özelliği hata verirse sistemi durdurmaması için şimdilik sade tutuyoruz
                system_instruction="""
                Sen Özel Eren Fen ve Teknoloji Lisesi'nin resmi asistanı Eren AI'sın.
                Okul web sitesi: www.eren.k12.tr. Bilimsel ve nazik bir dil kullan.
                """
            )

            # İçerik hazırlama
            icerik = [prompt]
            if yuklenen_dosya:
                if yuklenen_dosya.type.startswith("image/"):
                    icerik.append(PIL.Image.open(yuklenen_dosya))
                elif yuklenen_dosya.type == "application/pdf":
                    icerik.append({"mime_type": "application/pdf", "data": yuklenen_dosya.read()})

            # Yanıt oluşturma
            response = model.generate_content(icerik)
            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            st.error(f"Bir sorun oluştu: {str(e)}")
