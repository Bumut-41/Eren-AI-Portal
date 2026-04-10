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

# --- SOL MENÜ (KURUMSAL YAPI) ---
def sidebar_ciz():
    with st.sidebar:
        try:
            st.image("Logo.png", use_container_width=True)
        except:
            st.subheader("🛡️ Eren AI")
        
        st.markdown("---")
        st.markdown("### **🛡️ Akademik Rehber v19.0**")
        st.success("**Eğitici Mod Aktif:** Analitik ve derinlemesine öğrenme süreci.")
        
        st.info("""
        **Nasıl Kullanılır?**
        1. Ödev dosyanı yükle.
        2. Analiz edilmesini istediğin konuyu belirt.
        3. Eren AI her soruyu tek tek, derinlemesine analiz etsin.
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
    dosya = st.file_uploader("Dosya Yükleme", type=['pdf','docx','xlsx','pptx','csv','png','jpg','jpeg'], 
                             key=f"uploader_{st.session_state.uploader_key}", 
                             label_visibility="collapsed")
    
    # İstediğiniz kurumsal metin buraya eklendi
    soru = st.chat_input("Eren AI'a sormak istediğin soruyu bu alana girebilirsiniz.")

# --- AKADEMİK İŞLEMCİ ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with chat_area:
        with st.chat_message("user"):
            st.markdown(soru)

    with chat_area:
        with st.chat_message("assistant"):
            durum = st.status("🛡️ Eren AI Akademik İnceleme Başlatıyor...")
            
            try:
                # --- YENİLENMİŞ KİMLİK VE KESİN TALİMATLAR ---
                system_instruction = f"""
                Sen Eren AI, Özel Eren Fen ve Teknoloji Lisesi'nin Yapay Zekasısın. {OKUL_BILGILERI}
                
                KİMLİK TANIMIN: Cevaplarına başlarken "Eren AI, Özel Eren Fen ve Teknoloji Lisesi'nin Yapay Zekası olarak size hizmet ediyorum." ifadesini kullan. Asla "Baş Akademik Danışman" deme.

                KESİN ANALİZ KURALLARI:
                1. EKSİKSİZLİK: Yüklenen materyaldeki TÜM soruları tespit et. Hiçbir soruyu atlama.
                2. TEK TEK ANALİZ: Soruları gruplandırma. Her soru için ayrı bir başlık aç (Soru 1, Soru 2, Soru 3...).
                3. CEVAP VERME, ÖĞRET: Doğrudan "Cevap A" deme. Önce konunun bilimsel mantığını anlat, sonra şıkları analiz et ve öğrenciyi cevaba yönlendirecek bir soru sor.
                4. KURUMSAL ÜSLUP: eren.k12.tr vizyonuna uygun, profesyonel ve derin bir dil kullan. 
                5. GÜNCEL BİLGİ: Okul hakkındaki sorularda web sitesini referans al.
                6. YASAK: Cevapların sonuna otomatik kütüphane/web sitesi yönlendirme metni ekleme.

                ANALİZ ŞABLONU (Her Soru İçin):
                - SORU [No]: [Konu Başlığı]
                - Kavramsal Mantık: (Derin bilimsel açıklama)
                - Adım Adım Strateji: (Öğrencinin izlemesi gereken mantıksal yol)
                - Sokratik Soru: (Öğrencinin cevabı bulmasını sağlayacak yönlendirme)
                """
                
                prompt_parts = [system_instruction, soru]
                
                if dosya:
                    if dosya.type.startswith("image/"):
                        prompt_parts.append(Image.open(dosya))
                    elif dosya.type == "application/pdf":
                        reader = PdfReader(dosya)
                        pdf_metni = ""
                        for page in reader.pages:
                            text = page.extract_text()
                            if text: pdf_metni += text + "\n"
                        prompt_parts.append(f"ANALİZ EDİLECEK TÜM SORULAR:\n{pdf_metni}")
                    else:
                        # Diğer metin tabanlı dosyalar için veri ekleme
                        pass

                response = model.generate_content(prompt_parts)
                
                if response:
                    durum.update(label="✅ Analiz Tamamlandı", state="complete")
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                    
                    if dosya:
                        st.session_state.uploader_key += 1
                        st.rerun() 
                    
            except Exception as e:
                durum.update(label="❌ Hata", state="error")
                st.error(f"Sistem hatası: {str(e)}")
