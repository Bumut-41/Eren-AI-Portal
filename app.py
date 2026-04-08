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

# --- GELİŞMİŞ DOSYA OKUMA SİSTEMİ ---
def dosya_metne_cevir(dosya):
    try:
        if dosya.type == "application/pdf":
            reader = PdfReader(dosya)
            # Tüm sayfaları oku ve metni birleştir
            return "\n".join([sayfa.extract_text() for sayfa in reader.pages if sayfa.extract_text()])
        elif dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(dosya)
            return "\n".join([p.text for p in doc.paragraphs])
        elif "presentationml" in dosya.type:
            pptx = Presentation(dosya)
            return "\n".join([shape.text for slide in pptx.slides for shape in slide.shapes if hasattr(shape, "text")])
        elif "spreadsheet" in dosya.type or "csv" in dosya.type:
            df = pd.read_excel(dosya) if "spreadsheet" in dosya.type else pd.read_csv(dosya)
            return df.to_string()
        return None
    except Exception as e:
        return f"Dosya okuma hatası: {e}"

# --- MODEL YAPILANDIRMASI ---
# Listenizde çalıştığını teyit ettiğimiz en güncel model
model = genai.GenerativeModel('gemini-3-flash-preview')

# --- ARAYÜZ ---
with st.sidebar:
    st.title("🛡️ Eren AI")
    st.markdown("### Özel Eren Fen ve Teknoloji Lisesi")
    st.divider()
    mod = st.selectbox("Asistan Modu", ["Genel Asistan", "Döküman Analizi", "Akademik Rehber"])

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Giriş ve Dosya
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        belge = st.file_uploader("Dosya", type=['pdf','docx','pptx','xlsx','csv','png','jpg','jpeg'], label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya sorunuzu iletin...")

# --- İŞLEME VE YANIT ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        cevap_alani = st.empty()
        cevap_alani.info("🛡️ Eren AI dosyayı okuyor ve analiz ediyor...")
        
        try:
            # Temel prompt
            prompt_parcalari = [f"Sen Eren AI'sın. Mod: {mod}. Profesyonel bir okul asistanısın.", soru]
            
            # Eğer dosya yüklüyse metne çevir ve prompta ekle
            if belge:
                if belge.type.startswith("image/"):
                    prompt_parcalari.append(Image.open(belge))
                else:
                    # Döküman içeriğini metne dönüştür
                    belge_metni = dosya_metne_cevir(belge)
                    if belge_metni:
                        # Bu kısım dosyanın AI tarafından "görülmesini" sağlar
                        prompt_parcalari.append(f"\n\n[SİSTEM NOTU: Kullanıcı bir dosya yükledi. Dosya içeriği aşağıdadır:]\n{belge_metni}")
            
            # Yanıt Üret
            response = model.generate_content(prompt_parcalari)
            
            if response.text:
                cevap_alani.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            else:
                cevap_alani.error("Model boş bir yanıt döndürdü.")
                
        except Exception as e:
            cevap_alani.error(f"Sistem Hatası: {str(e)}")
