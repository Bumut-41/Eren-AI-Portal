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

# API Yapılandırması
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı!")
    st.stop()

# Model Seçimi (Erişim sorunlarını gidermek için en stabil önizleme sürümü)
# Not: image_cc99a1 ve image_cca52b'deki hataları aşmak için bu model seçilmiştir.
model = genai.GenerativeModel('gemini-1.5-pro') 

# --- DOSYA İŞLEME FONKSİYONLARI ---
def metin_ayikla(dosya):
    try:
        # WORD (.docx)
        if dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(dosya)
            return "\n".join([p.text for p in doc.paragraphs])
        
        # EXCEL (.xlsx, .csv)
        elif "spreadsheetml" in dosya.type or "csv" in dosya.type:
            df = pd.read_excel(dosya) if "spreadsheet" in dosya.type else pd.read_csv(dosya)
            return f"Tablo Verileri:\n{df.to_string()}"
        
        # POWERPOINT (.pptx)
        elif "presentationml" in dosya.type:
            prs = Presentation(dosya)
            text_runs = []
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text_runs.append(shape.text)
            return "\n".join(text_runs)
        return None
    except Exception as e:
        return f"Dosya Okuma Hatası: {str(e)}"

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

# Giriş Alanı
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        uploaded_file = st.file_uploader("Dosya", type=['pdf','docx','xlsx','pptx','csv','png','jpg','jpeg'], key="eren_v4", label_visibility="collapsed")
    with c2:
        prompt = st.chat_input("Eren AI'ya sorunuzu iletin...")

# --- ANA MANTIK ---
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        status = st.status("🛡️ Eren AI dosyayı ve soruyu analiz ediyor...")
        
        try:
            # Model için içerik listesi oluştur
            content_to_send = [f"Sen Eren AI'sın. Mod: {mod}. Profesyonel bir okul asistanısın. Aşağıdaki verileri/görselleri incele ve soruyu yanıtla.", prompt]
            
            if uploaded_file:
                # 1. GÖRSELLER (JPG, PNG)
                if uploaded_file.type.startswith("image/"):
                    img = Image.open(uploaded_file)
                    content_to_send.append(img)
                    status.write("🖼️ Görsel başarıyla eklendi.")
                
                # 2. PDF İŞLEME
                elif uploaded_file.type == "application/pdf":
                    # Önce metin tabanlı okumayı dene
                    pdf_reader = PdfReader(uploaded_file)
                    pdf_text = "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
                    
                    if len(pdf_text.strip()) > 100: # Eğer yeterli metin varsa
                        content_to_send.append(f"PDF Metin İçeriği:\n{pdf_text}")
                        status.write("📄 PDF metin olarak okundu.")
                    else:
                        # Metin yoksa görselleştirmeye geç (Taranmış PDF çözümü - image_cd8a45)
                        status.write("👁️ PDF metin içermiyor, görsel analiz (OCR) başlatılıyor...")
                        pdf_images = pdf2image.convert_from_bytes(uploaded_file.read())
                        content_to
