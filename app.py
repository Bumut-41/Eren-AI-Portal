import streamlit as st
import google.generativeai as genai
import PIL.Image
import os

# --- 1. GÖRSEL AYARLAR ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=150)
    
    modul = st.selectbox("Asistan Modu", ["Eren AI Asistanı", "Akademik Destek", "Veli Bilgilendirme"])
    st.divider()
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

# --- 2. API BAĞLANTISI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Secrets kısmına GOOGLE_API_KEY ekleyin!")
    st.stop()

# --- 3. ANA EKRAN ---
st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Giriş Alanı
with st.container(border=True):
    col1, col2 = st.columns([1, 4]) 
    with col1:
        yuklenen_dosya = st.file_uploader("Upload", type=['png', 'jpg', 'jpeg', 'pdf'], label_visibility="collapsed")
    with col2:
        prompt = st.chat_input("Bir mesaj yazın...")

# Geçmişi Yazdır
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. AKILLI VE SADE CEVAP MOTORU ---
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        
        try:
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            
            # Bu talimat sayesinde bilgileri biliyor ama gereksizse söylemiyor
            sistem_bilgi_bankasi = """
            Sen Özel Eren Fen ve Teknoloji Lisesi asistanısın. 
            BİLGİ: Müdür Mert Kadıoğlu, Müdür Yrd. Damla İskender, Kurucu Sadıka Ulusan.
            KURAL: Bu bilgileri sadece kullanıcı okul hakkında spesifik bir soru sorarsa kullan. 
            Her cevabın sonuna bu isimleri ekleme. Sadece sorulan soruya odaklan.
            """

            girdi = [sistem_bilgi_bankasi, prompt]
            if yuklenen_dosya and yuklenen_dosya.type.startswith("image/"):
                girdi.append(PIL.Image.open(yuklenen_dosya))

            response = model.generate_content(girdi)
            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            st.error(f"Bir hata oluştu: {str(e)}")
