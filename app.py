import streamlit as st
import google.generativeai as genai
import PIL.Image
import os

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

# API Yapılandırması
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Secrets içinde API anahtarı bulunamadı!")
    st.stop()

# --- 2. MODELİ AKILLI SEÇ (404 ÇÖZÜMÜ) ---
@st.cache_resource
def get_model():
    try:
        # Önce senin sisteminde hangi modellerin 'aktif' olduğuna bakar
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'gemini-1.5-flash' in m.name:
                    return genai.GenerativeModel(m.name)
        return genai.GenerativeModel('gemini-pro')
    except:
        return genai.GenerativeModel('gemini-1.5-flash')

model = get_model()

# --- 3. TASARIM VE YAN ÇUBUK (SIDEBAR) ---
with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    # Logo kontrolü
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=150)
    
    st.divider()
    mod = st.selectbox("Asistan Modu", ["Eren AI Asistanı", "Akademik Destek", "Veli Bilgilendirme"])
    st.divider()
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

# Ana Başlık
st.title("🛡️ Eren AI Portalı")

# Sohbet Geçmişi Hafızası
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 4. GİRİŞ ALANLARI (TASARIMLI) ---
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        yukle = st.file_uploader("Dosya", type=['png','jpg','pdf','docx'], label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya bir soru sorun...")

# Mesajları Ekrana Yazdır
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 5. YANIT MOTORU ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("⚡ *Bağlantı kuruluyor...*")
        
        try:
            # Sistem komutuyla beraber gönder
            prompt_parts = [f"Sen Eren AI'sın. Modun: {mod}. Kurumsal ve yardımcı bir dille yanıt ver.", soru]
            
            # Eğer görsel yüklendiyse ekle
            if yukle and yukle.type.startswith("image/"):
                img = PIL.Image.open(yukle)
                prompt_parts.append(img)

            yanit = model.generate_content(prompt_parts)
            
            if yanit.text:
                placeholder.markdown(yanit.text)
                st.session_state.messages.append({"role": "assistant", "content": yanit.text})
            else:
                placeholder.error("Model boş yanıt döndürdü.")
                
        except Exception as e:
            placeholder.error(f"Sistem Hatası: {str(e)}")
