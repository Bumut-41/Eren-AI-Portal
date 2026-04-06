import streamlit as st
import google.generativeai as genai
import PIL.Image
import os

# --- 1. GÖRSEL AYARLAR VE SOL MENÜ ---
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

# --- 2. API VE OTOMATİK MODEL BULUCU ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Secrets kısmına GOOGLE_API_KEY ekleyin!")
    st.stop()

# Programın içinden hatayı çözmeye çalışan fonksiyon
@st.cache_resource
def get_working_model():
    try:
        # Senin API anahtarınla erişebildiğin modelleri listele
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                # 1.5 Flash veya Pro modellerinden birini seç
                if 'gemini-1.5-flash' in m.name or 'gemini-pro' in m.name:
                    return m.name
        return None
    except Exception:
        return "gemini-1.5-flash" # Hata olursa varsayılana dön

working_model_name = get_working_model()

# --- 3. ANA EKRAN VE DOSYA YÜKLEME ---
st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Görseldeki düzenin aynısı: Dosya yükleme ve giriş yan yana
with st.container(border=True):
    col1, col2 = st.columns([1, 4]) 
    with col1:
        yuklenen_dosya = st.file_uploader("Upload", type=['png', 'jpg', 'jpeg', 'pdf'], label_visibility="collapsed")
    with col2:
        prompt = st.chat_input("Mesajınızı yazın...")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. AKILLI CEVAP MOTORU ---
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("Eren AI sistemi kontrol ediyor... 🛡️")
        
        try:
            # Otomatik bulunan modeli kullan (404 hatasını bu çözer)
            model = genai.GenerativeModel(working_model_name)
            
            sistem_mesaji = f"""
            Sen Özel Eren Fen ve Teknoloji Lisesi'nin asistanısın.
            OKUL BİLGİLERİ:
            - Müdür: Mert Kadıoğlu
            - Müdür Yardımcısı: Damla İskender
            - Web: https://eren.k12.tr
            Modun: {modul}.
            """

            girdi = [sistem_mesaji, prompt]
            if yuklenen_dosya and yuklenen_dosya.type.startswith("image/"):
                girdi.append(PIL.Image.open(yuklenen_dosya))

            response = model.generate_content(girdi)
            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            st.error(f"Bağlantı kurulamadı. Model: {working_model_name}. Hata: {str(e)}")
