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

# --- SOL MENÜ (ANAYASAL VE SABİT) ---
def sidebar_ciz():
    with st.sidebar:
        try:
            st.image("Logo.png", use_container_width=True)
        except:
            st.subheader("🛡️ Eren AI")
        
        st.markdown("---")
        # ANAYASAL MADDE: Kimlik Başlığı
        st.markdown("### **🛡️ Eren AI Education**")
        st.success("**Anayasal Mod:** Her soru için bireysel ve derin analiz zorunludur.")
        
        # ANAYASAL MADDE: Sistem Rehberi (Güncel ve Kurumsal)
        st.markdown("### **📖 Sistem Rehberi**")
        st.info("""
        1. **Akademik dökümanlarınızı veya ödev dosyalarınızı** "Dosya Yükleme" alanından sisteme güvenle iletebilirsiniz.
        2. Analiz edilmesini istediğiniz tüm hususları **metin alanına girerek** Eren AI ile akademik etkileşim başlatabilirsiniz.
        3. Sisteme iletilen her bir soru, **pedagojik derinlik ilkeleri** uyarınca hiçbir detay atlanmadan, müstakil birer ders modülü olarak analiz edilir.
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
    
    # ANAYASAL GİRİŞ METNİ
    soru = st.chat_input("Eren AI'a sormak istediğin soruyu bu alana girebilirsiniz.")

# --- AKADEMİK İŞLEMCİ ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with chat_area:
        with st.chat_message("user"):
            st.markdown(soru)

    with chat_area:
        with st.chat_message("assistant"):
            durum = st.status("🛡️ Eren AI Akademik Müfredat Analizini Yürütüyor...")
            
            try:
                # --- ANAYASAL DERİN TALİMAT (V23.0) ---
                system_instruction = f"""
                Sen Eren AI, Özel Eren Fen ve Teknoloji Lisesi'nin Yapay Zekasısın. {OKUL_BILGILERI}
                
                KİMLİK TANIMIN: Cevaplarına başlarken "Eren AI, Özel Eren Fen ve Teknoloji Lisesi'nin Yapay Zekası olarak size hizmet ediyorum." ifadesini kullan.

                🛡️ AKADEMİK ANAYASA (SABİT VE DEĞİŞTİRİLEMEZ):
                MADDE 1: MATERYALDEKİ TÜM SORULARI TEKER TEKER ANALİZ ET. Hiçbir soruyu atlama, toplu cevap verme.
                MADDE 2: MAKSİMUM AKADEMİK DERİNLİK. Konuyu bir ders kitabı zenginliğinde, bilimsel terminolojiye sadık kalarak genişçe anlat.
                MADDE 3: REHBERLİK İLKESİ. Şıkları analiz et, mantık yollarını göster ama doğrudan doğru şıkkı söyleme.
                MADDE 4: SİSTEMATİK ANALİZ FORMATI. Her soru için aşağıdaki üçlü başlık yapısını kullan.
                MADDE 5: KURUMSAL ÜSLUP. Profesyonel, teşvik edici ve eren.k12.tr vizyonuna uygun bir dil kullan.

                ZORUNLU ANALİZ ŞABLONUN:
                ## [SORU NO / KONU BAŞLIĞI]
                
                ### 📚 Kavramsal ve Bilimsel Derinlik
                [Burada konuyu en ince ayrıntısına kadar, akademik bir dille öğret.]
                
                ### 🔍 Analitik İnceleme ve Çözüm Stratejisi
                [Soru verilerini ve seçenekleri bilimsel bir süzgeçten geçirerek analiz et.]
                
                ### 💡 Analitik Sorgulama ve Sentez
                [Öğrencinin konuyu içselleştirmesini sağlayacak, çıkarım odaklı Sokratik soru.]
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

                response = model.generate_content(prompt_parts)
                
                if response:
                    durum.update(label="✅ Anayasal Analiz Tamamlandı", state="complete")
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                    
                    if dosya:
                        st.session_state.uploader_key += 1
                        st.rerun() 
                    
            except Exception as e:
                durum.update(label="❌ Hata", state="error")
                st.error(f"Teknik bir aksaklık oluştu: {str(e)}")
