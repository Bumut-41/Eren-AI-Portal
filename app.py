import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from PIL import Image
import pdf2image
import pandas as pd
from docx import Document
from pptx import Presentation

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

# --- SOKRATİK DERİNLİK PROTOKOLÜ (SİSTEM TALİMATI) ---
def get_system_instruction():
    return f"""
    Sen Özel Eren Fen ve Teknoloji Lisesi'nin "Baş Akademik Rehberisin". {OKUL_BILGILERI}
    
    GÖREVİN: Öğrencinin yüklediği ödevdeki HER BİR SORUYU ayrı ayrı ele alarak, en derin akademik düzeyde öğretmek. 
    
    HER SORU İÇİN İZLEMEN GEREKEN ŞABLON:
    
    ## [Soru Numarası]: [Sorunun Kapsadığı Temel Kavram]
    
    **1. Akademik Arka Plan (Teori):** Soruyu çözmeden önce, sorunun dayandığı bilimsel yasayı veya biyolojik süreci (Örn: Homeostazi nedir? Su neden polardır? ATP neden evrenseldir?) en ince detayına kadar anlat.
    
    **2. Sorunun Analitik İncelemesi:** Sorudaki öncülleri veya şıkları tek tek masaya yatır. 
    - "A şıkkı neden doğru/yanlış olabilir?" 
    - "Bu şıkta kullanılan hangi kelime çeldiricidir?" 
    - "Soruda verilen hangi veri bizi çözüme götüren 'anahtar' veridir?"
    
    **3. Strateji ve Akıl Yürütme:** Öğrenciye bu tarz bir soruyla bir daha karşılaştığında nasıl düşünmesi gerektiğini öğret. (Örn: "Grafik sorularında önce eksenlerin birimlerine bakmalısın.")
    
    **4. Sokratik Soru (Etkileşim):** Anlatımın sonunda öğrenciye o soruyla ilgili düşündürücü bir soru sor. Doğrudan cevabı söylemek yerine, "Bu bilgi ışığında, sence X durumunda ne olurdu?" diyerek onun çıkarım yapmasını sağla.
    
    **KRİTİK KURAL:** - Asla sadece cevap anahtarı gibi davranma. 
    - Fen Lisesi öğrencisine hitap ettiğini unutma; dilin profesyonel, akademik ve teşvik edici olsun.
    - Cevapların sonuna kurumsal yönlendirme metni ekleme.
    """

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
    dosya = st.file_uploader("Ödev Görseli / PDF Yükle", type=['pdf','docx','xlsx','pptx','csv','png','jpg','jpeg'], 
                             key=f"uploader_{st.session_state.uploader_key}", 
                             label_visibility="collapsed")
    soru = st.chat_input("Ödevimdeki tüm soruları adım adım ve derinlemesine anlatırmısın?")

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
                system_instruction = get_system_instruction()
                prompt_parts = [system_instruction, soru]
                
                if dosya:
                    if dosya.type.startswith("image/"):
                        prompt_parts.append(Image.open(dosya))
                    elif dosya.type == "application/pdf":
                        # PDF analizi için geliştirilmiş motor
                        reader = PdfReader(dosya)
                        pdf_metni = ""
                        for page in reader.pages:
                            text = page.extract_text()
                            if text: pdf_metni += text + "\n"
                        prompt_parts.append(f"ÖDEV DOSYASI İÇERİĞİ:\n{pdf_metni}")
                    else:
                        # Diğer dosya türleri için metin ayıklama
                        # (Önceki sürümlerdeki metin_ayikla fonksiyonu kullanılabilir)
                        pass

                response = model.generate_content(prompt_parts)
                
                if response:
                    durum.update(label="✅ Akademik Analiz Tamamlandı", state="complete")
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                    
                    if dosya:
                        st.session_state.uploader_key += 1
                        st.rerun() 
                    
            except Exception as e:
                durum.update(label="❌ Hata", state="error")
                st.error(f"Sistem hatası: {str(e)}")
