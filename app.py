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
st.set_page_config(page_title="Eren AI | Akademik Portal", page_icon="🛡️", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı!")
    st.stop()

model = genai.GenerativeModel('gemini-3-flash-preview')

# --- ÖZEL EREN FEN VE TEKNOLOJİ LİSESİ BİLGİ TABANI ---
OKUL_BILGILERI = "Kurum: Özel Eren Fen ve Teknoloji Lisesi | Web: https://eren.k12.tr/"

# --- GELİŞMİŞ DOSYA ÜRETİM MOTORLARI (v14.4 - Şablonlu) ---

def metin_temizle(metin):
    metin = metin.replace('**', '').replace('*', '').replace('$', '')
    metin = metin.replace('\\times', 'x').replace('\\cdot', '.').replace('^{', '^').replace('}', '')
    return metin.strip()

def word_olustur(icerik):
    doc = Document()
    doc.add_heading('Özel Eren Fen ve Teknoloji Lisesi', 0)
    for line in icerik.split('\n'):
        temiz_line = line.replace('**', '').replace('$', '')
        if temiz_line.startswith('Slayt') or temiz_line.startswith('###'):
            doc.add_heading(temiz_line.replace('#', '').strip(), level=1)
        else:
            doc.add_paragraph(temiz_line)
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def pptx_olustur(icerik):
    try:
        # Şablon dosyasını kullan (template.pptx adıyla yüklendiği varsayılır)
        prs = Presentation("template.pptx")
    except:
        # Şablon bulunamazsa boş sunum aç
        prs = Presentation()
    
    parcalar = re.split(r'Slayt \d+:', icerik)
    
    for i, parca in enumerate(parcalar):
        if len(parca.strip()) < 10: continue
        
        # Şablondaki uygun düzeni seç (Genellikle 1. veya 2. layout)
        try:
            slide_layout = prs.slide_layouts[1] 
        except:
            slide_layout = prs.slide_layouts[0]
            
        slide = prs.slides.add_slide(slide_layout)
        satirlar = parca.strip().split('\n')
        
        # Başlık ve İçerik Yerleştirme
        if slide.shapes.title:
            slide.shapes.title.text = metin_temizle(satirlar[0])
        
        # İçeriği placeholders üzerinden ekle
        for shape in slide.placeholders:
            if shape.placeholder_format.type == 2: # Body/İçerik alanı
                tf = shape.text_frame
                tf.text = ""
                for satir in satirlar[1:]:
                    temiz_satir = metin_temizle(satir)
                    if temiz_satir:
                        p = tf.add_paragraph()
                        p.text = temiz_satir
                        p.level = 0

    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer

def excel_olustur(icerik):
    df = pd.DataFrame(icerik.split('\n'), columns=["Akademik İçerik"])
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    buffer.seek(0)
    return buffer

def gorsel_olustur(icerik, format="PNG"):
    img = Image.new('RGB', (800, 1200), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((20, 20), "Özel Eren Fen ve Teknoloji Lisesi", fill=(26, 95, 122))
    y = 70
    for satir in icerik.split('\n')[:40]:
        d.text((20, y), metin_temizle(satir)[:85], fill=(0, 0, 0))
        y += 25
    buffer = io.BytesIO()
    img.save(buffer, format=format)
    buffer.seek(0)
    return buffer

# --- ARAYÜZ VE SÜREÇ ---
with st.sidebar:
    try: st.image("Logo.png", use_container_width=True)
    except: st.subheader("🛡️ Eren AI")
    st.markdown("### **Kurumsal Çıktı Merkezi v14.4**")
    st.info("PowerPoint çıktıları artık okul şablonuna göre üretilmektedir.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        dosya = st.file_uploader("Dosya", type=['pdf','docx','xlsx','pptx','png','jpg'], key="v14_4_final", label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Ders notu veya şablonlu sunum hazırlatın...")

if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"): st.markdown(soru)

    with st.chat_message("assistant"):
        durum = st.status("🛡️ Eren AI Şablona Uygun İçerik Üretiyor...")
        try:
            system_instruction = f"Sen Özel Eren Fen ve Teknoloji Lisesi asistanısın. {OKUL_BILGILERI} Sunum taleplerinde 'Slayt 1:', 'Slayt 2:' formatını kullan."
            response = model.generate_content([system_instruction, soru])
            
            if response:
                durum.update(label="✅ Şablonlu Dosyalar Hazır", state="complete")
                st.markdown(response.text)
                
                st.divider()
                st.write("📥 **Kurumsal Dosyalar:**")
                col1, col2, col3, col4 = st.columns(4)
                with col1: st.download_button("📄 Word", data=word_olustur(response.text), file_name="Eren_AI_Not.docx")
                with col2: st.download_button("📊 Kurumsal Sunum", data=pptx_olustur(response.text), file_name="Eren_AI_Sablonlu_Sunum.pptx")
                with col3: st.download_button("📈 Excel", data=excel_olustur(response.text), file_name="Eren_AI_Tablo.xlsx")
                with col4: st.download_button("🖼️ PNG", data=gorsel_olustur(response.text, "PNG"), file_name="Eren_AI_Gorsel.png")

                st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Hata: {e}")
