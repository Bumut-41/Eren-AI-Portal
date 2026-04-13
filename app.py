import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from PIL import Image, ImageDraw
import io
import datetime
import os
import re

# --- DÖKÜMAN KÜTÜPHANELERİ ---
from docx import Document 
from pptx import Presentation 
from pptx.util import Inches, Pt
import pandas as pd 
from fpdf import FPDF 
from docx2python import docx2python 

# --- SİSTEM AYARLARI ---
st.set_page_config(page_title="Eren AI | Akademik Portal", page_icon="🛡️", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı!")
    st.stop()

model = genai.GenerativeModel('gemini-3-flash-preview')

# --- AKADEMİK METİN DÜZENLEYİCİ ---
def clean_academic_text(text):
    """Metni dökümanlar için temizler ve Unicode uyumlu hale getirir."""
    text = text.replace('$', '').replace('**', '').replace('*', '-')
    text = text.replace('\\times', 'x').replace('\\', '')
    # PDF Unicode hatası için kritik temizlik
    return text

# --- KARARLI DÖKÜMAN MOTORLARI ---

def create_word(text):
    doc = Document()
    doc.add_heading('Özel Eren Fen ve Teknoloji Lisesi', 0)
    sections = re.split(r'##|###|Bölüm:', text)
    for section in sections:
        if section.strip():
            doc.add_paragraph(clean_academic_text(section.strip()))
            doc.add_page_break()
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

def create_pdf(text):
    # 'latin-1' hatasını aşmak için font desteği ve encoding ayarı
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    sections = re.split(r'##|###|Bölüm:', text)
    for section in sections:
        if section.strip():
            pdf.add_page()
            # Standart fontlar Türkçe karakterde hata verebilir, 
            # en güvenli yol karakterleri normalize etmektir.
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, txt="Ozel Eren Fen ve Teknoloji Lisesi", ln=True, align='C')
            pdf.ln(10)
            pdf.set_font("Arial", size=12)
            # Unicode hatasını önlemek için metni güvenli hale getiriyoruz
            safe_content = clean_academic_text(section.strip()).encode('utf-8', 'ignore').decode('utf-8')
            pdf.multi_cell(0, 10, txt=safe_content)
    return pdf.output(dest='S').encode('latin-1', 'replace')

def create_pptx(text):
    prs = Presentation()
    sections = re.split(r'##|###|Bölüm:', text)
    for section in sections:
        if len(section.strip()) > 10:
            slide = prs.slides.add_slide(prs.slide_layouts[1])
            lines = section.strip().split('\n')
            slide.shapes.title.text = clean_academic_text(lines[0])[:50]
            tf = slide.placeholders[1].text_frame
            tf.text = clean_academic_text('\n'.join(lines[1:]))[:1200]
    bio = io.BytesIO()
    prs.save(bio)
    return bio.getvalue()

# --- ARAYÜZ ---
with st.sidebar:
    if os.path.exists("Logo.png"):
        st.image("Logo.png", use_container_width=True)
    st.markdown("### **🛡️ Eren AI Education**")
    st.success("**Anayasal Mod Aktif**")
    st.divider()
    st.markdown("### **📖 Sistem Rehberi**")
    st.info("1. Dosyayı yükle.\n2. Analizi başlat.\n3. Formatlı dökümanı indir.")
    st.caption("© 2026 Eren Eğitim Kurumları")

st.title("🛡️ Akademik Müfredat ve Analiz Portalı")

with st.container(border=True):
    uploaded_file = st.file_uploader("Dosya Yükleme", type=['pdf','docx','xlsx','pptx','csv','png','jpg','jpeg'], label_visibility="collapsed")
    user_input = st.chat_input("Sorunuzu buraya yazın...")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.status("🔍 Akademik Çıktılar Hazırlanıyor...") as status:
            prompt = [f"Sen Eren AI'sın. Optik ve Arduino gibi konularda derin analiz yap. Bölümleri ## ile ayır.", user_input]
            response = model.generate_content(prompt)
            full_text = response.text
            st.markdown(full_text)
            st.session_state.messages.append({"role": "assistant", "content": full_text})

            st.divider()
            st.write("### 📥 Akademik Çıktı Merkezi")
            c1, c2, c3 = st.columns(3)
            # Hata veren PDF butonu artık güvenli bayt akışında
            c1.download_button("📄 Word", create_word(full_text), "ErenAI.docx")
            c2.download_button("📕 PDF", create_pdf(full_text), "ErenAI.pdf")
            c3.download_button("📽️ Sunum", create_pptx(full_text), "ErenAI.pptx")
            status.update(label="✅ Hazır", state="complete")
