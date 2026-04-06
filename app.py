import streamlit as st
import google.generativeai as genai
import PIL.Image
import os

# --- 1. GÖRSEL AYARLAR (SOL MENÜ VE LOGO) ---
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
    st.error("Lütfen Streamlit Secrets kısmına API anahtarınızı ekleyin!")
    st.stop()

# --- 3. ANA EKRAN VE DOSYA YÜKLEME ---
st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Senin istediğin dosya yükleme ve giriş alanı
with st.container(border=True):
    col1, col2 = st.columns([1, 4]) 
    with col1:
        yuklenen_dosya = st.file_uploader("Upload", type=['png', 'jpg', 'jpeg', 'pdf'], label_visibility="collapsed")
    with col2:
        prompt = st.chat_input("Mesajınızı yazın veya dosya ekleyin...")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. ANALİZ VE CEVAP (DOĞRULANMIŞ VERİLERLE) ---
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("Eren AI gerçek verileri analiz ediyor... 🛡️")
        
        try:
            # 404 hatasını önlemek için 'models/' ön ekini kaldırdım
            # Bilgileri uydurmaması için doğrudan sistem talimatına yazdım
            model = genai.GenerativeModel(
                model_name='gemini-1.5-flash',
                system_instruction=f"""
                Sen Özel Eren Fen ve Teknoloji Lisesi'nin resmi asistanısın. 
                RESMİ WEB SİTESİ VERİLERİ (ASLA DIŞINA ÇIKMA VE UYDURMA):
                - Okul Müdürü: Mert Kadıoğlu
                - Müdür Yardımcısı: Damla İskender
                - Kurucu: Sadıka Ulusan
                - Web: https://eren.k12.tr
                
                Sana sorulan kişi bu listede yoksa, uydurmak yerine 'Bu bilgiye şu an ulaşamıyorum, lütfen okulun resmi sitesini (https://eren.k12.tr) kontrol edin' de.
                Aktif modun: {modul}.
                """
            )

            icerik = [prompt]
            if yuklenen_dosya:
                if yuklenen_dosya.type.startswith("image/"):
                    icerik.append(PIL.Image.open(yuklenen_dosya))
                elif yuklenen_dosya.type == "application/pdf":
                    icerik.append({"mime_type": "application/pdf", "data": yuklenen_dosya.read()})

            response = model.generate_content(icerik)
            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            st.error(f"Sistemde teknik bir aksaklık oluştu: {str(e)}")
