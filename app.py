import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from PIL import Image
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

# --- KURUMSAL TABAN ---
OKUL_BILGILERI = "Kurum: Özel Eren Fen ve Teknoloji Lisesi | Web: https://eren.k12.tr/"

# --- SUNUM VE DOSYA MOTORLARI ---
def metin_temizle(metin):
    return re.sub(r'\*\*|\$|\*', '', metin).strip()

def pptx_olustur(icerik):
    try:
        prs = Presentation("template.pptx")
        while len(prs.slides) > 0:
            r_id = prs.slides._sldIdLst[0].rId
            prs.part.drop_rel(r_id)
            del prs.slides._sldIdLst[0]
    except:
        prs = Presentation()
    
    parcalar = re.split(r'Slayt \d+:', icerik)
    for parca in parcalar:
        if len(parca.strip()) < 10: continue
        layout = prs.slide_layouts[1] if len(prs.slide_layouts) > 1 else prs.slide_layouts[0]
        slide = prs.slides.add_slide(layout)
        satirlar = parca.strip().split('\n')
        if slide.shapes.title: slide.shapes.title.text = metin_temizle(satirlar[0])
        for shape in slide.placeholders:
            if shape.placeholder_format.type == 2:
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

# --- SIDEBAR ---
with st.sidebar:
    try: st.image("Logo.png", use_container_width=True)
    except: st.subheader("🛡️ Eren AI")
    st.markdown("### **Akademik Portal v15.6**")
    st.info("Mesaj alanı ve dosya yükleyici en alta taşındı.")
    st.divider()
    st.caption("© 2026 Eren Eğitim Kurumları")

# --- SOHBET GEÇMİŞİ (EKRANIN ÜSTÜNDE KALIR) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mesajları bir container içinde gösteriyoruz (Otomatik yukarı kayması için)
chat_placeholder = st.container()

with chat_placeholder:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if "file_link" in m: # Eğer mesajda bir indirme linki varsa tekrar göster
                st.info("Dosya çıktıları yukarıdaki analizde mevcuttur.")

# --- GİRİŞ PANELİ (SAYFANIN EN ALTINDA) ---
st.divider()
footer_container = st.container()

with footer_container:
    # Dosya yükleyiciyi mesaj kutusunun hemen üzerine koyuyoruz
    dosya = st.file_uploader("Analiz edilecek dosya", type=['pdf','docx','png','jpg','pptx'], label_visibility="collapsed")
    soru = st.chat_input("Eren AI'ya bir soru sorun veya dosyanızı analiz ettirin...")

if soru:
    # Kullanıcı mesajını ekrana bas ve hafızaya al
    st.session_state.messages.append({"role": "user", "content": soru})
    with chat_placeholder:
        with st.chat_message("user"):
            st.markdown(soru)

    with chat_placeholder:
        with st.chat_message("assistant"):
            durum = st.status("🛡️ Eren AI analiz yapıyor...")
            try:
                # Dosya okuma ve besleme hazırlığı
                besleme = [f"Sen Eren Fen ve Teknoloji Lisesi asistanısın. {OKUL_BILGILERI} Sunumlarda 'Slayt X: [Başlık]' yapısını kullan."]
                
                if dosya:
                    if dosya.type == "application/pdf":
                        pdf_text = "\n".join([p.extract_text() for p in PdfReader(dosya).pages if p.extract_text()])
                        besleme.append(f"DOSYA İÇERİĞİ:\n{pdf_text}")
                    elif dosya.type.startswith("image/"):
                        besleme.append(Image.open(dosya))
                
                besleme.append(soru)
                response = model.generate_content(besleme)
                
                if response:
                    durum.update(label="✅ Analiz Tamamlandı", state="complete")
                    st.markdown(response.text)
                    
                    # Çıktı Butonları
                    st.divider()
                    c1, c2 = st.columns(2)
                    with c1: st.download_button("📊 Kurumsal Sunum", data=pptx_olustur(response.text), file_name="Eren_AI_Sunum.pptx")
                    with c2: st.download_button("📄 Word Notu", data=io.BytesIO(response.text.encode()), file_name="Eren_AI_Not.txt")
                    
                    st.session_state.messages.append({"role": "assistant", "content": response.text, "file_link": True})
            
            except Exception as e:
                st.error(f"Sistem hatası: {e}")
