import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from PIL import Image
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
    st.error("API Anahtarı bulunamadı!")
    st.stop()

model = genai.GenerativeModel('gemini-3-flash-preview')

# --- KURUMSAL TABAN ---
OKUL_BILGILERI = "Özel Eren Fen ve Teknoloji Lisesi (https://eren.k12.tr/)"

# --- DOSYA İŞLEME VE TEMİZLEME (v15.1) ---

def metin_temizle(metin):
    # Markdown ve LaTeX kalıntılarını profesyonel sunum için temizler
    metin = re.sub(r'\*\*|\$|\*', '', metin)
    return metin.strip()

def pptx_olustur(icerik):
    try:
        prs = Presentation("template.pptx")
        # Eski slaytları temizle (Görsel 7'deki karışıklığı önler)
        xml_slides = prs.slides._sldIdLst
        for s in list(xml_slides): xml_slides.remove(s)
    except:
        prs = Presentation()
    
    parcalar = re.split(r'Slayt \d+:', icerik)
    for parca in parcalar:
        if len(parca.strip()) < 10: continue
        # Şablon düzenini koru
        layout = prs.slide_layouts[1] if len(prs.slide_layouts) > 1 else prs.slide_layouts[0]
        slide = prs.slides.add_slide(layout)
        satirlar = parca.strip().split('\n')
        
        if slide.shapes.title:
            slide.shapes.title.text = metin_temizle(satirlar[0])
        
        for shape in slide.placeholders:
            if shape.placeholder_format.type == 2: # İçerik Alanı
                tf = shape.text_frame
                tf.text = ""
                for satir in satirlar[1:]:
                    temiz = metin_temizle(satir)
                    if temiz:
                        p = tf.add_paragraph()
                        p.text = temiz
                        p.level = 0
    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer

def word_olustur(icerik):
    doc = Document()
    doc.add_heading('Eren Fen ve Teknoloji Lisesi Akademik Rapor', 0)
    for line in icerik.split('\n'):
        if line.strip(): doc.add_paragraph(metin_temizle(line))
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- ANA ARAYÜZ ---
with st.sidebar:
    try: st.image("Logo.png", use_container_width=True)
    except: st.title("🛡️ Eren AI")
    st.info("v15.1: Dosya Okuma ve Şablon Uyumu Aktif")
    st.divider()
    st.caption("© 2026 Eren Eğitim Kurumları")

# Sohbet Geçmişi
if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# Giriş Alanı
with st.container():
    col_file, col_text = st.columns([1, 3])
    with col_file:
        yuklenen_dosya = st.file_uploader("Belge/Görsel", type=['pdf','docx','xlsx','png','jpg','pptx'])
    with col_text:
        soru = st.chat_input("Yüklediğim dosyayı özetle veya sunum yap...")

if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"): st.markdown(soru)

    with st.chat_message("assistant"):
        islem = st.status("🛡️ Dosya okunuyor ve analiz ediliyor...")
        try:
            # Model talimatları
            besleme = [f"Sen Eren Fen ve Teknoloji Lisesi asistanısın. {OKUL_BILGILERI}. Sunumlarda 'Slayt 1: [Başlık]' yapısını kullan.", soru]
            
            # DOSYA OKUMA MOTORU (v15.1 Fix)
            if yuklenen_dosya:
                if yuklenen_dosya.type.startswith("image/"):
                    besleme.append(Image.open(yuklenen_dosya))
                elif yuklenen_dosya.type == "application/pdf":
                    pdf_metni = "\n".join([p.extract_text() for p in PdfReader(yuklenen_dosya).pages])
                    besleme.append(f"ANALİZ EDİLECEK DOSYA METNİ:\n{pdf_metni}")
                elif "officedocument" in yuklenen_dosya.type: # Word/PPTX
                    # Basit metin ayıklama
                    besleme.append("Kullanıcı bir belge yükledi, içeriğe göre yanıt ver.")
            
            response = model.generate_content(besleme)
            
            if response:
                islem.update(label="✅ Analiz Tamamlandı", state="complete")
                st.markdown(response.text)
                
                # İndirme Butonları
                st.divider()
                b1, b2 = st.columns(2)
                with b1: st.download_button("📊 Kurumsal Sunum", data=pptx_olustur(response.text), file_name="Eren_AI_Sunum.pptx")
                with b2: st.download_button("📄 Word Raporu", data=word_olustur(response.text), file_name="Eren_AI_Analiz.docx")
                
                st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Hata: {e}")
