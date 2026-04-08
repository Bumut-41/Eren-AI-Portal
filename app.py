import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from PIL import Image
import pdf2image
import pandas as pd
from docx import Document
from pptx import Presentation
import io

# --- SİSTEM AYARLARI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı!")
    st.stop()

# Model: Çok modlu (Multimodal) analiz kapasitesi en yüksek sürüm
model = genai.GenerativeModel('gemini-3-flash-preview')

# --- DOSYA İŞLEME FONKSİYONLARI ---
def metin_ayikla(dosya):
    try:
        if dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return "\n".join([p.text for p in Document(dosya).paragraphs])
        
        elif "spreadsheetml" in dosya.type or "csv" in dosya.type:
            df = pd.read_excel(dosya) if "spreadsheet" in dosya.type else pd.read_csv(dosya)
            return f"Tablo Verileri:\n{df.to_string()}"
        
        elif "presentationml" in dosya.type:
            prs = Presentation(dosya)
            text = []
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text.append(shape.text)
            return "\n".join(text)
        return None
    except Exception as e:
        return f"Hata: {str(e)}"

# --- ARAYÜZ ---
with st.sidebar:
    st.title("🛡️ Eren AI")
    st.markdown("### Özel Eren Fen ve Teknoloji Lisesi")
    st.divider()
    mod = st.selectbox("Asistan Modu", ["Döküman Analizi", "Genel Asistan"])

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Giriş Paneli
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        dosya = st.file_uploader("Dosya", type=['pdf','docx','xlsx','pptx','csv','png','jpg','jpeg'], key="final_v3", label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya sorunuzu iletin...")

# --- ANA İŞLEMCİ ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        durum = st.status("🛡️ Eren AI dökümanı analiz ediyor...")
        
        try:
            # Prompt hazırlığı
            prompt_parcalari = [f"Sen Eren AI'sın. Mod: {mod}. Profesyonel bir okul asistanısın. Aşağıdaki verileri/görselleri incele ve soruyu yanıtla.", soru]
            
            if dosya:
                # 1. GÖRSELLER (JPG, PNG)
                if dosya.type.startswith("image/"):
                    prompt_parcalari.append(Image.open(dosya))
                    durum.write("🖼️ Görsel işleniyor...")
                
                # 2. PDF (Taranmış veya Dijital)
                elif dosya.type == "application/pdf":
                    # Önce metin okumayı dene
                    reader = PdfReader(dosya)
                    metin = "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
                    
                    if len(metin.strip()) > 50:
                        prompt_parcalari.append(f"PDF Metin İçeriği:\n{metin}")
                        durum.write("📄 PDF metin olarak okundu.")
                    else:
                        # Metin yoksa görselleştirmeye geç (OCR)
                        durum.write("👁️ PDF metin içermiyor, görsel analiz başlatılıyor...")
                        images = pdf2image.convert_from_bytes(dosya.read())
                        prompt_parcalari.extend(images[:5]) # İlk 5 sayfayı görsel olarak ekle
                
                # 3. DİĞER (Word, Excel, PPT)
                else:
                    icerik = metin_ayikla(dosya)
                    if icerik:
                        prompt_parcalari.append(f"Dosya İçeriği ({dosya.name}):\n{icerik}")
                        durum.write(f"📂 {dosya.name} başarıyla okundu.")

            # YANIT AL
            response = model.generate_content
