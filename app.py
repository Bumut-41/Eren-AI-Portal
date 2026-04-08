import streamlit as st
import google.generativeai as genai
import PIL.Image
import os
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document
from pptx import Presentation

# --- SİSTEM AYARLARI ---
# v1beta hatasını önlemek için çevresel değişkeni en üstte zorluyoruz
os.environ["GOOGLE_API_VERSION"] = "v1" 

st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı!")
    st.stop()

# --- GELİŞMİŞ DOSYA ANALİZ MOTORU ---
def dosya_icerigini_oku(dosya):
    try:
        # 1. PDF Okuma
        if dosya.type == "application/pdf":
            reader = PdfReader(dosya)
            return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        
        # 2. Word (DOCX) Okuma
        elif dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(dosya)
            return "\n".join([p.text for p in doc.paragraphs])
        
        # 3. PowerPoint (PPTX) Okuma
        elif "presentationml" in dosya.type:
            pptx = Presentation(dosya)
            text = []
            for slide in pptx.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text.append(shape.text)
            return "\n".join(text)
        
        # 4. Excel (XLSX) veya CSV Okuma
        elif "spreadsheetml" in dosya.type or "csv" in dosya.type:
            df = pd.read_excel(dosya) if "spreadsheet" in dosya.type else pd.read_csv(dosya)
            # Veriyi asistanın anlayabileceği özet bir tablo metnine çevirir
            return f"Tablo Verisi Önemli Satırlar:\n{df.head(20).to_string()}"
            
        return None
    except Exception as e:
        return f"Okuma hatası: {str(e)}"

# Model Tanımı (v1 zorlamalı tam yol)
model_engine = genai.GenerativeModel('models/gemini-1.5-flash')

# --- ARAYÜZ ---
with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    # Logo yoksa okul adını yazdırır
    st.image("https://eren.k12.tr/wp-content/uploads/2021/05/ozel-eren-logo-1.png", width=180)
    st.divider()
    mod = st.selectbox("Asistan Modu", ["Eren AI Asistanı", "Akademik Analiz", "Veli Bilgilendirme"])
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Mesaj Geçmişini Yazdır
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Giriş Alanı
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        yukle = st.file_uploader("Dosya", type=['pdf','docx','pptx','xlsx','csv','png','jpg','jpeg'], label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya bir soru sorun...")

# --- İŞLEME MANTIĞI ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        alan = st.empty()
        alan.info("🛡️ Eren AI verileri işliyor...")
        
        try:
            # Sistem talimatı ve kullanıcı sorusu
            prompt = [f"Sen Eren AI'sın. Mod: {mod}. Profesyonel bir lise asistanısın.", soru]
            
            if yukle:
                if yukle.type.startswith("image/"):
                    # Görseli doğrudan gönder
                    prompt.append(PIL.Image.open(yukle))
                else:
                    # Diğer belgeleri metne çevirip gönder
                    metin_verisi = dosya_icerigini_oku(yukle)
                    if metin_verisi:
                        prompt.append(f"\n[YÜKLENEN BELGE İÇERİĞİ]:\n{metin_verisi}")

            # Yanıt Üret (v1 yolu üzerinden)
            response = model_engine.generate_content(prompt)
            
            if response.text:
                alan.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
        except Exception as e:
            # Hata mesajını yakala ve kullanıcıya temiz göster
            alan.error(f"Sistem hatası oluştu. Lütfen sayfayı yenileyin. Detay: {str(e)}")
