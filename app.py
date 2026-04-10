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
st.set_page_config(page_title="Eren AI | Derin Akademik Rehber", page_icon="🛡️", layout="wide")

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

# --- SOL MENÜ (GARANTİLENMİŞ GÖRÜNÜM) ---
def sidebar_ciz():
    with st.sidebar:
        try:
            st.image("Logo.png", use_container_width=True)
        except:
            st.subheader("🛡️ Eren AI")
        
        st.markdown("---")
        st.markdown("### **🛡️ Akademik Rehber v17.6**")
        st.success("**Eğitici Mod Aktif:** Her soru bir ders niteliğindedir.")
        
        st.info("""
        **Nasıl Kullanılır?**
        1. Ödev dosyanı aşağıdan yükle.
        2. Sorularını sor.
        3. Eren AI her soruyu derinlemesine analiz etsin.
        """)
        
        st.divider()
        st.caption("© 2026 Eren Eğitim Kurumları")

# Menüyü çiz
sidebar_ciz()

# --- SOHBET GEÇMİŞİ ---
if "messages" not in st.session_state:
    st.session_state.messages = []

chat_area = st.container()
with chat_area:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

# --- GİRİŞ PANELİ (SAYFANIN EN ALTI) ---
with st.container():
    st.write("---")
    dosya = st.file_uploader("Ödev Dosyası", type=['pdf','docx','xlsx','pptx','csv','png','jpg','jpeg'], 
                             key=f"uploader_{st.session_state.uploader_key}", 
                             label_visibility="collapsed")
    soru = st.chat_input("Ödevimdeki tüm soruları en derin akademik düzeyde analiz etmeni istiyorum...")

# --- AKADEMİK İŞLEMCİ ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with chat_area:
        with st.chat_message("user"):
            st.markdown(soru)

    with chat_area:
        with st.chat_message("assistant"):
            durum = st.status("🛡️ Eren AI Derin Analiz Yapıyor...")
            
            try:
                # --- HER SORUYA ÖZEL DERİN ANALİZ TALİMATI ---
                system_instruction = f"""
                Sen Özel Eren Fen ve Teknoloji Lisesi'nin "Baş Akademik Rehberisin". {OKUL_BILGILERI}
                
                GÖREVİN: Öğrencinin yüklediği materyaldeki HER BİR SORUYU (Soru 1, Soru 2...) ayrı ayrı başlıklandırarak derinlemesine öğretmek.
                
                HER SORU İÇİN ANALİZ ŞABLONU:
                1. **Kavramsal Temel:** Sorunun merkezindeki konuyu (Örn: Enzimlerin çalışma prensibi) akademik olarak anlat.
                2. **Adım Adım Analiz:** Sorudaki öncülleri tek tek değerlendir, neden doğru veya yanlış olduklarını bilimsel kanıtlarla açıkla.
                3. **Strateji:** Bu tür sorularda hangi 'anahtar kelimelere' bakılması gerektiğini öğret.
                4. **Düşündürücü Soru:** Öğrenciye, öğrendiğini pekiştirecek Sokratik bir soru sor.
                
                Kısıtlama: Kurumsal yönlendirme metni ekleme. Cevabı sadece söyleme, buldur.
                """
                
                prompt_parts = [system_instruction, soru]
                
                if dosya:
                    if dosya.type.startswith("image/"):
                        prompt_parts.append(Image.open(dosya))
                    elif dosya.type == "application/pdf":
                        reader = PdfReader(dosya)
                        pdf_metni = "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
                        prompt_parts.append(f"ÖDEV İÇERİĞİ:\n{pdf_metni}")
                    else:
                        # Metin ayıklama fonksiyonu buraya entegre edilebilir
                        pass

                response = model.generate_content(prompt_parts)
                
                if response:
                    durum.update(label="✅ Derin Analiz Tamamlandı", state="complete")
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                    
                    if dosya:
                        st.session_state.uploader_key += 1
                        st.rerun() 
                    
            except Exception as e:
                durum.update(label="❌ Hata", state="error")
                st.error(f"Sistem hatası: {str(e)}")
