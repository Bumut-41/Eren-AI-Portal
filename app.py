import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from PIL import Image
import pdf2image
import pandas as pd
from docx import Document
from pptx import Presentation
import io

# --- SİSTEM AYARLARI ---
st.set_page_config(page_title="Eren AI | Akademik Portalı", page_icon="🛡️", layout="wide")

# API Yapılandırması
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı eksik!")
    st.stop()

# --- MODEL (Gemini 3 Flash) ---
model = genai.GenerativeModel('gemini-3-flash-preview')

# --- ÖZEL EREN FEN VE TEKNOLOJİ LİSESİ BİLGİ TABANI ---
# Web sitesinden alınan temel bilgiler buraya "Context" olarak eklenir.
OKUL_BILGILERI = """
Özel Eren Fen ve Teknoloji Lisesi Bilgi Notları:
- Vizyon: Bilim ve teknolojide öncü, akademik dürüstlüğe sahip bireyler yetiştirmek.
- İletişim: https://eren.k12.tr/
- Odak: Fen bilimleri, ileri teknoloji, mühendislik ve akademik başarı.
- Kullanıcılar: Sadece Özel Eren Fen ve Teknoloji Lisesi öğretmen ve öğrencilerine hizmet verir.
- Görev: Öğrencileri akademik araştırmalarda, öğretmenleri ise materyal hazırlığında asiste etmek.
"""

# --- DOSYA İŞLEME FONKSİYONLARI ---
def metin_ayikla(dosya):
    try:
        if dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return "\n".join([p.text for p in Document(dosya).paragraphs])
        elif "spreadsheet" in dosya.type or "csv" in dosya.type:
            df = pd.read_excel(dosya) if "spreadsheet" in dosya.type else pd.read_csv(dosya)
            return f"Tablo Verileri:\n{df.to_string()}"
        elif "presentationml" in dosya.type:
            prs = Presentation(dosya)
            return "\n".join([shape.text for slide in prs.slides for shape in slide.shapes if hasattr(shape, "text")])
        return None
    except Exception as e:
        return f"Dosya Okuma Hatası: {e}"

# --- ARAYÜZ (Kurumsal Tasarım) ---
with st.sidebar:
    st.image("https://eren.k12.tr/wp-content/uploads/2021/05/eren-logo.png", width=150) # Varsa logo linki
    st.title("🛡️ Eren AI")
    st.markdown("### **Akademik Destek Sistemi**")
    st.info("Bu platform Özel Eren Fen ve Teknoloji Lisesi öğrencileri ve öğretmenleri için özel olarak geliştirilmiştir.")
    st.divider()
    mod = st.selectbox("Asistan Modu", ["Döküman Analizi", "Genel Akademik Asistan", "Sınav Hazırlık Modu"])
    st.divider()
    st.caption("© 2026 Eren Eğitim Kurumları")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Giriş Paneli
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        dosya = st.file_uploader("Dosya Yükle", type=['pdf','docx','xlsx','pptx','csv','png','jpg','jpeg'], key="eren_final", label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Akademik sorunuzu buraya yazın...")

# --- ANA İŞLEMCİ ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        status_text = "🛡️ Eren AI Akademik Verileri İnceliyor..."
        durum = st.status(status_text)
        
        try:
            # SİSTEM PROMPT (Kişilik kazandırma)
            system_instruction = f"""
            Sen Eren AI'sın. Özel Eren Fen ve Teknoloji Lisesi'nin resmi akademik yapay zeka asistanısın.
            Amacın: Öğretmen ve öğrencilere akademik yolculuklarında yüksek seviyeli destek sağlamaktır.
            Dilin: Profesyonel, destekleyici, akademik ve nazik olmalı.
            Okul Bilgileri: {OKUL_BILGILERI}
            Eğer kullanıcı okul hakkında soru sorursa, yukarıdaki bilgileri ve eren.k12.tr adresini referans al.
            Öğrencilere çözüm odaklı, öğretmenlere ise verimlilik odaklı yanıtlar ver.
            """
            
            icerik_listesi = [system_instruction, f"Kullanıcı Modu: {mod}", soru]
            
            if dosya:
                if dosya.type.startswith("image/"):
                    icerik_listesi.append(Image.open(dosya))
                elif dosya.type == "application/pdf":
                    reader = PdfReader(dosya)
                    pdf_metni = "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
                    if len(pdf_metni.strip()) > 50:
                        icerik_listesi.append(f"Yüklenen PDF İçeriği:\n{pdf_metni}")
                    else:
                        dosya.seek(0)
                        sayfalar = pdf2image.convert_from_bytes(dosya.read())
                        icerik_listesi.extend(sayfalar[:3]) # İlk 3 sayfa görsel olarak
                else:
                    ek_metin = metin_ayikla(dosya)
                    if ek_metin: icerik_listesi.append(f"Yüklenen Belge İçeriği:\n{ek_metin}")

            # Yanıt Üretimi
            response = model.generate_content(icerik_listesi)
            
            if response.text:
                durum.update(label="✅ Analiz Tamamlandı", state="complete")
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
        except Exception as e:
            durum.update(label="❌ İşlem Kesildi", state="error")
            st.error(f"Eren AI şu an yanıt veremiyor: {str(e)}")
