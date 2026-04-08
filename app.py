import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import pandas as pd
from docx import Document
from pptx import Presentation
from PIL import Image
import io

# --- SİSTEM AYARLARI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

# API Anahtarı
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı! Lütfen Secrets kısmını kontrol edin.")
    st.stop()

# --- GELİŞMİŞ DOSYA OKUMA MOTORU ---
def dosya_metne_donustur(dosya):
    try:
        # PDF Okuma
        if dosya.type == "application/pdf":
            reader = PdfReader(dosya)
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted: text += extracted + "\n"
            return text
        
        # Word Okuma
        elif dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(dosya)
            return "\n".join([p.text for p in doc.paragraphs])
        
        # PowerPoint Okuma
        elif "presentationml" in dosya.type:
            pptx = Presentation(dosya)
            text = ""
            for slide in pptx.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"): text += shape.text + "\n"
            return text
        
        # Excel veya CSV Okuma
        elif "spreadsheetml" in dosya.type or "csv" in dosya.type:
            df = pd.read_excel(dosya) if "spreadsheet" in dosya.type else pd.read_csv(dosya)
            return f"Tablo Verileri (İlk 50 Satır):\n{df.head(50).to_string()}"
            
        return None
    except Exception as e:
        return f"Hata: {str(e)}"

# --- MODEL YAPILANDIRMASI ---
# Listenizde mevcut olan Gemini 3 sürümünü kullanıyoruz
model = genai.GenerativeModel('gemini-3-flash-preview')

# --- ARAYÜZ ---
with st.sidebar:
    st.title("🛡️ Eren AI")
    st.markdown("### Özel Eren Fen ve Teknoloji Lisesi")
    st.divider()
    mod = st.selectbox("Asistan Modu", ["Genel Asistan", "Akademik Analiz", "Veli Rehberi"])

if "messages" not in st.session_state:
    st.session_state.messages = []

# Geçmiş mesajları göster
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Giriş Bölümü
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        yuklenen_dosya = st.file_uploader("Dosya", type=['pdf','docx','pptx','xlsx','csv','png','jpg','jpeg'], label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya sorunuzu iletin...")

# --- ANA İŞLEMCİ ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        cevap_alani = st.empty()
        cevap_alani.info("🛡️ Eren AI dökümanı okuyor...")
        
        try:
            # Temel talimat ve soru
            prompt_list = [f"Sen Eren AI'sın. Mod: {mod}. Profesyonel bir okul asistanısın.", soru]
            
            # Dosya varsa içeriği ayıkla ve soruya ekle
            if yuklenen_dosya:
                if yuklenen_dosya.type.startswith("image/"):
                    prompt_list.append(Image.open(yuklenen_dosya))
                else:
                    icerik = dosya_metne_donustur(yuklenen_dosya)
                    if icerik:
                        # DOSYAYI SORUNUN BAŞINA EKLEYEREK MODELİN GÖRMESİNİ SAĞLIYORUZ
                        belge_notu = f"\n\n--- KULLANICININ YÜKLEDİĞİ DOSYA İÇERİĞİ ---\n{icerik}\n----------------------------------\n"
                        prompt_list[1] = belge_notu + soru # Soruyu belge içeriğiyle birleştir

            # Yanıtı al
            response = model.generate_content(prompt_list)
            
            if response.text:
                cevap_alani.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            else:
                cevap_alani.warning("Dosya okundu ancak anlamlı bir metin bulunamadı.")
                
        except Exception as e:
            cevap_alani.error(f"Sistem Hatası: {str(e)}")
