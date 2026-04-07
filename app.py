import streamlit as st
import google.generativeai as genai
import PIL.Image
import os
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document
from pptx import Presentation # PowerPoint için ekledik

# --- 1. SİSTEM VE API AYARLARI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

# API Versiyon Kilidi (404 hatasını engellemek için en güvenli yöntem)
os.environ["GOOGLE_API_VERSION"] = "v1"

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Secrets içinde API anahtarı bulunamadı!")
    st.stop()

# --- 2. GELİŞMİŞ DOSYA OKUMA MOTORU ---
def dosya_metnini_oku(yuklenen_dosya):
    try:
        # PDF Okuma
        if yuklenen_dosya.type == "application/pdf":
            reader = PdfReader(yuklenen_dosya)
            return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        
        # Word Okuma
        elif yuklenen_dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(yuklenen_dosya)
            return "\n".join([para.text for para in doc.paragraphs])
        
        # Excel Okuma
        elif "spreadsheetml" in yuklenen_dosya.type or "csv" in yuklenen_dosya.type:
            df = pd.read_excel(yuklenen_dosya) if "spreadsheet" in yuklenen_dosya.type else pd.read_csv(yuklenen_dosya)
            return f"Tablo Verisi:\n{df.to_string()}"
        
        # PowerPoint Okuma
        elif "presentationml" in yuklenen_dosya.type:
            prs = Presentation(yuklenen_dosya)
            metin = [shape.text for slide in prs.slides for shape in slide.shapes if hasattr(shape, "text")]
            return "\n".join(metin)
            
        return None
    except Exception as e:
        return f"Dosya okunurken hata oluştu: {e}"

# --- 3. MODEL YAPILANDIRMASI ---
@st.cache_resource
def model_getir():
    # En kararlı modeli doğrudan çağırıyoruz
    return genai.GenerativeModel('gemini-1.5-flash')

model_engine = model_getir()

# --- 4. TASARIM VE SIDEBAR ---
with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    # Logo kontrolü (Logo.png dosyan varsa görünür)
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=150)
    else:
        st.info("Logo.png bulunamadı.")
    
    st.divider()
    mod = st.selectbox("Asistan Modu", ["Eren AI Asistanı", "Akademik Destek", "Veli Bilgilendirme"])
    st.divider()
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Giriş Alanları
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        # Desteklenen tüm formatları ekledik
        yukle = st.file_uploader("Dosya Seç", type=['png','jpg','jpeg','pdf','docx','xlsx','pptx','csv'], label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya bir soru sorun...")

# Sohbeti Yazdır
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 5. YANIT VE DOSYA ANALİZ MANTIĞI ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("⚡ *İşleniyor...*")
        
        try:
            # Sistem talimatı
            prompt_parcalari = [f"Sen Eren AI'sın. Özel Eren Fen ve Teknoloji Lisesi asistanısın. Mod: {mod}. Kurumsal ve yardımcı bir dil kullan.", soru]
            
            # DOSYA İŞLEME (Kritik Değişiklik Burası)
            if yukle:
                if yukle.type.startswith("image/"):
                    # Görsel ise doğrudan ekle
                    prompt_parcalari.append(PIL.Image.open(yukle))
                else:
                    # Metin tabanlı döküman ise HER ZAMAN içeriği oku ve gönder
                    icerik_metni = dosya_metnini_oku(yukle)
                    if icerik_metni:
                        # Bu kısım dökümanın içeriğini 'görünmez' bir şekilde soruya ekler
                        prompt_parcalari.append(f"\n--- YÜKLENEN BELGE İÇERİĞİ ---\n{icerik_metni}")

            # Yanıtı üret
            yanit = model_engine.generate_content(prompt_parcalari)
            
            if yanit.text:
                placeholder.markdown(yanit.text)
                st.session_state.messages.append({"role": "assistant", "content": yanit.text})
            else:
                placeholder.error("Modelden yanıt alınamadı.")
                
        except Exception as e:
            placeholder.error(f"Sistem Hatası: {str(e)}")
