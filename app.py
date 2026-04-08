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
    st.error("API Anahtarı eksik! Lütfen Streamlit ayarlarını kontrol edin.")
    st.stop()

# --- MODEL (Gemini 3 Flash) ---
model = genai.GenerativeModel('gemini-3-flash-preview')

# --- ÖZEL EREN FEN VE TEKNOLOJİ LİSESİ DERİN BİLGİ TABANI ---
# Bu bilgiler okulun kurumsal yapısını derinlemesine temsil eder.
OKUL_BILGILERI = """
Kurum: Özel Eren Fen ve Teknoloji Lisesi
Web Sitesi: https://eren.k12.tr/

Akademik Misyon: 
Özel Eren Fen ve Teknoloji Lisesi, öğrencilerini sadece bilgi tüketen değil, teknoloji üreten liderler olarak yetiştirir. 
Eren AI, bu ekosistemin bir parçası olarak öğretmenlerin materyal hazırlığını hızlandırmak ve öğrencilerin akademik araştırmalarına rehberlik etmek için tasarlanmıştır.

Kurumsal Bilgiler:
- Eğitim Odağı: İleri düzey Fen Bilimleri, Robotik, Yazılım ve İnovasyon.
- Vizyon: Bilim ve teknolojide öncü, akademik dürüstlüğe sahip, dünya ile rekabet edebilecek bireyler yetiştirmek.
- Projeler: TÜBİTAK, Teknofest ve uluslararası bilim olimpiyatları temel önceliktir.
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

# --- ARAYÜZ ---
with st.sidebar:
    st.image("https://eren.k12.tr/wp-content/uploads/2021/05/eren-logo.png", width=150)
    st.title("🛡️ Eren AI")
    st.markdown("### **Akademik Destek Sistemi**")
    st.info("Bu platform Özel Eren Fen ve Teknoloji Lisesi paydaşları için özel olarak geliştirilmiştir.")
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
        dosya = st.file_uploader("Dosya Yükle", type=['pdf','docx','xlsx','pptx','csv','png','jpg','jpeg'], key="eren_final_v10", label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya akademik sorunuzu iletin...")

# --- ANA İŞLEMCİ ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        durum = st.status("🛡️ Eren AI akademik verileri derinlemesine inceliyor...")
        
        try:
            # SİSTEM TALİMATI (Kurumsal Kimlik)
            system_instruction = f"""
            Sen Eren AI'sın. Özel Eren Fen ve Teknoloji Lisesi'nin resmi akademik asistanısın.
            Görevin: Öğretmenleri akademik materyal üretiminde, öğrencileri ise öğrenme süreçlerinde asiste etmektir.
            Okul Bilgileri: {OKUL_BILGILERI}
            
            Önemli: Okul idaresi veya yapısı hakkında soru sorulduğunda, yukarıdaki bilgileri ve eren.k12.tr sitesini referans alarak kurumsal bir dille cevap ver. 
            Bilmediğin okul içi bilgiler için kullanıcıyı 'Hakkımızda' veya 'İletişim' sayfasına yönlendir.
            Dilin akademik, nazik ve çözüm odaklı olmalı.
            """
            
            prompt_parts = [system_instruction, f"Aktif Mod: {mod}", soru]
            
            if dosya:
                if dosya.type.startswith("image/"):
                    prompt_parts.append(Image.open(dosya))
                elif dosya.type == "application/pdf":
                    reader = PdfReader(dosya)
                    pdf_metni = "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
                    if len(pdf_metni.strip()) > 50:
                        prompt_parts.append(f"Analiz Edilecek PDF:\n{pdf_metni}")
                    else:
                        dosya.seek(0)
                        sayfalar = pdf2image.convert_from_bytes(dosya.read())
                        prompt_parts.extend(sayfalar[:5]) # İlk 5 sayfayı görsel olarak ekle
                else:
                    ek_metin = metin_ayikla(dosya)
                    if ek_metin: prompt_parts.append(f"Ek Belge İçeriği:\n{ek_metin}")

            response = model.generate_content(prompt_parts)
            
            if response:
                durum.update(label="✅ İşlem Tamamlandı", state="complete")
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
        except Exception as e:
            durum.update(label="❌ Bağlantı Hatası", state="error")
            st.error(f"Sistem hatası: {str(e)}")
