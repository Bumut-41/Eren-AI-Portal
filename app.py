import streamlit as st
import google.generativeai as genai
import PIL.Image
import os
from PyPDF2 import PdfReader
from docx import Document
import io

# --- 1. AYARLAR VE TASARIM ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı!")
    st.stop()

# --- 2. DOSYA OKUMA FONKSİYONLARI ---
def dosya_metnini_oku(yuklenen_dosya):
    try:
        if yuklenen_dosya.type == "application/pdf":
            reader = PdfReader(yuklenen_dosya)
            return "\n".join([page.extract_text() for page in reader.pages])
        elif yuklenen_dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(yuklenen_dosya)
            return "\n".join([para.text for para in doc.paragraphs])
        return None
    except Exception as e:
        return f"Dosya okunurken hata oluştu: {e}"

@st.cache_resource
def model_yukle():
    modeller = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    for tercih in ['models/gemini-1.5-flash', 'gemini-1.5-flash', 'models/gemini-pro']:
        if tercih in modeller:
            return genai.GenerativeModel(tercih)
    return genai.GenerativeModel(modeller[0])

model_engine = model_yukle()

# --- 3. ARAYÜZ (SIDEBAR) ---
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
        yukle = st.file_uploader("Dosya", type=['png','jpg','jpeg','pdf','docx'], label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya bir soru sorun...")

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
        alan.markdown("⚡ *Dosya inceleniyor ve yanıt üretiliyor...*")
        
        try:
            icerik = [f"Sen Eren AI'sın. Mod: {mod}. Kurumsal bir dille yanıt ver.", soru]
            
            if yukle:
                if yukle.type.startswith("image/"):
                    icerik.append(PIL.Image.open(yukle))
                else:
                    metin = dosya_metnini_oku(yukle)
                    if metin:
                        icerik.append(f"\n--- YÜKLENEN DOSYA İÇERİĞİ ---\n{metin}")

            yanit = model_engine.generate_content(icerik)
            
            if yanit.text:
                alan.markdown(yanit.text)
                st.session_state.messages.append({"role": "assistant", "content": yanit.text})
            else:
                alan.error("Boş yanıt döndü.")
                
        except Exception as e:
            alan.error(f"Bağlantı Hatası: {str(e)}")
