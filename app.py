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
    st.error("API Anahtarı eksik! Lütfen Streamlit Cloud ayarlarını kontrol edin.")
    st.stop()

# --- MODEL ---
model = genai.GenerativeModel('gemini-3-flash-preview')

# --- ÖZEL EREN FEN VE TEKNOLOJİ LİSESİ DERİN BİLGİ TABANI ---
OKUL_BILGILERI = """
Kurum: Özel Eren Fen ve Teknoloji Lisesi
Web Sitesi: https://eren.k12.tr/

Akademik Misyon: 
Öğrencileri sadece bilgi tüketen değil, teknoloji üreten liderler olarak yetiştirir. 
Eren AI, bu ekosistemin bir parçası olarak akademik dürüstlük ve teknolojik inovasyon odaklı hizmet verir.

Eğitim Odağı: İleri düzey Fen Bilimleri, Robotik, Yazılım ve İnovasyon projeleri (TÜBİTAK, Teknofest).
Vizyon: Atatürk ilke ve inkılaplarına bağlı, dünya ile rekabet edebilecek bilim insanları yetiştirmek.
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

# --- SOL MENÜ (SIDEBAR) TASARIMI ---
with st.sidebar:
    # GitHub deposundaki Logo.png dosyasını çağırıyoruz
    try:
        logo = Image.open("Logo.png")
        st.image(logo, use_container_width=True)
    except:
        st.error("Logo.png bulunamadı.")
    
    st.title("🛡️ Eren AI")
    st.markdown("### **Akademik Destek Sistemi**")
    st.info("Bu platform Özel Eren Fen ve Teknoloji Lisesi paydaşları için özel olarak geliştirilmiştir.")
    
    st.divider()
    # Talep üzerine asistan modu açılır kutusu kaldırıldı
    st.write("📌 **Durum:** Aktif")
    st.write("🎓 **Odak:** Akademik Analiz")
    st.divider()
    st.caption("© 2026 Eren Eğitim Kurumları")

# --- SOHBET GEÇMİŞİ ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- GİRİŞ ALANI ---
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        dosya = st.file_uploader("Dosya Yükle", type=['pdf','docx','xlsx','pptx','csv','png','jpg','jpeg'], key="eren_v11", label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya akademik sorunuzu iletin...")

# --- ANA İŞLEMCİ ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        durum = st.status("🛡️ Eren AI kurumsal verileri ve belgeleri inceliyor...")
        
        try:
            # SİSTEM TALİMATI
            system_instruction = f"""
            Sen Eren AI'sın. Özel Eren Fen ve Teknoloji Lisesi'nin resmi akademik asistanısın.
            Okul Bilgileri: {OKUL_BILGILERI}
            
            Görevin:
            1. Öğrencilere ve öğretmenlere akademik konularda asistanlık yapmak.
            2. Okul hakkında soru sorulduğunda eren.k12.tr sitesini ve yukarıdaki bilgileri baz alarak resmi bir dille cevap vermek.
            3. Yüklenen belgeleri analiz ederek özetlemek veya soruları yanıtlamak.
            
            Üslubun profesyonel, vizyoner ve her zaman Özel Eren Fen ve Teknoloji Lisesi'nin prestijine uygun olmalı.
            """
            
            prompt_parts = [system_instruction, soru]
            
            if dosya:
                if dosya.type.startswith("image/"):
                    prompt_parts.append(Image.open(dosya))
                elif dosya.type == "application/pdf":
                    reader = PdfReader(dosya)
                    pdf_metni = "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
                    if len(pdf_metni.strip()) > 50:
                        prompt_parts.append(f"Belge Metni:\n{pdf_metni}")
                    else:
                        dosya.seek(0)
                        sayfalar = pdf2image.convert_from_bytes(dosya.read())
                        prompt_parts.extend(sayfalar[:3])
                else:
                    ek_metin = metin_ayikla(dosya)
                    if ek_metin: prompt_parts.append(f"Belge İçeriği:\n{ek_metin}")

            response = model.generate_content(prompt_parts)
            
            if response:
                durum.update(label="✅ Analiz Tamamlandı", state="complete")
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
        except Exception as e:
            durum.update(label="❌ Bağlantı Kesildi", state="error")
            st.error(f"Bir hata oluştu: {str(e)}")
