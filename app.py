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

# --- 2. API VE MODEL DOĞRULAMA (HATA ÇÖZÜCÜ) ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Secrets kısmına GOOGLE_API_KEY ekleyin!")
    st.stop()

# 404 HATASINI BİTİREN FONKSİYON: Senin sisteminde hangi isim çalışıyorsa onu bulur
@st.cache_resource
def get_model_name():
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                # Önce 1.5 Flash, yoksa Pro, o da yoksa ilk bulduğunu seç
                if 'gemini-1.5-flash' in m.name: return m.name
                if 'gemini-pro' in m.name: return m.name
        return "models/gemini-1.5-flash" 
    except:
        return "gemini-pro"

working_model = get_model_name()

# --- 3. ANA EKRAN VE DOSYA YÜKLEME ---
st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Dosya yükleme ve giriş yan yana
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
        
        try:
            model = genai.GenerativeModel(working_model)
            
            # SADELEŞTİRİLMİŞ TALİMAT: Bilgileri biliyor ama zorla söylemiyor
            sistem_mesaji = f"""
            Sen Özel Eren Fen ve Teknoloji Lisesi asistanısın. 
            Müdür: Mert Kadıoğlu, Müdür Yrd: Damla İskender. 
            Bu isimleri sadece sorulursa kullan. Her cevabın sonuna ekleme. 
            Kısa ve öz yanıt ver. Mod: {modul}
            """

            # İçeriği güvenli liste formatında gönder
            icerik = [sistem_mesaji, prompt]
            
            if yuklenen_dosya and yuklenen_dosya.type.startswith("image/"):
                img = PIL.Image.open(yuklenen_dosya)
                icerik.append(img)

            response = model.generate_content(icerik)
            
            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            st.error(f"Bağlantı Hatası: {str(e)}")
            st.info(f"Denenen Model: {working_model}")
