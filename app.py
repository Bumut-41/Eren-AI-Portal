import streamlit as st
import google.generativeai as genai
import PIL.Image
import os
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document
from pptx import Presentation

# --- SİSTEM AYARLARI ---
# v1beta hatasını önlemek için çevresel değişkeni zorluyoruz
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
        # PDF Okuma
        if dosya.type == "application/pdf":
            reader = PdfReader(dosya)
            return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        
        # Word (DOCX) Okuma
        elif dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(dosya)
            return "\n".join([p.text for p in doc.paragraphs])
        
        # PowerPoint (PPTX) Okuma
        elif "presentationml" in dosya.type:
            pptx = Presentation(dosya)
            text = []
            for slide in pptx.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"): text.append(shape.text)
            return "\n".join(text)
        
        # Excel (XLSX) veya CSV Okuma
        elif "spreadsheetml" in dosya.type or "csv" in dosya.type:
            df = pd.read_excel(dosya) if "spreadsheet" in dosya.type else pd.read_csv(dosya)
            return f"Tablo Verisi Özeti:\n{df.to_string()}"
            
        return None
    except Exception as e:
        return f"Okuma hatası: {str(e)}"

# --- MODEL YAPILANDIRMASI ---
# Model ismini sadece 'gemini-1.5-flash' olarak kullanmak v1beta hatasını çözer
model = genai.GenerativeModel('gemini-1.5-flash')

# --- ARAYÜZ ---
with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    # Logo yüklenemezse isim yazdırılır
    st.markdown("### Özel Eren Fen ve Teknoloji Lisesi")
    st.divider()
    mod = st.selectbox("Asistan Modu", ["Eren AI Asistanı", "Akademik Analiz", "Veli Bilgilendirme"])
    st.caption("© 2026 Eren Eğitim Kurumları")

st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Mesaj Geçmişi
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Giriş Bölümü
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        yukle = st.file_uploader("Dosya", type=['pdf','docx','pptx','xlsx','csv','png','jpg'], label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya sorunuzu iletin...")

# --- İŞLEME VE YANIT ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        cevap_alani = st.empty()
        cevap_alani.info("🛡️ Eren AI analiz ediyor...")
        
        try:
            # Sistem talimatı
            prompt_list = [f"Sen Eren AI'sın. Mod: {mod}. Profesyonel bir lise asistanısın.", soru]
            
            if yukle:
                if yukle.type.startswith("image/"):
                    prompt_list.append(PIL.Image.open(yukle))
                else:
                    metin = dosya_icerigini_oku(yukle)
                    if metin:
                        prompt_list.append(f"\n[DÖKÜMAN İÇERİĞİ]:\n{metin}")

            # Yanıt Üret (v1 yolu üzerinden)
            response = model.generate_content(prompt_list)
            
            if response.text:
                cevap_alani.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
        except Exception as e:
            # Hata devam ederse detaylı uyarı gösterilir
            cevap_alani.error(f"Sistem Hatası: {str(e)}. Lütfen kütüphane versiyonunu kontrol edin.")
