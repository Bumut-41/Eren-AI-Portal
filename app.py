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
st.set_page_config(page_title="Eren AI | Akademik Portal", page_icon="🛡️", layout="wide")

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

# --- SOL MENÜ (EKRAN GÖRÜNTÜSÜYLE BİREBİR) ---
def sidebar_ciz():
    with st.sidebar:
        try:
            st.image("Logo.png", use_container_width=True)
        except:
            st.subheader("🛡️ Eren AI")
        
        st.markdown("---")
        st.markdown("### **🛡️ Akademik Rehber v18.0**")
        st.success("**Eğitici Mod Aktif:** Her soru bir ders niteliğindedir.")
        
        st.info("""
        **Nasıl Kullanılır?**
        1. Ödev dosyanı aşağıdan yükle.
        2. Sorularını sor.
        3. Eren AI her soruyu derinlemesine analiz etsin.
        """)
        
        st.divider()
        st.caption("© 2026 Eren Eğitim Kurumları")

sidebar_ciz()

# --- SOHBET GEÇMİŞİ ---
if "messages" not in st.session_state:
    st.session_state.messages = []

chat_area = st.container()
with chat_area:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

# --- GİRİŞ PANELİ ---
with st.container():
    st.write("---")
    dosya = st.file_uploader("Dosya", type=['pdf','docx','xlsx','pptx','csv','png','jpg','jpeg'], 
                             key=f"uploader_{st.session_state.uploader_key}", 
                             label_visibility="collapsed")
    
    soru = st.chat_input("Akademik danışmanınıza sormak istediğiniz konuyu veya sorunuzu buraya giriniz...")

# --- AKADEMİK İŞLEMCİ ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with chat_area:
        with st.chat_message("user"):
            st.markdown(soru)

    with chat_area:
        with st.chat_message("assistant"):
            durum = st.status("🛡️ Eren AI Soruları Tek Tek Analiz Ediyor...")
            
            try:
                # --- GÜNCELLENMİŞ KURUMSAL VE SORU ODAKLI TALİMAT ---
                system_instruction = f"""
                Sen Özel Eren Fen ve Teknoloji Lisesi'nin resmi "Eren AI" akademik asistanı ve Baş Akademik Danışmanısın. {OKUL_BILGILERI}
                TEMEL KAYNAĞIN: https://eren.k12.tr/ web sitesindeki kurumsal bilgilerdir.

                KRİTİK ANALİZ PROTOKOLÜ (SORU SORU ANALİZ):
                1. GENELLEME YAPMA: Materyaldeki soruları özetleme. Her bir soruyu (Soru 1, Soru 2, Soru 3...) ayrı birer başlık altında incele.
                2. AKADEMİK DERİNLİK: Cevabı asla doğrudan verme. Sorunun mantığını temel bilimsel yasalarla (polinomiyal açılım, hücre teorisi, termodinamik vb.) açıkla. 
                3. BAĞLAM YÖNETİMİ: Yüklenen dosyadaki verileri Fen ve Teknoloji Lisesi standartlarında, teknik detayları atlamadan analiz et.
                4. KURUMSAL ÜSLUP: Profesyonel, teşvik edici ve çözüm odaklı bir dil kullan. Asla "Kütüphaneye bak" gibi yönlendirme metinleri ekleme.
                5. SOKRATİK YÖNTEM: Her sorunun analizinden sonra öğrenciye cevabı bulduracak kritik bir mantık sorusu sor.

                ANALİZ ŞABLONUN:
                - SORU [NO]: [KONU BAŞLIĞI]
                - Kavramsal Mantık: (Bilimsel açıklama)
                - Çözüm Stratejisi: (Adım adım rehberlik)
                - Kritik Düşünme Sorusu: (Öğrenciye yönelik etkileşim)
                """
                
                prompt_parts = [system_instruction, soru]
                
                if dosya:
                    if dosya.type.startswith("image/"):
                        prompt_parts.append(Image.open(dosya))
                    elif dosya.type == "application/pdf":
                        reader = PdfReader(dosya)
                        pdf_metni = "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
                        prompt_parts.append(f"ANALİZ EDİLECEK MATERYAL:\n{pdf_metni}")

                response = model.generate_content(prompt_parts)
                
                if response:
                    durum.update(label="✅ Soru Analizleri Hazır", state="complete")
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                    
                    if dosya:
                        st.session_state.uploader_key += 1
                        st.rerun() 
                    
            except Exception as e:
                durum.update(label="❌ Sistem Hatası", state="error")
                st.error(f"Teknik bir sorun oluştu: {str(e)}")
