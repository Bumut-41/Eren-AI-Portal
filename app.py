import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from PIL import Image, ImageDraw
import pandas as pd
from docx import Document
from pptx import Presentation
import io
import re

# --- SİSTEM AYARLARI ---
st.set_page_config(page_title="Eren AI | Kurumsal Portal", page_icon="🛡️", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı eksik!")
    st.stop()

model = genai.GenerativeModel('gemini-3-flash-preview')

# --- KURUMSAL BİLGİLER ---
OKUL_BILGILERI = "Özel Eren Fen ve Teknoloji Lisesi | Akademik Asistan Sistemi"

# --- GELİŞMİŞ DOSYA ÜRETİM MOTORLARI (v14.5) ---

def metin_temizle(metin):
    # Markdown, LaTeX ve gereksiz karakter temizliği
    metin = re.sub(r'\*\*|\$|\*', '', metin)
    metin = metin.replace('\\times', 'x').replace('\\cdot', '.').replace('^{', '^').replace('}', '')
    return metin.strip()

def pptx_olustur(icerik):
    try:
        # Şablonu yükle
        prs = Presentation("template.pptx")
        # Şablondaki mevcut tüm slaytları sil (Karman çormanlığı önler)
        xml_slides = prs.slides._sldIdLst
        slides = list(xml_slides)
        for s in slides:
            xml_slides.remove(s)
    except:
        prs = Presentation()
    
    # İçeriği parçala
    parcalar = re.split(r'Slayt \d+:', icerik)
    
    for parca in parcalar:
        if len(parca.strip()) < 10: continue
        
        # Tasarımı koru: Şablondaki 2. düzeni (Başlık + İçerik) kullan
        try:
            slide_layout = prs.slide_layouts[1]
        except:
            slide_layout = prs.slide_layouts[0]
            
        slide = prs.slides.add_slide(slide_layout)
        satirlar = parca.strip().split('\n')
        
        # Başlığı yerleştir
        if slide.shapes.title:
            slide.shapes.title.text = metin_temizle(satirlar[0])
        
        # İçeriği yerleştir (Hizalamayı bozmadan sadece metin ekle)
        for shape in slide.placeholders:
            if shape.placeholder_format.type == 2: # İçerik kutusu
                tf = shape.text_frame
                tf.word_wrap = True # Otomatik satır kaydırma
                for i, satir in enumerate(satirlar[1:]):
                    temiz_satir = metin_temizle(satir)
                    if temiz_satir:
                        p = tf.add_paragraph() if i > 0 else tf.paragraphs[0]
                        p.text = temiz_satir
                        p.level = 0 # Madde işareti seviyesi

    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer

def word_olustur(icerik):
    doc = Document()
    doc.add_heading('Eren Fen ve Teknoloji Lisesi Akademik Notlar', 0)
    for line in icerik.split('\n'):
        if line.strip():
            doc.add_paragraph(metin_temizle(line))
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- ARAYÜZ ---
with st.sidebar:
    st.markdown("### **Kurumsal Portal v14.5**")
    st.success("Hizalama ve Şablon Temizliği Optimize Edildi.")
    st.divider()
    st.caption("Eren Eğitim Kurumları © 2026")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

soru = st.chat_input("Konuyu yazın, kurumsal sunumu hazırlayayım...")

if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"): st.markdown(soru)

    with st.chat_message("assistant"):
        durum = st.status("🛡️ Kurumsal şablon üzerine içerik işleniyor...")
        try:
            prompt = f"{OKUL_BILGILERI} Sunum hazırla. Format: Slayt 1: Başlık, Slayt 2: Başlık... \nSoru: {soru}"
            response = model.generate_content(prompt)
            
            if response:
                durum.update(label="✅ Sunum Hazır!", state="complete")
                st.markdown(response.text)
                
                st.divider()
                c1, c2 = st.columns(2)
                with c1:
                    st.download_button("📊 Kurumsal Sunumu İndir", 
                                     data=pptx_olustur(response.text), 
                                     file_name="Eren_K12_Sunum.pptx")
                with c2:
                    st.download_button("📄 Word Notlarını İndir", 
                                     data=word_olustur(response.text), 
                                     file_name="Akademik_Notlar.docx")

                st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Hata oluştu: {e}")
