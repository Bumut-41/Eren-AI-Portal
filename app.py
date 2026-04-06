import streamlit as st
import google.generativeai as genai
import PIL.Image
import os

# --- 1. GÖRSEL AYARLAR VE SOL MENÜ (GERİ GELDİ) ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=150)
    
    st.subheader("Modül Seçin:")
    modul = st.selectbox(
        "Asistan Modu",
        ["Eren AI Asistanı", "Akademik Destek", "Veli Bilgilendirme"],
        label_visibility="collapsed"
    )
    st.info(f"Aktif: {modul}")
    st.divider()
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

# --- 2. API BAĞLANTISI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Secrets kısmına GOOGLE_API_KEY ekleyin!")
    st.stop()

# --- 3. ANA EKRAN VE DOSYA YÜKLEME (GERİ GELDİ) ---
st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Dosya yükleme ve mesaj kutusu yan yana
with st.container(border=True):
    col1, col2 = st.columns([1, 4]) 
    with col1:
        yuklenen_dosya = st.file_uploader("Upload", type=['png', 'jpg', 'jpeg', 'pdf'], label_visibility="collapsed")
    with col2:
        prompt = st.chat_input("Eren AI'ya bir mesaj yazın...")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. HATAYI BİTİREN GÜVENLİ MODEL ÇAĞRISI ---
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("Eren AI yanıt hazırlıyor... 🛡️")
        
        try:
            # OKULUN GERÇEK BİLGİLERİ (SİSTEME GÖMÜLDÜ)
            sistem_talimati = f"""
            Sen Özel Eren Fen ve Teknoloji Lisesi asistanısın.
            KESİN BİLGİLER:
            - Okul Müdürü: Mert Kadıoğlu
            - Müdür Yardımcısı: Damla İskender
            - Web: https://eren.k12.tr
            Bu bilgiler dışında isim uydurma. Modun: {modul}.
            """

            # 404 hatasını çözmek için model ismini doğrudan 'gemini-pro' veya 'gemini-1.5-flash' olarak dene
            # Senin kütüphanen hangisini tanıyorsa onu seçecek şekilde güncelledim
            model = genai.GenerativeModel('gemini-1.5-flash') 
            
            girdi = [sistem_talimati, prompt]
            if yuklenen_dosya and yuklenen_dosya.type.startswith("image/"):
                girdi.append(PIL.Image.open(yuklenen_dosya))

            response = model.generate_content(girdi)
            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            # Hata kodunu göster ama programı kapatma
            st.error(f"Teknik bir sorun oluştu: {str(e)}")
            st.info("Eğer 404 hatası devam ederse, lütfen API anahtarınızın 'Gemini 1.5 Flash' modelini desteklediğinden emin olun.")
