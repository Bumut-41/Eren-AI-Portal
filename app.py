import streamlit as st
import google.generativeai as genai
import io
import datetime
import os
import re

# --- DÖKÜMAN KÜTÜPHANELERİ ---
from docx import Document 
from pptx import Presentation 
from fpdf import FPDF 

# --- SİSTEM AYARLARI ---
st.set_page_config(page_title="Eren AI | Akademik Portal", page_icon="🛡️", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı!")
    st.stop()

model = genai.GenerativeModel('gemini-3-flash-preview')

# --- KARAKTER VE METİN DÜZENLEME ---
def tr_fix(text):
    chars = {'İ': 'I', 'ı': 'i', 'Ş': 'S', 'ş': 's', 'Ğ': 'G', 'ğ': 'g', 'ç': 'c', 'Ç': 'C', 'ö': 'o', 'Ö': 'O', 'ü': 'u', 'Ü': 'U'}
    for search, replace in chars.items():
        text = text.replace(search, replace)
    return text

def clean_academic_text(text):
    text = text.replace('$', '').replace('**', '').replace('*', '-')
    text = text.replace('\\times', 'x').replace('\\', '')
    return text

# --- GARANTİLİ DOSYA ÜRETİM MOTORLARI ---

def create_pdf_bytes(text):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    sections = re.split(r'##|###|Slayt \d+:|Bölüm:', text)
    
    for section in sections:
        if section.strip():
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, txt="Ozel Eren Fen ve Teknoloji Lisesi", ln=True, align='C')
            pdf.ln(10)
            pdf.set_font("Arial", size=12)
            safe_content = tr_fix(clean_academic_text(section.strip()))
            pdf.multi_cell(0, 10, txt=safe_content)
    
    # PDF verisini ham bayt dizisi olarak döndürür
    return pdf.output(dest='S').encode('latin-1')

def create_word_bytes(text):
    doc = Document()
    doc.add_heading('Özel Eren Fen ve Teknoloji Lisesi', 0)
    sections = re.split(r'##|###|Slayt \d+:|Bölüm:', text)
    for section in sections:
        if section.strip():
            doc.add_paragraph(clean_academic_text(section.strip()))
            doc.add_page_break()
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

def create_pptx_bytes(text):
    prs = Presentation()
    sections = re.split(r'##|###|Slayt \d+:|Bölüm:', text)
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

# --- SOL MENÜ ---
with st.sidebar:
    st.image("https://raw.githubusercontent.com/eren-ai/portal/main/logo.png", use_container_width=True) # Logo yolu örnektir
    st.markdown("### **🛡️ Eren AI Education**")
    st.success("**Anayasal Mod Aktif**")
    st.divider()
    st.info("**Rehber:** Analiz bittikten sonra aşağıdaki butonlar aktifleşecektir.")

# --- ANA PANEL ---
st.title("🛡️ Akademik Müfredat ve Analiz Portalı")

with st.container(border=True):
    uploaded_file = st.file_uploader("Dosya Yükleme", type=['pdf','docx','xlsx','pptx','csv','png','jpg','jpeg'], label_visibility="collapsed")
    user_input = st.chat_input("Optik veya Arduino hakkında sorunuzu yazın...")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.status("🔍 Dosya Yapılandırılıyor...") as status:
            response = model.generate_content([f"Sen Eren AI'sın. İçeriği Slayt 1, Slayt 2 şeklinde bölümlere ayır.", user_input])
            full_text = response.text
            st.markdown(full_text)
            st.session_state.messages.append({"role": "assistant", "content": full_text})

            st.divider()
            st.write("### 📥 Akademik Çıktı Merkezi")
            c1, c2, c3 = st.columns(3)
            
            # Veriler ham bayt (getvalue) olarak butona teslim ediliyor
            c1.download_button("📄 Word Fasikül", create_word_bytes(full_text), "ErenAI_Rapor.docx")
            c2.download_button("📕 PDF Döküman", create_pdf_bytes(full_text), "ErenAI_Rapor.pdf", mime="application/pdf")
            c3.download_button("📽️ PPTX Sunum", create_pptx_bytes(full_text), "ErenAI_Sunum.pptx")
            status.update(label="✅ Dosyalar Oluşturuldu", state="complete")
