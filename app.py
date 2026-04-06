import streamlit as st
import google.generativeai as genai
import PIL.Image
import os

# --- 1. SAYFA AYARLARI VE SOL MENÜ (GERİ GELDİ) ---
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
    st.error("Lütfen Secrets kısmına GOOGLE_API_KEY ekleyin!")
    st.stop()

# --- 3. ANA EKRAN VE GİRİŞ ALANI ---
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

# --- 4. HATASIZ CEVAP ÜRETME MOTORU ---
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("Eren AI yanıt hazırlıyor... 🛡️")
        
        try:
            # 404 HATASINI BİTİREN KRİTİK DEĞİŞİKLİK:
            # Başına 'models/' eklemiyoruz, sadece saf ismi yazıyoruz.
            model = genai.GenerativeModel('gemini-1.5-flash') 
            
            # Gerçek verileri sisteme sabitliyoruz
            sistem_talimati = f"""
            Sen Özel Eren Fen ve Teknoloji Lisesi'nin resmi asistanısın.
            KESİN BİLGİLER:
            - Okul Müdürü: Mert Kadıoğlu
            - Müdür Yardımcısı: Damla İskender
            - Kurucu: Sadıka Ulusan
            - Web: https://eren.k12.tr
            Bu isimler dışında birini uydurma. Modun: {modul}.
            """

            # Veriyi gönder
            # Eğer resim yüklendiyse onu da analize dahil et
            girdi = [sistem_talimati, prompt]
            if yuklenen_dosya and yuklenen_dosya.type.startswith("image/"):
                girdi.append(PIL.Image.open(yuklenen_dosya))

            response = model.generate_content(girdi)
            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            # Eğer hala hata verirse ne olduğunu tam görelim
            st.error(f"Teknik bir sorun oluştu: {str(e)}")
