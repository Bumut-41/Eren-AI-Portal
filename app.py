import streamlit as st
import google.generativeai as genai
from google.generativeai import client
import PIL.Image
import os
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document
from pptx import Presentation

# --- 1. KRİTİK: API VERSİYONUNU ÇEKİRDEKTEN KİLİTLEME ---
# Hata mesajındaki 'v1beta' zorlamasını engellemek için hem ortam değişkenini 
# hem de kütüphane istemcisini v1'e zorluyoruz.
os.environ["GOOGLE_API_VERSION"] = "v1"
client._API_VERSION = "v1" 

# --- 2. SAYFA VE API YAPILANDIRMASI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı! Lütfen Secrets ayarlarını kontrol edin.")
    st.stop()

# Modeli en yalın ismiyle tanımlıyoruz
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 3. DOSYA OKUMA MOTORU ---
def dosya_oku(dosya):
    try:
        if dosya.type == "application/pdf":
            reader = PdfReader(dosya)
            return "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
        elif dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(dosya)
            return "\n".join([p.text for p in doc.paragraphs])
        elif dosya.type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
            prs = Presentation(dosya)
            return "\n".join([shape.text for slide in prs.slides for shape in slide.shapes if hasattr(shape, "text")])
        elif dosya.type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "text/csv"]:
            df = pd.read_excel(dosya) if "spreadsheet" in dosya.type else pd.read_csv(dosya)
            return df.to_string()
        return None
    except Exception as e:
        return f"Okuma Hatası: {str(e)}"

# --- 4. ARAYÜZ (SOL MENÜ, LOGO VE YÜKLEME) ---
with st.sidebar:
    # Logo sorununu okulun logosunun URL'sini kullanarak çözüyoruz
    st.image("https://eren.k12.tr/wp-content/uploads/2021/05/ozel-eren-logo-1.png", width=200)
    st.title("🛡️ Eren AI Menü")
    mod = st.selectbox("Asistan Modu", ["Eren AI Asistanı", "Akademik Analiz", "Okul Bilgilendirme"])
    
    st.subheader("📁 Belge Yükle")
    yuklenen = st.file_uploader("Dosyayı buraya bırakın", type=['pdf','docx','pptx','xlsx','csv','png','jpg','jpeg'])
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

st.title("🛡️ Eren AI Portalı")
st.markdown(f"**Mod:** {mod} | **Sistem:** v1 Stable")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 5. ANALİZ VE YANIT MOTORU ---
soru = st.chat_input("Eren AI'ya sorunuzu iletin...")

if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        cevap_alani = st.empty()
        cevap_alani.markdown("⚡ *Döküman inceleniyor...*")
        
        try:
            # Talimatlar ve Dosya Enjeksiyonu
            komut = [f"Sen Özel Eren Fen ve Teknoloji Lisesi asistanısın. Mod: {mod}.", soru]
            
            if yuklenen:
                if yuklenen.type.startswith("image/"):
                    komut.append(PIL.Image.open(yuklenen))
                else:
                    icerik = dosya_oku(yuklenen)
                    if icerik:
                        komut.append(f"\nBELGE İÇERİĞİ:\n{icerik}")

            # Yanıt üretimi
            yanit = model.generate_content(komut)
            
            if yanit.text:
                cevap_alani.markdown(yanit.text)
                st.session_state.messages.append({"role": "assistant", "content": yanit.text})
        except Exception as e:
            # Hata devam ederse buradaki detay her şeyi açıklayacak
            cevap_alani.error(f"Bağlantı Hatası: {str(e)}")
