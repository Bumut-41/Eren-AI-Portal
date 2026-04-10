import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from PIL import Image
import pdf2image
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

# --- SUNUM OLUŞTURMA MOTORU (Şablon Destekli) ---
def pptx_olustur(icerik):
    try:
        prs = Presentation("template.pptx")
        # Şablonu temizle
        while len(prs.slides) > 0:
            rId = prs.slides._sldIdLst[0].rId
            prs.part.drop_rel(rId)
            del prs.slides._sldIdLst[0]
    except:
        prs = Presentation()
    
    parcalar = re.split(r'Slayt \d+:', icerik)
    for parca in parcalar:
        if len(parca.strip()) < 10: continue
        layout = prs.slide_layouts[1] if len(prs.slide_layouts) > 1 else prs.slide_layouts[0]
        slide = prs.slides.add_slide(layout)
        satirlar = parca.strip().split('\n')
        
        # Temizleme ve Yerleştirme
        baslik = satirlar[0].replace("**", "").replace("*", "").strip()
        if slide.shapes.title: slide.shapes.title.text = baslik
        
        for shape in slide.placeholders:
            if shape.placeholder_format.type == 2:
                tf = shape.text_frame
                tf.text = ""
                for satir in satirlar[1:]:
                    temiz_satir = satir.replace("**", "").replace("*", "").strip()
                    if temiz_satir:
                        p = tf.add_paragraph()
                        p.text = temiz_satir
                        p.level = 0
    
    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer

def metin_ayikla(dosya):
    try:
        if dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return "\n".join([p.text for p in Document(dosya).paragraphs])
        elif "spreadsheet" in dosya.type or "csv" in dosya.type:
            df = pd.read_excel(dosya) if "spreadsheet" in dosya.type else pd.read_csv(dosya)
            return f"TABLO VERİSİ:\n{df.to_string()}"
        elif "presentationml" in dosya.type:
            prs = Presentation(dosya)
            return "\n".join([shape.text for slide in prs.slides for shape in slide.shapes if hasattr(shape, "text")])
        return None
    except Exception as e:
        return f"Dosya Okuma Hatası: {e}"

# --- SOL MENÜ ---
with st.sidebar:
    try: st.image("Logo.png", use_container_width=True)
    except: st.subheader("🛡️ Eren AI")
    st.markdown("### **Akademik Portal v15.7**")
    st.info("Stabil sürüm: Giriş alanları en alta taşındı.")
    st.divider()
    st.caption("© 2026 Eren Eğitim Kurumları")

# --- SOHBET GEÇMİŞİ (ÜST ALAN) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mesajları bir kap (container) içinde göster
chat_container = st.container()
with chat_container:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

# --- GİRİŞ PANELİ (EN ALT ALAN) ---
# Bu kısım sayfanın en altında sabit kalır
st.write("") # Boşluk
with st.container():
    # Dosya yükleyici ve chat input'u yan yana veya alt alta alabiliriz
    # Genelde dosya yükleyiciyi chat input'un hemen üstünde tutmak daha kullanışlıdır
    dosya = st.file_uploader("Dosya", type=['pdf','docx','xlsx','pptx','csv','png','jpg','jpeg'], key="eren_v15_7", label_visibility="collapsed")
    soru = st.chat_input("Mesajınızı buraya yazın...")

# --- AKILLI İŞLEMCİ ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with chat_container:
        with st.chat_message("user"):
            st.markdown(soru)

    with chat_container:
        with st.chat_message("assistant"):
            durum = st.status("🛡️ Eren AI düşünüyor...")
            try:
                system_instruction = f"""
                Sen Özel Eren Fen ve Teknoloji Lisesi'nin resmi "Eren AI" akademik asistanısın. {OKUL_BILGILERI}
                Sunum isteklerinde mutlaka 'Slayt 1:', 'Slayt 2:' formatını kullan.
                """
                
                prompt_parts = [system_instruction, soru]
                
                if dosya:
                    analiz_kelimeleri = ["dosya", "belge", "doküman", "özet", "listele", "tablo", "analiz", "oku", "yüklediğim", "quiz", "soru", "ödev", "sunum"]
                    if any(kelime in soru.lower() for kelime in analiz_kelimeleri):
                        if dosya.type.startswith("image/"):
                            prompt_parts.append(Image.open(dosya))
                        elif dosya.type == "application/pdf":
                            reader = PdfReader(dosya)
                            pdf_metni = "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
                            if len(pdf_metni.strip()) > 50:
                                prompt_parts.append(f"İLGİLİ DOSYA İÇERİĞİ:\n{pdf_metni}")
                            else:
                                dosya.seek(0)
                                prompt_parts.extend(pdf2image.convert_from_bytes(dosya.read())[:5])
                        else:
                            ek_metin = metin_ayikla(dosya)
                            if ek_metin: prompt_parts.append(f"İLGİLİ DOSYA İÇERİĞİ:\n{ek_metin}")

                response = model.generate_content(prompt_parts)
                
                if response:
                    durum.update(label="✅ Hazır", state="complete")
                    st.markdown(response.text)
                    
                    # Eğer sunum hazırlandıysa indirme butonu göster
                    if "Slayt 1" in response.text:
                        st.divider()
                        st.download_button("📊 Kurumsal Sunumu İndir", 
                                         data=pptx_olustur(response.text), 
                                         file_name="Eren_AI_Sunum.pptx")
                    
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                    
            except Exception as e:
                durum.update(label="❌ Hata", state="error")
                st.error(f"Sistem hatası: {str(e)}")
