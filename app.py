import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from PIL import Image
import pdf2image
import pandas as pd
from docx import Document
from pptx import Presentation

# --- SİSTEM AYARLARI ---
st.set_page_config(page_title="Eren AI | Akademik Rehber", page_icon="🛡️", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı!")
    st.stop()

model = genai.GenerativeModel('gemini-3-flash-preview')

# --- ÖZEL EREN FEN VE TEKNOLOJİ LİSESİ BİLGİ TABANI ---
OKUL_BILGILERI = "Kurum: Özel Eren Fen ve Teknoloji Lisesi | Web: https://eren.k12.tr/"

# --- DOSYA TEMİZLEME SİSTEMİ ---
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

def metin_ayikla(dosya):
    try:
        if dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return "\n".join([p.text for p in Document(dosya).paragraphs])
        elif "spreadsheet" in dosya.type or "csv" in dosya.type:
            df = pd.read_excel(dosya) if "spreadsheet" in dosya.type else pd.read_csv(dosya)
            return f"VERİ SETİ:\n{df.to_string()}"
        elif "presentationml" in dosya.type:
            prs = Presentation(dosya)
            return "\n".join([shape.text for slide in prs.slides for shape in slide.shapes if hasattr(shape, "text")])
        return None
    except Exception as e:
        return f"Dosya Okuma Hatası: {e}"

# --- SOL MENÜ ---
with st.sidebar:
    try:
        st.image("Logo.png", use_container_width=True)
    except:
        st.subheader("🛡️ Eren AI")
    st.markdown("### **Akademik Rehber v17.0**")
    st.success("Eğitici Mod: Odak noktası cevap değil, öğrenmedir.")
    st.divider()
    st.caption("© 2026 Eren Eğitim Kurumları")

# --- SOHBET GEÇMİŞİ ---
if "messages" not in st.session_state:
    st.session_state.messages = []

chat_area = st.container()
with chat_area:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

# --- GİRİŞ PANELİ (ALTTA SABİT) ---
with st.container():
    st.write("---")
    dosya = st.file_uploader("Eğitilecek Dosya", type=['pdf','docx','xlsx','pptx','csv','png','jpg','jpeg'], 
                             key=f"uploader_{st.session_state.uploader_key}", 
                             label_visibility="collapsed")
    soru = st.chat_input("Konuyu anlamak için bir soru sorun veya dosyanızı analiz ettirin...")

# --- AKADEMİK İŞLEMCİ ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with chat_area:
        with st.chat_message("user"):
            st.markdown(soru)

    with chat_area:
        with st.chat_message("assistant"):
            durum = st.status("🛡️ Eren AI Akademik Analiz Başlatıyor...")
            
            try:
                # --- SOKRATİK EĞİTMEN TALİMATI ---
                system_instruction = f"""
                Sen Özel Eren Fen ve Teknoloji Lisesi'nin "Baş Akademik Rehberisin". {OKUL_BILGILERI}
                
                TEMEL FELSEFEN: Öğrenciye cevabı vermek yerine, cevabı bulmasını sağlayacak yolu öğretmek.
                
                NASIL DAVRANMALISIN:
                1. KAVRAMSAL ANLATIM: Bir soru sorulduğunda, sorudaki sayıları kullanmadan önce konunun mantığını (teorisini) açıkla.
                2. STRATEJİ BELİRLEME: "Bu soruyu çözmek için şu adımları izlemelisin" diyerek yol haritası sun.
                3. DERİNLİK: Fen ve Teknoloji Lisesi düzeyinde teknik terimleri kullanarak akademik derinlik sağla.
                4. ETKİLEŞİM: Anlatımın arasına "Buradaki mantığı anladın mı?" veya "Sence bir sonraki adım ne olmalı?" gibi sorular ekleyerek öğrenciyi aktif tut.
                5. KESİN YASAK: Cevapların sonuna otomatik kütüphane veya web sitesi yönlendirmesi ekleme.
                """
                
                prompt_parts = [system_instruction, soru]
                
                if dosya:
                    if dosya.type.startswith("image/"):
                        prompt_parts.append(Image.open(dosya))
                    elif dosya.type == "application/pdf":
                        reader = PdfReader(dosya)
                        pdf_metni = "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
                        prompt_parts.append(f"ÖĞRETİLECEK MATERYAL:\n{pdf_metni}")
                    else:
                        ek_metin = metin_ayikla(dosya)
                        if ek_metin: prompt_parts.append(f"ÖĞRETİLECEK MATERYAL:\n{ek_metin}")

                response = model.generate_content(prompt_parts)
                
                if response:
                    durum.update(label="✅ Anlatım Hazır", state="complete")
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                    
                    # İşlem sonrası dosya yükleyiciyi temizle
                    if dosya:
                        st.session_state.uploader_key += 1
                        st.rerun() 
                    
            except Exception as e:
                durum.update(label="❌ Hata", state="error")
                st.error(f"Sistem hatası: {str(e)}")
