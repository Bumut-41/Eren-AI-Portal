import streamlit as st
import google.generativeai as genai
import os

# --- 1. SAYFA VE SOL MENÜ AYARLARI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    # Logo dosyası yoksa hata vermemesi için kontrol ekledik
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=150)
    
    st.subheader("Modül Seçin:")
    modul = st.selectbox(
        "Asistan Modu",
        ["Eren AI Asistanı", "Akademik Destek", "Veli Bilgilendirme"],
        label_visibility="collapsed"
    )
    st.divider()
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

# --- 2. API GÜVENLİK KONTROLÜ ---
# API anahtarının doğruluğundan emin olun (Streamlit Secrets üzerinden)
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Hata: Streamlit Secrets kısmında GOOGLE_API_KEY bulunamadı!")
    st.stop()

# --- 3. ANA ARAYÜZ ---
st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Mesaj giriş alanı
prompt = st.chat_input("Mesajınızı buraya yazın...")

# Geçmiş mesajları göster
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. MODEL BAĞLANTISI VE YANIT ÜRETME ---
if prompt:
    # Kullanıcı mesajını ekrana bas ve hafızaya al
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # OKULUN GERÇEK BİLGİLERİNİ BURAYA SABİTLEDİK (ASLA UYDURMAZ)
            sistem_talimati = f"""
            Sen Özel Eren Fen ve Teknoloji Lisesi'nin resmi AI asistanısın.
            KESİN BİLGİLER:
            - Okul Müdürü: Mert Kadıoğlu
            - Müdür Yardımcısı: Damla İskender
            - Kurucu: Sadıka Ulusan
            - Web Sitesi: https://eren.k12.tr
            Bu bilgiler dışında isim uydurma. Modun: {modul}
            """

            # 404 hatasını önlemek için en güncel model tanımlaması
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Yanıtı oluştur
            response = model.generate_content(sistem_talimati + "\n\nKullanıcı Sorusu: " + prompt)
            
            if response.text:
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            else:
                st.warning("Modelden boş bir yanıt döndü.")

        except Exception as e:
            # Hatanın ne olduğunu net görmek için teknik detayı basıyoruz
            st.error(f"Bağlantı Hatası: {str(e)}")
            st.info("Lütfen API anahtarınızın 'Gemini 1.5 Flash' modeline erişimi olduğunu kontrol edin.")
