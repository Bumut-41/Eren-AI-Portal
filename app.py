import streamlit as st
import google.generativeai as genai
import PIL.Image
import os
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document

# --- 1. KRİTİK: VERSİYON HATASINI KÖKTEN ÇÖZEN AYAR ---
# Bu satır, kütüphanenin v1beta hatası vermesini engeller ve sistemi v1'e kilitler.
os.environ["GOOGLE_API_VERSION"] = "v1"

# --- 2. SAYFA VE API YAPILANDIRMASI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı! Lütfen Secrets ayarlarını kontrol edin.")
    st.stop()

# Modeli en güncel kararlı ismiyle tanımlıyoruz
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 3. DÖKÜMAN OKUMA FONKSİYONU ---
def dokuman_oku(dosya):
    try:
        if dosya.type == "application/pdf":
            reader = PdfReader(dosya)
            return "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
        elif dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(dosya)
            return "\n".join([p.text for p in doc.paragraphs])
        elif dosya.type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "text/csv"]:
            df = pd.read_excel(dosya) if "spreadsheet" in dosya.type else pd.read_csv(dosya)
            return df.to_string()
        return None
    except Exception as e:
        return f"Dosya Okuma Hatası: {str(e)}"

# --- 4. ARAYÜZ TASARIMI ---
st.title("🛡️ Eren AI Portalı")

with st.sidebar:
    st.title("🛡️ Eren AI")
    mod = st.selectbox("Asistan Modu", ["Eren AI Asistanı", "Akademik Analiz"])
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Giriş Bölümü
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        yukle = st.file_uploader("Belge", type=['pdf','docx','xlsx','csv','png','jpg'], label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya sorunuzu iletin...")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 5. ANALİZ VE YANIT MOTORU ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        cevap_alani = st.empty()
        cevap_alani.markdown("⚡ *Döküman inceleniyor...*")
        
        try:
            # Asistanın dosyayı "görememe" sorununu (image_43697a) metin enjeksiyonu ile çözüyoruz
            prompt_parcalari = [f"Sen Özel Eren Fen ve Teknoloji Lisesi asistanısın. Mod: {mod}.", soru]
            
            if yukle:
                if yukle.type.startswith("image/"):
                    prompt_parcalari.append(PIL.Image.open(yukle))
                else:
                    icerik = dokuman_oku(yukle)
                    if icerik:
                        # Bu enjeksiyon asistanın dosyayı görmesini sağlar
                        prompt_parcalari.append(f"\nSİZE YÜKLENEN BELGE İÇERİĞİ:\n{icerik}")

            # Kararlı API yolu üzerinden yanıt üretimi
            yanit = model.generate_content(prompt_parcalari)
            
            if yanit.text:
                cevap_alani.markdown(yanit.text)
                st.session_state.messages.append({"role": "assistant", "content": yanit.text})
        except Exception as e:
            cevap_alani.error(f"Sistem Hatası: {str(e)}")
