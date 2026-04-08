import streamlit as st
import google.generativeai as genai
import PIL.Image
import os
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document
from pptx import Presentation

# --- SİSTEM AYARLARI ---
os.environ["GOOGLE_API_VERSION"] = "v1" # v1beta hatasını önler
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı!")
    st.stop()

# --- GELİŞMİŞ DOSYA OKUMA MOTORU ---
def dosya_icerigini_coz(dosya):
    try:
        # PDF Okuma
        if dosya.type == "application/pdf":
            okuyucu = PdfReader(dosya)
            return "\n".join([sayfa.extract_text() for sayfa in okuyucu.pages if sayfa.extract_text()])
        
        # Word (DOCX) Okuma
        elif dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            belge = Document(dosya)
            return "\n".join([p.text for p in belge.paragraphs])
        
        # PowerPoint (PPTX) Okuma
        elif "presentationml" in dosya.type:
            sunum = Presentation(dosya)
            text_runs = []
            for slide in sunum.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text_runs.append(shape.text)
            return "\n".join(text_runs)
        
        # Excel (XLSX) veya CSV Okuma
        elif "spreadsheetml" in dosya.type or "csv" in dosya.type:
            df = pd.read_excel(dosya) if "spreadsheet" in dosya.type else pd.read_csv(dosya)
            return f"Tablo Verileri:\n{df.to_string()}"
            
        return None
    except Exception as e:
        return f"Dosya işlenirken hata: {e}"

# Model Tanımı
model = genai.GenerativeModel('models/gemini-1.5-flash')

# --- ARAYÜZ ---
with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    # Okul Logosu (İnternet üzerinden çekmek en güvenlisi)
    st.image("https://eren.k12.tr/wp-content/uploads/2021/05/ozel-eren-logo-1.png", width=180)
    st.divider()
    mod = st.selectbox("Asistan Modu", ["Eren AI Asistanı", "Akademik Analiz", "Veli Bilgilendirme"])
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Mesaj Geçmişi
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Giriş Bölümü (Sütunlu Tasarım)
with st.container():
    sol, sag = st.columns([1, 4])
    with sol:
        yukle = st.file_uploader("Dosya", type=['pdf','docx','pptx','xlsx','csv','png','jpg','jpeg'], label_visibility="collapsed")
    with sag:
        soru = st.chat_input("Eren AI'ya sorun...")

# --- YANIT ÜRETİMİ ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        cevap_alani = st.empty()
        cevap_alani.markdown("⚡ *Dökümanlar ve veriler analiz ediliyor...*")
        
        try:
            prompt_havuzu = [f"Sen Eren AI'sın. Özel Eren Fen ve Teknoloji Lisesi asistanısın. Mod: {mod}.", soru]
            
            if yukle:
                if yukle.type.startswith("image/"):
                    # Görsel ise doğrudan yapay zekaya gönder
                    prompt_havuzu.append(PIL.Image.open(yukle))
                else:
                    # Metin/Tablo tabanlıysa içeriği oku ve metin olarak ekle
                    metin = dosya_icerigini_coz(yukle)
                    if metin:
                        prompt_havuzu.append(f"\n[DÖKÜMAN İÇERİĞİ]:\n{metin}")

            # Yanıt Üret
            yanit = model.generate_content(prompt_havuzu)
            
            if yanit.text:
                cevap_alani.markdown(yanit.text)
                st.session_state.messages.append({"role": "assistant", "content": yanit.text})
                
        except Exception as e:
            cevap_alani.error(f"Sistem Hatası: {str(e)}")
