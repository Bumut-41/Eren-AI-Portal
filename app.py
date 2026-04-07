import streamlit as st
import google.generativeai as genai
import PIL.Image
import os
import requests
from bs4 import BeautifulSoup
import PyPDF2
from docx import Document

# --- 1. FONKSİYONLAR (Hata riskini azaltmak için en başa alındı) ---
def hizli_web_tara(url):
    try:
        r = requests.get(url, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for s in soup(["script", "style", "nav", "footer"]): s.extract()
        return soup.get_text()[:1500]
    except:
        return ""

def hizli_belge_oku(dosya):
    try:
        if dosya.name.lower().endswith('.pdf'):
            pdf = PyPDF2.PdfReader(dosya)
            return "".join([p.extract_text() for p in pdf.pages[:3]])[:3000]
        elif dosya.name.lower().endswith('.docx'):
            return "\n".join([p.text for p in Document(dosya).paragraphs[:50]])
        return ""
    except:
        return ""

# --- 2. AYARLAR ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Secrets içinde API anahtarı bulunamadı!")
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

c1, c2 = st.columns([1, 4])
with c1:
    yukle = st.file_uploader("Dosya", type=['png','jpg','pdf','docx'], label_visibility="collapsed")
with c2:
    soru = st.chat_input("Mesajınızı buraya yazın...")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 4. ASIL İŞLEM DÖNGÜSÜ (Syntax Hatası İçermez) ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("⚡ *İşleniyor...*")
        
        site_bilgisi = hizli_web_tara("https://eren.k12.tr/") if "eren" in soru.lower() else ""
        belge_bilgisi = hizli_belge_oku(yukle) if (yukle and not yukle.type.startswith("image/")) else ""

        try:
            # 404 HATASINI ÖNLEYEN MODEL TANIMI
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            baglam = f"Sen Eren AI'sın. Mod: {mod}. Kaynaklar: {site_bilgisi} {belge_bilgisi}"
            payload = [baglam, soru]
            
            if yukle and yukle.type.startswith("image/"):
                payload.append(PIL.Image.open(yukle))

            yanit = model.generate_content(payload)
            
            if yanit.text:
                placeholder.markdown(yanit.text)
                st.session_state.messages.append({"role": "assistant", "content": yanit.text})
            else:
                placeholder.error("Yanıt üretilemedi.")
                
        except Exception as e:
            placeholder.error(f"Sistem Hatası: {str(e)}")
