import streamlit as st
import google.generativeai as genai
import PIL.Image
import os
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document
from pptx import Presentation

# --- 1. KURUMSAL KİMLİK VE SAYFA AYARLARI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

EREN_AI_KIMLIK = """
Merhaba! Ben **Eren AI**, Özel Eren Fen ve Teknoloji Lisesi için geliştirilmiş resmi yapay zeka asistanıyım. 
Dökümanlarınızı analiz edebilir ve akademik çalışmalarınızda size destek olabilirim.
"""

# --- 2. API VE MODEL YAPILANDIRMASI (404 HATASI KESİN ÇÖZÜM) ---
# Beta sürüm kısıtlamalarından kurtulmak için en kararlı konfigürasyonu kullanıyoruz
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı! Lütfen Secrets kısmını kontrol edin.")
    st.stop()

# Versiyon hatasını aşmak için modeli doğrudan kararlı isimle çağırıyoruz
model_engine = genai.GenerativeModel('gemini-1.5-flash')

# --- 3. SUNUCU TARAFLI DOSYA OKUMA MOTORU ---
def dosya_metnini_ayikla(dosya):
    try:
        if dosya.type == "application/pdf":
            reader = PdfReader(dosya)
            return "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
        
        elif dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(dosya)
            return "\n".join([p.text for p in doc.paragraphs])
        
        elif dosya.type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
            prs = Presentation(dosya)
            metin = []
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"): metin.append(shape.text)
            return "\n".join(metin)
        
        elif dosya.type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "text/csv"]:
            df = pd.read_excel(dosya) if "spreadsheet" in dosya.type else pd.read_csv(dosya)
            return f"Tablo Verisi:\n{df.to_string()}"
            
        return None
    except Exception as e:
        return f"Dosya Okuma Hatası: {str(e)}"

# --- 4. ARAYÜZ TASARIMI ---
with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=150)
    st.divider()
    mod = st.selectbox("Asistan Modu", ["Eren AI Asistanı", "Akademik Analiz", "Veri İnceleme"])
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Giriş Alanları
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        yukle = st.file_uploader("Dosya Seç", type=['pdf','docx','pptx','xlsx','csv','png','jpg'], label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya bir soru sorun...")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 5. YANIT MOTORU VE DOSYA ANALİZİ ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        alan = st.empty()
        
        if any(k in soru.lower() for k in ["kimsin", "adın ne"]):
            alan.markdown(EREN_AI_KIMLIK)
            st.session_state.messages.append({"role": "assistant", "content": EREN_AI_KIMLIK})
        else:
            alan.markdown("⚡ *İşleniyor...*")
            try:
                # Prompt listesini oluşturuyoruz
                prompt_parcalari = [f"Sen Özel Eren Fen ve Teknoloji Lisesi asistanısın. Mod: {mod}.", soru]
                
                # Dosya analizi: Asistanın "dosyaya erişemiyorum" demesini engeller
                if yukle:
                    if yukle.type.startswith("image/"):
                        prompt_parcalari.append(PIL.Image.open(yukle))
                    else:
                        icerik = dosya_metnini_ayikla(yukle)
                        if icerik:
                            prompt_parcalari.append(f"\n--- DOSYA İÇERİĞİ ---\n{icerik}")

                # Modelden kararlı sürümle yanıt alıyoruz
                yanit = model_engine.generate_content(prompt_parcalari)
                if yanit.text:
                    alan.markdown(yanit.text)
                    st.session_state.messages.append({"role": "assistant", "content": yanit.text})
            except Exception as e:
                alan.error(f"Sistem Hatası: {str(e)}")
