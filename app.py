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
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı!")
    st.stop()

# En güncel ve stabil model
model = genai.GenerativeModel('gemini-1.5-pro')

# --- DOSYA İŞLEME FONKSİYONLARI ---
def metin_ayikla(dosya):
    try:
        if dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return "\n".join([p.text for p in Document(dosya).paragraphs])
        elif "spreadsheetml" in dosya.type or "csv" in dosya.type:
            df = pd.read_excel(dosya) if "spreadsheet" in dosya.type else pd.read_csv(dosya)
            return f"Tablo Verileri:\n{df.to_string()}"
        elif "presentationml" in dosya.type:
            prs = Presentation(dosya)
            text = []
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text.append(shape.text)
            return "\n".join(text)
        return None
    except Exception as e:
        return f"Hata: {str(e)}"

# --- ARAYÜZ ---
with st.sidebar:
    st.title("🛡️ Eren AI")
    st.markdown("### Özel Eren Fen ve Teknoloji Lisesi")
    st.divider()
    mod = st.selectbox("Asistan Modu", ["Döküman Analizi", "Genel Asistan"])

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Giriş Paneli
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        dosya = st.file_uploader("Dosya", type=['pdf','docx','xlsx','pptx','csv','png','jpg','jpeg'], key="final_v5", label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya sorunuzu iletin...")

# --- ANA İŞLEMCİ ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        durum = st.status("🛡️ Eren AI analiz ediyor...")
        try:
            prompt_parcalari = [f"Sen Eren AI'sın. Mod: {mod}. Profesyonel bir okul asistanısın.", soru]
            
            if dosya:
                if dosya.type.startswith("image/"):
                    prompt_parcalari.append(Image.open(dosya))
                    durum.write("🖼️ Görsel eklendi.")
                elif dosya.type == "application/pdf":
                    reader = PdfReader(dosya)
                    metin = "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
                    
                    if len(metin.strip()) > 100:
                        prompt_parcalari.append(f"PDF İçeriği:\n{metin}")
                        durum.write("📄 PDF metni okundu.")
                    else:
                        durum.write("👁️ Metin bulunamadı, PDF görsele çevriliyor...")
                        # Baştan okumak için dosya işaretçisini sıfırla
                        dosya.seek(0)
                        images = pdf2image.convert_from_bytes(dosya.read())
                        prompt_parcalari.extend(images[:5]) # İlk 5 sayfa
                else:
                    icerik = metin_ayikla(dosya)
                    if icerik:
                        prompt_parcalari.append(f"Dosya ({dosya.name}) İçeriği:\n{icerik}")
                        durum.write(f"📂 {dosya.name} okundu.")

            response = model.generate_content(prompt_parcalari)
            if response.text:
                durum.update(label="✅ Tamamlandı", state="complete")
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            durum.update(label="❌ Hata", state="error")
            st.error(f"Hata: {str(e)}")
