import streamlit as st
import google.generativeai as genai
import PIL.Image
import os
import requests
from bs4 import BeautifulSoup
import PyPDF2
from docx import Document

# --- 1. AYARLAR VE ARAÇLAR ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

def web_tara(url):
    try:
        r = requests.get(url, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for s in soup(["script", "style", "nav", "footer"]): s.extract()
        return soup.get_text()[:1500]
    except:
        return ""

def dosya_oku(f):
    try:
        if f.name.lower().endswith('.pdf'):
            pdf = PyPDF2.PdfReader(f)
            return "".join([p.extract_text() for p in pdf.pages[:3]])[:3000]
        elif f.name.lower().endswith('.docx'):
            return "\n".join([p.text for p in Document(f).paragraphs[:50]])
        return ""
    except:
        return ""

# --- 2. API BAĞLANTISI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Secrets içinde API anahtarı eksik!")
    st.stop()

# --- 3. ARAYÜZ ---
with st.sidebar:
    st.title("🛡️ Eren AI")
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=150)
    mod = st.selectbox("Mod", ["Asistan", "Akademik", "Veli"])

st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Giriş Bölümü
c1, c2 = st.columns([1, 4])
with c1:
    yukle = st.file_uploader("Dosya", type=['png','jpg','pdf','docx'], label_visibility="collapsed")
with c2:
    soru = st.chat_input("Mesajınızı buraya yazın...")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 4. ASIL İŞLEM (Hata Blokları Tamamen Ayrıldı) ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        alan = st.empty()
        alan.markdown("⚡ *Bağlantı kuruluyor...*")
        
        # Bilgi toplama
        sv = web_tara("https://eren.k12.tr/") if "eren" in soru.lower() else ""
        bv = dosya_oku(yukle) if (yukle and not yukle.type.startswith("image/")) else ""

        try:
            # 404 HATASINI ÖNLEYEN KRİTİK DEĞİŞİKLİK
            # Bazı SDK versiyonlarında 'models/' eklenince hata verir, bazılarında eklenmeyince.
            # En güncel SDK için standart isim:
            model_name = 'gemini-1.5-flash'
            model = genai.GenerativeModel(model_name)
            
            baglam = f"Sen Eren AI'sın. Mod: {mod}. Kaynaklar: {sv} {bv}"
            payload = [baglam, soru]
            
            if yukle and yukle.type.startswith("image/"):
                payload.append(PIL.Image.open(yukle))

            yanit = model.generate_content(payload)
            
            if yanit.text:
                alan.markdown(yanit.text)
                st.session_state.messages.append({"role": "assistant", "content": yanit.text})
            else:
                alan.error("Boş yanıt döndü.")
                
        except Exception as e:
            # Eğer hala 404 verirse 'models/gemini-1.5-flash' denemesi yapacak yedek mekanizma
            try:
                model = genai.GenerativeModel('models/gemini-1.5-flash')
                yanit = model.generate_content(payload)
                alan.markdown(yanit.text)
                st.session_state.messages.append({"role": "assistant", "content": yanit.text})
            except:
                alan.error(f"Bağlantı Hatası: {str(e)}")
