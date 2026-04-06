import streamlit as st
import google.generativeai as genai
import PIL.Image
import os

# --- 1. SAYFA AYARLARI VE SOL MENÜ ---
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
    st.info(f"Aktif Mod: {modul}")
    st.divider()
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

# --- 2. API BAĞLANTISI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Lütfen Secrets kısmına GOOGLE_API_KEY ekleyin!")
    st.stop()

# --- 3. ANA EKRAN TASARIMI ---
st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Dosya yükleme ve mesaj kutusu
with st.container(border=True):
    col1, col2 = st.columns([1, 4]) 
    with col1:
        yuklenen_dosya = st.file_uploader("Upload", type=['png', 'jpg', 'jpeg', 'pdf'], label_visibility="collapsed")
    with col2:
        prompt = st.chat_input("Eren AI'ya bir mesaj yazın...")

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
        placeholder.markdown("Eren AI yanıt hazırlıyor... 🛡️")
        
        try:
            # 404 HATASINI ÇÖZEN KRİTİK NOKTA:
            # Bazı sürümler 'models/' takısını kabul etmiyor. 
            # En güvenli isimlendirme budur:
            model = genai.GenerativeModel('gemini-1.5-flash') 
            
            # Gerçek bilgileri sisteme sabitliyoruz ki uydurmasın
            sistem_mesaji = f"""
            Sen Özel Eren Fen ve Teknoloji Lisesi'nin resmi asistanısın.
            OKUL BİLGİLERİ (GERÇEKTİR, ASLA DEĞİŞTİRME):
            - Okul Müdürü: Mert Kadıoğlu
            - Müdür Yardımcısı: Damla İskender
            - Kurucu: Sadıka Ulusan
            - Web Sitesi: https://eren.k12.tr
            
            Bilmediğin bir personel sorulursa uydurma yapma, web sitesine yönlendir.
            Aktif asistan modun: {modul}
            """

            # İçeriği gönder (Görsel varsa ekle)
            icerik = [sistem_mesaji, prompt]
            if yuklenen_dosya and yuklenen_dosya.type.startswith("image/"):
                icerik.append(PIL.Image.open(yuklenen_dosya))

            response = model.generate_content(icerik)
            
            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            # Eğer hala hata verirse, otomatik olarak alternatif ismi dene
            try:
                model_alt = genai.GenerativeModel('models/gemini-1.5-flash')
                response = model_alt.generate_content([sistem_mesaji, prompt])
                placeholder.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except:
                st.error(f"Sistemde teknik bir aksaklık var: {str(e)}")
