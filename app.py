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

# Doğru model ismini kullandığınızdan emin olun
model = genai.GenerativeModel('gemini-3-flash-preview')

# --- ÖZEL EREN FEN VE TEKNOLOJİ LİSESİ BİLGİ TABANI ---
OKUL_BILGILERI = "Kurum: Özel Eren Fen ve Teknoloji Lisesi | Web: https://eren.k12.tr/"

def metin_ayikla(dosya):
    try:
        if dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return "\n".join([p.text for p in Document(dosya).paragraphs])
        elif "spreadsheet" in dosya.type or "csv" in dosya.type:
            df = pd.read_excel(dosya) if "spreadsheet" in dosya.type else pd.read_csv(dosya)
            return f"TABLO VERİSİ:\n{df.to_string()}"
        elif "presentationml" in dosya.type:
            prs = Presentation(dosya)
            return "\n".join([shape.text for slide in prs.slides for shape in slide.shapes if hasattr(shape, "text")])
        return None
    except Exception as e:
        return f"Dosya Okuma Hatası: {e}"

# --- SOL MENÜ ---
with st.sidebar:
    try:
        st.image("Logo.png", use_container_width=True) # GitHub deponuzdaki logo
    except:
        st.subheader("🛡️ Eren AI")
    
    st.markdown("### **Akademik Portal**")
    st.info("Özel Eren Fen ve Teknoloji Lisesi paydaşları için geliştirilmiştir.")
    st.divider()
    st.caption("© 2026 Eren Eğitim Kurumları")

# --- SOHBET GEÇMİŞİ ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- GİRİŞ PANELİ ---
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        dosya = st.file_uploader("Dosya", type=['pdf','docx','xlsx','pptx','csv','png','jpg','jpeg'], key="eren_v13", label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Mesajınızı buraya yazın...")

# --- AKILLI İŞLEMCİ ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        durum = st.status("🛡️ Eren AI düşünüyor...")
        
        try:
            # --- ANA TALİMAT BLOĞU ---
            system_instruction = f"""
            Sen Özel Eren Fen ve Teknoloji Lisesi'nin resmi "Eren AI" akademik asistanısın. {OKUL_BILGILERI}
            TEMEL KAYNAĞIN: https://eren.k12.tr/ web sitesindeki kurumsal bilgilerdir.

            KRİTİK KURALLAR: 
            1. OKUL SORULARI: Okulun idari kadrosu, vizyonu veya etkinlikleri sorulduğunda, daima eren.k12.tr adresini referans al. 
            2. BAĞLAM YÖNETİMİ: Kullanıcı doğrudan dosyaya referans vermedikçe (özetle, analiz et vb.) dosyayı görmezden gel.
            3. ÖĞRETMEN DESTEĞİ: "Quiz hazırla", "ödev oluştur" gibi taleplerde, Fen ve Teknoloji Lisesi standartlarına uygun, cevap anahtarlı içerikler üret.
            4. KURUMSAL ÜSLUP: "Dosyada bilgi yok" gibi teknik ifadeler kullanma, gerekirse okul web sitesine yönlendir.
            """
            
            prompt_parts = [system_instruction, soru]
            
            # Eğer kullanıcı dosyaya referans veriyorsa içeriği ekle
            if dosya:
                analiz_kelimeleri = ["dosya", "belge", "doküman", "özet", "listele", "tablo", "analiz", "oku", "yüklediğim", "quiz", "soru", "ödev"]
                if any(kelime in soru.lower() for kelime in analiz_kelimeleri):
                    if dosya.type.startswith("image/"):
                        prompt_parts.append(Image.open(dosya))
                    elif dosya.type == "application/pdf":
                        reader = PdfReader(dosya)
                        pdf_metni = "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
                        if len(pdf_metni.strip()) > 50:
                            prompt_parts.append(f"İLGİLİ DOSYA İÇERİĞİ:\n{pdf_metni}")
                        else:
                            dosya.seek(0)
                            prompt_parts.extend(pdf2image.convert_from_bytes(dosya.read())[:5])
                    else:
                        ek_metin = metin_ayikla(dosya)
                        if ek_metin: prompt_parts.append(f"İLGİLİ DOSYA İÇERİĞİ:\n{ek_metin}")

            response = model.generate_content(prompt_parts)
            
            if response:
                durum.update(label="✅ Hazır", state="complete")
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
        except Exception as e:
            durum.update(label="❌ Hata", state="error")
            st.error(f"Sistem hatası: {str(e)}")
