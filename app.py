import streamlit as st
import google.generativeai as genai
import PIL.Image
import os

# --- 1. SAYFA AYARLARI VE SADELEŞTİRİLMİŞ YAN PANEL ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

with st.sidebar:
    st.title("🛡️ Eren AI")
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=150)
    st.divider()
    # Modül seçimini senin isteğinle kaldırdım.
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

# --- 2. API BAĞLANTISI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Lütfen Streamlit Secrets kısmına API anahtarınızı ekleyin!")
    st.stop()

# --- 3. ANA EKRAN TASARIMI ---
st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Giriş alanı
with st.container(border=True):
    col1, col2 = st.columns([1, 4]) 
    with col1:
        yuklenen_dosya = st.file_uploader("Dosya", type=['png', 'jpg', 'jpeg', 'pdf'], label_visibility="collapsed")
    with col2:
        prompt = st.chat_input("Eren AI'ya bir soru sorun...")

# Mesajları ekrana bas
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. HATAYI BİTİREN CEVAP MOTORU ---
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("Eren AI yanıt veriyor...")
        
        try:
            # 404 hatasını çözmek için 'models/' ekini tamamen sildik.
            # En güncel ve her versiyonda çalışan isim budur:
            model = genai.GenerativeModel('gemini-1.5-flash') 
            
            # Okulun gerçek bilgilerini buraya sabitliyoruz (Artık uyduramaz)
            sistem_talimati = """
            Sen Özel Eren Fen ve Teknoloji Lisesi asistanısın. 
            GERÇEK BİLGİLER:
            - Okul Müdürü: Mert Kadıoğlu
            - Müdür Yardımcısı: Damla İskender
            - Okul Web Sitesi: https://eren.k12.tr
            - Kurucu: Sadıka Ulusan
            Asla yalan isim uydurma. Bilmediğin şeye 'Bilmiyorum' de.
            """

            # İçeriği gönderiyoruz
            response = model.generate_content([sistem_talimati, prompt])
            
            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            # Hata detayını göster ama sistemi çökertme
            st.error(f"Sistem bir sorunla karşılaştı: {str(e)}")
