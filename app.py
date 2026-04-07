import streamlit as st
import google.generativeai as genai
import PIL.Image
import os

# --- 1. AYARLAR VE TASARIM ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı!")
    st.stop()

# --- 2. 404 HATASINI BİTİREN DİNAMİK MODEL SEÇİCİ ---
@st.cache_resource
def model_yukle():
    try:
        # Sistemde 'v1' veya 'v1beta' üzerinde hangi model aktifse onu bulur
        modeller = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Öncelik sırasına göre en iyisini seç
        for tercih in ['models/gemini-1.5-flash', 'gemini-1.5-flash', 'models/gemini-pro']:
            if tercih in modeller:
                return genai.GenerativeModel(tercih)
        
        # Hiçbiri yoksa listedeki ilk çalışan modeli döndür
        return genai.GenerativeModel(modeller[0])
    except Exception as e:
        # Liste alınamazsa en güvenli limana sığın
        return genai.GenerativeModel('gemini-pro')

model_engine = model_yukle()

# --- 3. TASARIM (SIDEBAR VE ANA EKRAN) ---
with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=150)
    st.divider()
    mod = st.selectbox("Asistan Modu", ["Eren AI Asistanı", "Akademik Destek", "Veli Bilgilendirme"])
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Giriş Bölümü
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        yukle = st.file_uploader("Ek", type=['png','jpg','jpeg','pdf','docx'], label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya bir soru sorun...")

# Sohbeti Yazdır
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 4. YANIT MOTORU ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        alan = st.empty()
        alan.markdown("⚡ *Bağlantı Kuruluyor...*")
        
        try:
            icerik = [f"Sen Eren AI'sın. Mod: {mod}. Kurumsal ve net cevaplar ver.", soru]
            
            if yukle and yukle.type.startswith("image/"):
                icerik.append(PIL.Image.open(yukle))

            # Üretim (Dinamik model üzerinden)
            yanit = model_engine.generate_content(icerik)
            
            if yanit.text:
                alan.markdown(yanit.text)
                st.session_state.messages.append({"role": "assistant", "content": yanit.text})
            else:
                alan.error("Boş yanıt döndü.")
                
        except Exception as e:
            alan.error(f"Bağlantı Hatası: {str(e)}")
