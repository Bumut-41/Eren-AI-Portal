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
from pptx import Presentation as ReadPPTX 

# --- SİSTEM AYARLARI ---
st.set_page_config(page_title="Eren AI | Akademik Portal", page_icon="🛡️", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı!")
    st.stop()

model = genai.GenerativeModel('gemini-3-flash-preview')

# --- AKILLI DÖKÜMAN MOTORLARI (SAYFA BÖLMELİ) ---

def create_word(text, topic):
    doc = Document()
    doc.add_heading('Özel Eren Fen ve Teknoloji Lisesi', 0)
    # Metni bölümlere ayırarak Word'e ekle
    sections = text.split('##')
    for section in sections:
        if section.strip():
            doc.add_paragraph(section.strip())
            doc.add_page_break() # Her ana bölümden sonra yeni sayfa
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

def create_pdf(text):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Ozel Eren Fen ve Teknoloji Lisesi", ln=True, align='C')
    
    # Metni satır satır kontrol ederek ekle (Otomatik sayfa sonu fpdf2 ile sağlanır)
    safe_text = text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, txt=safe_text)
    return bytes(pdf.output())

def create_pptx(text, topic):
    prs = Presentation()
    
    # Kapak Slaytı
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = "Eren AI Akademik Sunumu"
    slide.placeholders[1].text = topic

    # İçeriği "Bölüm" veya "Soru" anahtar kelimelerine göre slaytlara böl
    # Görseldeki [Bölüm 1] gibi yapıları yakalar
    slides_content = re.split(r'###|##', text)
    
    for content in slides_content:
        if len(content.strip()) > 20: # Boş slaytları engelle
            slide = prs.slides.add_slide(prs.slide_layouts[1])
            # İlk satırı başlık yap, kalanı içerik
            lines = content.strip().split('\n')
            slide.shapes.title.text = lines[0][:50] 
            slide.placeholders[1].text = '\n'.join(lines[1:])[:1000] # Slayt kapasite sınırı

    bio = io.BytesIO()
    prs.save(bio)
    return bio.getvalue()

# --- ARAYÜZ (SOL MENÜ RESTORE EDİLDİ) ---
with st.sidebar:
    if os.path.exists("Logo.png"):
        st.image("Logo.png", use_container_width=True)
    st.markdown("### **🛡️ Eren AI Education**")
    st.success("**Anayasal Mod Aktif**")
    st.markdown("---")
    st.markdown("### **📖 Sistem Rehberi**")
    st.info("1. Dosyaları yükleyin.\n2. Soruları sorun.\n3. Bölümlere ayrılmış çıktıları indirin.")
    st.divider()
    st.caption("© 2026 Eren Eğitim Kurumları")

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
        with st.status("🔍 Çok Sayfalı Analiz Hazırlanıyor...") as status:
            # AI'ya çıktıları bölümlere ayırması için kesin talimat veriyoruz
            instruction = """Sen Eren AI'sın. Cevaplarını her zaman '## Bölüm' veya '## Soru' şeklinde net başlıklarla ayır. 
            Bu başlıklar döküman oluştururken yeni sayfa/slayt tetikleyicisi olacaktır."""
            
            response = model.generate_content([instruction, user_input])
            full_text = response.text
            st.markdown(full_text)
            st.session_state.messages.append({"role": "assistant", "content": full_text})

            st.divider()
            st.write("### 📥 Çok Sayfalı Akademik Çıktılar")
            c1, c2, c3 = st.columns(3)
            c1.download_button("📄 Word (Sayfa Bölmeli)", create_word(full_text, "Analiz"), "ErenAI_Rapor.docx")
            c2.download_button("📕 PDF (Düzenli)", create_pdf(full_text), "ErenAI_Rapor.pdf")
            c3.download_button("📽️ PPTX (Slayt Slayt)", create_pptx(full_text, "Sunum"), "ErenAI_Sunum.pptx")
            status.update(label="✅ Tüm Sayfalar Hazır", state="complete")
