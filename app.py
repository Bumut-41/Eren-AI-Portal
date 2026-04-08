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
    st.error("API Anahtarı bulunamadı!")
    st.stop()

model = genai.GenerativeModel('gemini-3-flash-preview')

# --- ÖZEL EREN FEN VE TEKNOLOJİ LİSESİ BİLGİ TABANI ---
OKUL_BILGILERI = "Kurum: Özel Eren Fen ve Teknoloji Lisesi | Web: https://eren.k12.tr/"

# --- GELİŞMİŞ DOSYA ÜRETİM MOTORLARI (v15.0) ---

def metin_temizle(metin):
    # Markdown ve LaTeX sembollerini temizler
    metin = re.sub(r'\*\*|\$|\*', '', metin)
    metin = metin.replace('\\times', 'x').replace('\\cdot', '.').replace('^{', '^').replace('}', '')
    return metin.strip()

def word_olustur(icerik):
    doc = Document()
    doc.add_heading('Özel Eren Fen ve Teknoloji Lisesi', 0)
    for line in icerik.split('\n'):
        if line.strip():
            doc.add_paragraph(metin_temizle(line))
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def pptx_olustur(icerik):
    try:
        # Şablonu yükle ve içindeki eski slaytları temizle
        prs = Presentation("template.pptx")
        xml_slides = prs.slides._sldIdLst
        for s in list(xml_slides):
            xml_slides.remove(s)
    except:
        prs = Presentation()
    
    parcalar = re.split(r'Slayt \d+:', icerik)
    
    for parca in parcalar:
        if len(parca.strip()) < 10: continue
        
        # Şablondaki 'İçerik' düzenini kullan (Genellikle index 1)
        try:
            slide_layout = prs.slide_layouts[1]
        except:
            slide_layout = prs.slide_layouts[0]
            
        slide = prs.slides.add_slide(slide_layout)
        satirlar = parca.strip().split('\n')
        
        # Başlık Yerleşimi
        if slide.shapes.title:
            slide.shapes.title.text = metin_temizle(satirlar[0])
        
        # Metin Yerleşimi (Placeholder kontrolü ile)
        for shape in slide.placeholders:
            if shape.placeholder_format.type == 2: # Body/Metin alanı
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

# --- DOSYA OKUMA ---
def metin_ayikla(dosya):
    try:
        if dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return "\n".join([p.text for p in Document(dosya).paragraphs])
        elif "spreadsheet" in dosya.type or "csv" in dosya.type:
            df = pd.read_excel(dosya) if "spreadsheet" in dosya.type else pd.read_csv(dosya)
            return f"TABLO VERİSİ:\n{df.to_string()}"
        return None
    except Exception as e:
        return f"Hata: {e}"

# --- ARAYÜZ ---
with st.sidebar:
    try: st.image("Logo.png", use_container_width=True)
    except: st.subheader("🛡️ Eren AI")
    st.markdown("### **Kurumsal Portal v15.0**")
    st.info("Tam özellikler aktif: Dosya Analizi + Şablonlu Sunum")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- GİRİŞ PANELİ (DOSYA YÜKLEME DAHİL) ---
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        dosya = st.file_uploader("Dosya", type=['pdf','docx','xlsx','pptx','png','jpg'], key="v15_main")
    with c2:
        soru = st.chat_input("Ders notu veya sunum isteyin...")

if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"): st.markdown(soru)

    with st.chat_message("assistant"):
        durum = st.status("🛡️ Eren AI Analiz Yapıyor...")
        try:
            prompt_parts = [f"Sen Özel Eren Fen ve Teknoloji Lisesi asistanısın. {OKUL_BILGILERI} Sunumlarda 'Slayt X:' formatını kullan.", soru]
            
            if dosya:
                if dosya.type.startswith("image/"):
                    prompt_parts.append(Image.open(dosya))
                elif dosya.type == "application/pdf":
                    reader = PdfReader(dosya)
                    prompt_parts.append(f"DOSYA İÇERİĞİ:\n" + "\n".join([p.extract_text() for p in reader.pages]))
                else:
                    ek_metin = metin_ayikla(dosya)
                    if ek_metin: prompt_parts.append(ek_metin)

            response = model.generate_content(prompt_parts)
            
            if response:
                durum.update(label="✅ İşlem Tamamlandı", state="complete")
                st.markdown(response.text)
                
                st.divider()
                col1, col2, col3 = st.columns(3)
                with col1: st.download_button("📊 Kurumsal Sunum", data=pptx_olustur(response.text), file_name="Eren_AI_Sunum.pptx")
                with col2: st.download_button("📄 Word Notu", data=word_olustur(response.text), file_name="Eren_AI_Notlar.docx")
                with col3: st.download_button("📈 Excel Veri", data=excel_olustur(response.text), file_name="Eren_AI_Tablo.xlsx")

                st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Sistem hatası: {e}")
