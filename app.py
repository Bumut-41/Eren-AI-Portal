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

def metin_temizle(metin):
    # LaTeX ve Markdown kirliliğini sunum için temizler
    metin = re.sub(r'\*\*|\$|\*', '', metin)
    return metin.strip()

def pptx_olustur(icerik):
    try:
        prs = Presentation("template.pptx")
        # Mevcut tüm slaytları silerek şablonu sıfırla (Görsel 7 karmaşasını önler)
        while len(prs.slides) > 0:
            r_id = prs.slides._sldIdLst[0].rId
            prs.part.drop_rel(r_id)
            del prs.slides._sldIdLst[0]
    except:
        prs = Presentation()
    
    parcalar = re.split(r'Slayt \d+:', icerik)
    for parca in parcalar:
        if len(parca.strip()) < 10: continue
        
        # Tasarımlı boş sayfa ekle
        layout = prs.slide_layouts[1] if len(prs.slide_layouts) > 1 else prs.slide_layouts[0]
        slide = prs.slides.add_slide(layout)
        satirlar = parca.strip().split('\n')
        
        if slide.shapes.title:
            slide.shapes.title.text = metin_temizle(satirlar[0])
        
        for shape in slide.placeholders:
            if shape.placeholder_format.type == 2: # İçerik kutusu
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
    doc.add_heading('Eren AI Akademik Rapor', 0)
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
    st.info("v15.3: Kararlı Dosya Okuma Motoru")

if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# Giriş Alanı
with st.container():
    yuklenen_dosya = st.file_uploader("Belge/Görsel Yükle", type=['pdf','docx','xlsx','png','jpg','pptx'])
    soru = st.chat_input("Dosyayı özetle veya sunum yap...")

if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"): st.markdown(soru)

    with st.chat_message("assistant"):
        islem = st.status("🛡️ Eren AI dosyayı analiz ediyor...")
        try:
            # Model besleme listesi
            besleme = [f"Sen Eren Fen ve Teknoloji Lisesi asistanısın. {OKUL_BILGILERI}. Sunumlarda 'Slayt X: [Başlık]' yapısını kullan."]
            
            # --- DOSYA OKUMA VE BESLEME ---
            if yuklenen_dosya:
                if yuklenen_dosya.type.startswith("image/"):
                    besleme.append(Image.open(yuklenen_dosya))
                elif yuklenen_dosya.type == "application/pdf":
                    pdf_metni = ""
                    for sayfa in PdfReader(yuklenen_dosya).pages:
                        pdf_metni += sayfa.extract_text() + "\n"
                    besleme.append(f"ANALİZ EDİLECEK METİN:\n{pdf_metni}")
            
            besleme.append(f"Kullanıcı Sorusu: {soru}")
            response = model.generate_content(besleme)
            
            if response:
                islem.update(label="✅ Analiz Tamamlandı", state="complete")
                st.markdown(response.text)
                st.divider()
                col1, col2 = st.columns(2)
                with col1: st.download_button("📊 Sunumu İndir", data=pptx_olustur(response.text), file_name="Eren_AI_Sunum.pptx")
                with col2: st.download_button("📄 Word İndir", data=word_olustur(response.text), file_name="Eren_AI_Rapor.docx")
                st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Sistem hatası: {e}")
