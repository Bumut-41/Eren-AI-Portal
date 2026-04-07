import streamlit as st
import google.generativeai as genai
import PIL.Image
import os
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document
from pptx import Presentation

# --- 1. SİSTEM KİLİDİ (HATAYI BİTİREN KRİTİK ADIM) ---
# v1beta hatasını engellemek için API versiyonunu en baştan v1'e sabitliyoruz.
os.environ["GOOGLE_API_VERSION"] = "v1"

# --- 2. SAYFA VE API YAPILANDIRMASI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı! Lütfen Secrets ayarlarını kontrol edin.")
    st.stop()

# Modeli en kararlı ismiyle çağırıyoruz
model_engine = genai.GenerativeModel('gemini-1.5-flash')

# --- 3. DÖKÜMAN OKUMA MOTORU (HİÇBİRİ SİLİNMEDİ) ---
def dosya_icerigini_getir(dosya):
    try:
        if dosya.type == "application/pdf":
            reader = PdfReader(dosya)
            return "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
        elif dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(dosya)
            return "\n".join([p.text for p in doc.paragraphs])
        elif dosya.type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
            prs = Presentation(dosya)
            metin = [shape.text for slide in prs.slides for shape in slide.shapes if hasattr(shape, "text")]
            return "\n".join(metin)
        elif dosya.type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "text/csv"]:
            df = pd.read_excel(dosya) if "spreadsheet" in dosya.type else pd.read_csv(dosya)
            return df.to_string()
        return None
    except Exception as e:
        return f"Okuma Hatası: {str(e)}"

# --- 4. ARAYÜZ TASARIMI (SOL MENÜ VE DOSYA YÜKLEME) ---
with st.sidebar:
    st.image("https://eren.k12.tr/logo.png", width=200) # Varsa logo URL'si
    st.title("🛡️ Eren AI Menü")
    mod = st.selectbox("Asistan Modu", ["Eren AI Asistanı", "Akademik Analiz", "Okul Bilgilendirme"])
    
    # Dosya yükleme alanı tekrar burada!
    st.subheader("📁 Belge Yükle")
    yukle = st.file_uploader(
        "Okul dökümanlarını buraya bırakın", 
        type=['pdf','docx','pptx','xlsx','csv','png','jpg','jpeg'],
        help="Word, Excel, PDF, PPT ve Görselleri destekler."
    )
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

st.title("🛡️ Eren AI Portalı")
st.markdown(f"**Şu anki Mod:** {mod} | **Sistem Durumu:** v1 Kararlı Sürüm")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Mesaj Geçmişini Göster
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 5. ANALİZ VE YANIT MOTORU ---
soru = st.chat_input("Eren AI'ya sorunuzu iletin...")

if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        cevap_alani = st.empty()
        cevap_alani.markdown("⚡ *Veriler işleniyor...*")
        
        try:
            # Temel talimatlar
            prompt_listesi = [
                f"Sen Özel Eren Fen ve Teknoloji Lisesi asistanısın. Okulla ilgili bilgilendirme yapıyorsun. Mod: {mod}.", 
                soru
            ]
            
            # Dosya varsa içeriğini ekle
            if yukle:
                if yukle.type.startswith("image/"):
                    prompt_listesi.append(PIL.Image.open(yukle))
                else:
                    icerik = dosya_icerigini_getir(yukle)
                    if icerik:
                        prompt_listesi.append(f"\nYÜKLENEN BELGE İÇERİĞİ:\n{icerik}")

            # Yanıt Üretme
            yanit = model_engine.generate_content(prompt_listesi)
            
            if yanit.text:
                cevap_alani.markdown(yanit.text)
                st.session_state.messages.append({"role": "assistant", "content": yanit.text})
        except Exception as e:
            cevap_alani.error(f"Sistem Hatası: {str(e)}")
