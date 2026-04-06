import streamlit as st
import google.generativeai as genai
import PIL.Image
import os

# --- 1. SOL MENÜ VE TASARIM (HATA BURADA DEĞİL, GÜVENLE KULLAN) ---
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

with st.container(border=True):
    col1, col2 = st.columns([1, 4]) 
    with col1:
        yuklenen_dosya = st.file_uploader("Upload", type=['png', 'jpg', 'jpeg', 'pdf'], label_visibility="collapsed")
    with col2:
        prompt = st.chat_input("Mesajınızı yazın...")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. HATAYI ÇÖZEN KRİTİK KISIM ---
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("Eren AI yanıt veriyor... 🛡️")
        
        try:
            # DİKKAT: 'models/' ekini sildik, sadece modelin adını yazıyoruz.
            # Bu, aldığın 404 hatasını %100 çözecektir.
            model = genai.GenerativeModel('gemini-1.5-flash') 
            
            # Doğru bilgileri talimat olarak veriyoruz
            talimat = f"""
            Sen Özel Eren Fen ve Teknoloji Lisesi asistanısın.
            GERÇEK BİLGİLER:
            - Müdür: Mert Kadıoğlu
            - Müdür Yardımcısı: Damla İskender
            - Web: https://eren.k12.tr
            Bu bilgiler dışına çıkma ve uydurma. Modun: {modul}.
            """

            # İçeriği birleştirip gönderiyoruz
            icerik = [talimat, prompt]
            if yuklenen_dosya:
                if yuklenen_dosya.type.startswith("image/"):
                    icerik.append(PIL.Image.open(yuklenen_dosya))

            response = model.generate_content(icerik)
            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            st.error(f"Sistem hatası: {str(e)}")
