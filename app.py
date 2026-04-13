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

# --- TEMİZLİK VE DÜZENLEME FONKSİYONU ---
def clean_academic_text(text):
    """Dökümanlara yazılacak metni LaTeX ve Markdown kalıntılarından temizler."""
    text = text.replace('$', '') # LaTeX işaretlerini kaldır
    text = text.replace('**', '') # Kalın yazım işaretlerini kaldır
    text = text.replace('*', '')  # Madde işaretlerini sadeleştir
    text = text.replace('\\times', 'x') # Matematik sembollerini sadeleştir
    text = text.replace('\\', '') # Ters eğik çizgileri kaldır
    return text

# --- TAM SAYFA DÖKÜMAN MOTORLARI ---

def create_word(text, topic):
    doc = Document()
    doc.add_heading('Özel Eren Fen ve Teknoloji Lisesi', 0)
    sections = re.split(r'##|###|Bölüm:', text)
    for section in sections:
        if section.strip():
            doc.add_heading('Akademik Analiz Birimi', level=1)
            doc.add_paragraph(clean_academic_text(section.strip()))
            doc.add_page_break() # Gerçek sayfa bölünmesi
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

def create_pdf(text):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    sections = re.split(r'##|###|Bölüm:', text)
    for section in sections:
        if section.strip():
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, txt="Ozel Eren Fen ve Teknoloji Lisesi", ln=True, align='C')
            pdf.ln(10)
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(0, 10, txt=clean_academic_text(section.strip()))
    return bytes(pdf.output())

def create_pptx(text, topic):
    prs = Presentation()
    sections = re.split(r'##|###|Bölüm:', text)
    for section in sections:
        if len(section.strip()) > 10:
            slide = prs.slides.add_slide(prs.slide_layouts[1])
            # Başlık ve gövdeyi ayır
            lines = section.strip().split('\n')
            slide.shapes.title.text = clean_academic_text(lines[0])
            content_text = clean_academic_text('\n'.join(lines[1:]))
            
            # Yazı tipini küçülterek sayfaya sığdır
            tf = slide.placeholders[1].text_frame
            tf.text = content_text[:1200]
            for paragraph in tf.paragraphs:
                paragraph.font.size = Pt(18)
    bio = io.BytesIO()
    prs.save(bio)
    return bio.getvalue()

# --- SOL MENÜ ---
with st.sidebar:
    if os.path.exists("Logo.png"):
        st.image("Logo.png", use_container_width=True)
    st.markdown("### **🛡️ Eren AI Education**")
    st.success("**Anayasal Mod Aktif**")
    st.markdown("---")
    st.info("**Sistem Rehberi:**\n1. Dosyayı yükle.\n2. Analizi başlat.\n3. Formatlı dökümanı indir.")

# --- ANA PANEL ---
st.title("🛡️ Akademik Müfredat ve Analiz Portalı")

with st.container(border=True):
    uploaded_file = st.file_uploader("Dosya Yükleme", type=['pdf','docx','xlsx','pptx','csv','png','jpg','jpeg'], label_visibility="collapsed")
    user_input = st.chat_input("Analiz için sorunuzu buraya yazın...")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.status("🔍 Tam Sayfa Döküman Hazırlanıyor...") as status:
            instruction = """Sen Eren AI'sın. Cevaplarını net '## Bölüm:' başlıklarıyla ayır. 
            Karmaşık LaTeX kodlarını sadece ekranda kullan, döküman motoru bunları temizleyecektir."""
            
            response = model.generate_content([instruction, user_input])
            full_text = response.text
            st.markdown(full_text)
            st.session_state.messages.append({"role": "assistant", "content": full_text})

            st.divider()
            st.write("### 📥 Temizlenmiş ve Düzenlenmiş Çıktılar")
            c1, c2, c3 = st.columns(3)
            c1.download_button("📄 Word (Tam Sayfa)", create_word(full_text, "Analiz"), "ErenAI.docx")
            c2.download_button("📕 PDF (Formatlı)", create_pdf(full_text), "ErenAI.pdf")
            c3.download_button("📽️ Sunum (Temiz Slayt)", create_pptx(full_text, "Sunum"), "ErenAI.pptx")
            status.update(label="✅ Akademik Çıktılar Hazır", state="complete")
