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
        st.markdown("### **🛡️ Akademik Rehber v20.0**")
        st.success("**Eğitici Mod:** Maksimum açıklama ve akademik derinlik aktif.")
        
        st.info("""
        **Nasıl Kullanılır?**
        1. Ödev dosyanı yükleyebilir veya doğrudan soru sorabilirsin.
        2. Eren AI, konuyu bir ders modülü gibi derinlemesine anlatacaktır.
        3. Her soru, kavramsal bir keşif yolculuğudur.
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
    
    # Güncellenmiş kurumsal input metni
    soru = st.chat_input("Eren AI'a sormak istediğin soruyu bu alana girebilirsiniz.")

# --- AKADEMİK İŞLEMCİ ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with chat_area:
        with st.chat_message("user"):
            st.markdown(soru)

    with chat_area:
        with st.chat_message("assistant"):
            durum = st.status("🛡️ Eren AI Akademik İçerik Hazırlıyor...")
            
            try:
                # --- V20.0 GENİŞLETİLMİŞ ÖĞRETİCİ TALİMAT ---
                system_instruction = f"""
                Sen Eren AI, Özel Eren Fen ve Teknoloji Lisesi'nin Yapay Zekasısın. {OKUL_BILGILERI}
                
                KİMLİK TANIMIN: Cevaplarına başlarken "Eren AI, Özel Eren Fen ve Teknoloji Lisesi'nin Yapay Zekası olarak size hizmet ediyorum." ifadesini kullan.

                AKADEMİK DERİNLİK VE GENİŞLETİLMİŞ ANLATIM PROTOKOLÜ:
                1. MİNİMUM ÖZET, MAKSİMUM ÖĞRETİM: Konuyu yüzeysel geçme. Bir terim geçtiğinde (Örn: "Oksidasyon", "Momentum", "Kalıtım") bu terimin ne anlama geldiğini, doğadaki karşılığını ve bilimsel önemini paragraf düzeyinde açıkla.
                2. TÜM SORULARI ANALİZ ET: Yüklenen materyaldeki tüm soruları eksiksiz tarayarak, her birini ayrı başlıkta derinlemesine incele.
                3. DOSYASIZ SORULARDA EKSTRA DETAY: Kullanıcı bir dosya yüklemeden soru soruyorsa, konuyu bir "Ders Notu" kapsamlılığında; tarihçesi, temel yasaları, uygulama alanları ve ileri seviye detaylarıyla anlat.
                4. CEVAP YASAK: Doğrudan cevap şıkkını söyleme. Öğrenciyi analitik düşünmeye sevk et. 
                5. KURUMSAL ÜSLUP: eren.k12.tr vizyonuna uygun, profesyonel, teşvik edici bir dil kullan.

                YENİ ANALİZ ŞABLONUN:
                ## [KONU BAŞLIĞI / SORU NO]
                
                ### 📚 Kavramsal ve Bilimsel Arkaplan
                [Burada konunun teorisini, bilimsel yasalarını ve 'neden' böyle olduğunu çok detaylı, öğretici bir metinle açıkla.]
                
                ### 🔍 Analitik İnceleme ve Strateji
                [Soruya özel verileri analiz et. Hangi bilginin hangi sonuca kapı açtığını, şıkların birbiriyle olan ilişkisini akademik bir dille irdele.]
                
                ### 💡 Kritik Düşünme Sentezi
                [Öğrencinin bu bilgiyi kullanarak çıkarım yapmasını sağlayacak derin bir Sokratik soru sor.]
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
                    durum.update(label="✅ Akademik Anlatım Tamamlandı", state="complete")
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                    
                    if dosya:
                        st.session_state.uploader_key += 1
                        st.rerun() 
                    
            except Exception as e:
                durum.update(label="❌ Hata", state="error")
                st.error(f"Sistem hatası: {str(e)}")
