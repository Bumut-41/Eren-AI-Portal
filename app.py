import streamlit as st
import google.generativeai as genai
import PIL.Image
import os

# --- 1. SAYFA AYARLARI VE TASARIM ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

# API Yapılandırması
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Secrets içinde API anahtarı bulunamadı!")
    st.stop()

# --- 2. 404 HATASINI BİTİREN MODEL YÜKLEYİCİ ---
@st.cache_resource
def güvenli_model_seç():
    # En güncelden en eskiye tüm isim kombinasyonlarını dene
    denenecek_isimler = [
        'gemini-1.5-flash', 
        'models/gemini-1.5-flash', 
        'gemini-1.0-pro',
        'gemini-pro'
    ]
    
    for isim in denenecek_isimler:
        try:
            m = genai.GenerativeModel(isim)
            # Küçük bir test çalıştırması (opsiyonel)
            return m
        except:
            continue
    # Eğer hiçbiri olmazsa (çok düşük ihtimal) listeyi zorla
    try:
        models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        return genai.GenerativeModel(models[0].name)
    except:
        return genai.GenerativeModel('gemini-1.5-flash')

model = güvenli_model_seç()

# --- 3. YAN ÇUBUK (SIDEBAR) ---
with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=150)
    
    st.divider()
    mod = st.selectbox("Asistan Modu", ["Eren AI Asistanı", "Akademik Destek", "Veli Bilgilendirme"])
    st.divider()
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

# --- 4. ANA EKRAN VE MESAJLAR ---
st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Giriş Kutuları
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        yukle = st.file_uploader("Ek", type=['png','jpg','jpeg','pdf','docx'], label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya bir soru sorun...")

# Geçmişi Göster
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 5. YANIT ÜRETİMİ ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        alan = st.empty()
        alan.markdown("⚡ *Bağlantı kuruluyor...*")
        
        try:
            # Komut ve içerik hazırlığı
            baglam = f"Sen Eren AI'sın. Mod: {mod}. Kurumsal ve yardımcı bir dil kullan."
            payload = [baglam, soru]
            
            if yukle and yukle.type.startswith("image/"):
                img = PIL.Image.open(yukle)
                payload.append(img)

            # Üretim
            yanit = model.generate_content(payload)
            
            if yanit and yanit.text:
                alan.markdown(yanit.text)
                st.session_state.messages.append({"role": "assistant", "content": yanit.text})
            else:
                alan.error("Yanıt üretilemedi, lütfen tekrar deneyin.")
                
        except Exception as e:
            alan.error(f"Sistem Hatası: {str(e)}")
