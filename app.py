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

# --- SOL MENÜ (KURUMSAL VE SABİT) ---
def sidebar_ciz():
    with st.sidebar:
        try:
            st.image("Logo.png", use_container_width=True)
        except:
            st.subheader("🛡️ Eren AI")
        
        st.markdown("---")
        st.markdown("### **🛡️ Akademik Rehber v21.0**")
        st.success("**Anayasal Mod:** Her soru için bireysel ve derin analiz zorunludur.")
        
        st.info("""
        **Sistem İlkeleri:**
        1. Hiçbir soru atlanmaz.
        2. Her soru bir "mikro-ders" olarak işlenir.
        3. Doğrudan cevap verilmez, konu öğretilir.
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
    
    soru = st.chat_input("Eren AI'a sormak istediğin soruyu bu alana girebilirsiniz.")

# --- AKADEMİK İŞLEMCİ ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with chat_area:
        with st.chat_message("user"):
            st.markdown(soru)

    with chat_area:
        with st.chat_message("assistant"):
            durum = st.status("🛡️ Eren AI Akademik Müfredat Analizi Yapıyor...")
            
            try:
                # --- SİSTEMİN ANAYASASI VE DERİN TALİMATI ---
                system_instruction = f"""
                Sen Eren AI, Özel Eren Fen ve Teknoloji Lisesi'nin Yapay Zekasısın. {OKUL_BILGILERI}
                
                KİMLİK TANIMIN: Cevaplarına başlarken "Eren AI, Özel Eren Fen ve Teknoloji Lisesi'nin Yapay Zekası olarak size hizmet ediyorum." ifadesini kullan.

                🛡️ AKADEMİK ANAYASA (DEĞİŞTİRİLEMEZ MADDELER):
                MADDE 1: MATERYALDEKİ TÜM SORULARI EKSİKSİZ ANALİZ ET. Hiçbir soruyu atlama, özetleme veya geçiştirme.
                MADDE 2: HER SORUYA AYRI BAŞLIK AÇ. Karma anlatım yapma, her soru bir "mikro-ders" modülüdür.
                MADDE 3: DERİN KAVRAMSAL ANLATIM ZORUNLUDUR. Sadece çözüm yolu gösterme; konunun bilimsel arka planını, yasalarını ve akademik önemini genişçe anlat.
                MADDE 4: CEVAP VERMEK YASAKTIR. Şıkları analiz et ama doğru seçeneği söyleme; öğrenciyi oraya akademik çıkarımlarla ulaştır.
                MADDE 5: SOKRATİK ETKİLEŞİM. Her soru sonunda, o sorunun mantığını test eden bir karşı soru sor.

                ANALİZ DÜZENİN:
                ## [SORU NO VE KONU]
                ### 📚 Akademik ve Bilimsel Temeller
                [Konunun teorik, ansiklopedik ve fen lisesi düzeyindeki derin anlatımı.]
                
                ### 🔍 Analitik Çözümleme ve Strateji
                [Soru verilerinin, öncüllerinin ve şıklarının teknik analizi.]
                
                ### 💡 Sokratik Düşünme Köprüsü
                [Öğrenciye yönelik, bilgiyi pekiştirici derin soru.]
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
                        prompt_parts.append(f"ANALİZ EDİLECEK MATERYAL:\n{pdf_metni}")

                response = model.generate_content(prompt_parts)
                
                if response:
                    durum.update(label="✅ Anayasal Akademik Analiz Tamamlandı", state="complete")
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                    
                    if dosya:
                        st.session_state.uploader_key += 1
                        st.rerun() 
                    
            except Exception as e:
                durum.update(label="❌ Hata", state="error")
                st.error(f"Sistem hatası: {str(e)}")
