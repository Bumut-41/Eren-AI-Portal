import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import pandas as pd
from docx import Document
from pptx import Presentation
from PIL import Image

# --- SİSTEM AYARLARI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

# API Anahtarı
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı!")
    st.stop()

# --- GELİŞMİŞ DOSYA OKUMA MOTORU (Hata Kontrollü) ---
def metin_ayikla(dosya):
    try:
        if dosya.type == "application/pdf":
            reader = PdfReader(dosya)
            return "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
        elif dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return "\n".join([p.text for p in Document(dosya).paragraphs])
        elif "spreadsheet" in dosya.type or "csv" in dosya.type:
            df = pd.read_excel(dosya) if "spreadsheet" in dosya.type else pd.read_csv(dosya)
            return f"Tablo Verileri:\n{df.to_string()}"
        elif "presentationml" in dosya.type:
            pptx = Presentation(dosya)
            return "\n".join([s.text for sl in pptx.slides for s in sl.shapes if hasattr(s, "text")])
        return None
    except Exception as e:
        return f"OKUMA HATASI: {str(e)}"

# --- MODEL ---
# Gemini 3 Preview - En gelişmiş döküman anlama kapasitesine sahip model
model = genai.GenerativeModel('gemini-3-flash-preview')

# --- ARAYÜZ ---
with st.sidebar:
    st.title("🛡️ Eren AI")
    st.markdown("### Özel Eren Fen ve Teknoloji Lisesi")
    st.divider()
    mod = st.selectbox("Asistan Modu", ["Genel Asistan", "Döküman Analizi"])

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Giriş Bölümü
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        belge = st.file_uploader("Dosya", type=['pdf','docx','pptx','xlsx','csv','png','jpg','jpeg'], label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya sorunuzu iletin...")

# --- İŞLEME ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        cevap_alani = st.empty()
        cevap_alani.info("🛡️ Eren AI dosyayı ve soruyu analiz ediyor...")
        
        try:
            # 1. DOSYA İÇERİĞİNİ HAZIRLA
            belge_icerigi = ""
            gorsel_mi = False
            gorsel_data = None

            if belge:
                if belge.type.startswith("image/"):
                    gorsel_mi = True
                    gorsel_data = Image.open(belge)
                else:
                    ayiklanan_metin = metin_ayikla(belge)
                    if ayiklanan_metin:
                        belge_icerigi = f"\n\n--- DOSYA İÇERİĞİ ---\n{ayiklanan_metin}\n--- DOSYA SONU ---\n"

            # 2. PROMPT OLUŞTUR
            # Talimat + Dosya İçeriği + Soru
            tam_prompt = [f"Sen Eren AI'sın. Profesyonel bir lise asistanısın. {belge_icerigi}", soru]
            
            if gorsel_mi:
                tam_prompt.append(gorsel_data)

            # 3. YANIT ÜRET
            response = model.generate_content(tam_prompt)
            
            if response.text:
                cevap_alani.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            else:
                cevap_alani.error("Yanıt üretilemedi.")
                
        except Exception as e:
            cevap_alani.error(f"Hata: {str(e)}")
