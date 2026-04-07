import streamlit as st
import google.generativeai as genai
from google.generativeai import client # Versiyonu zorlamak için gerekli
import PIL.Image
import os
from PyPDF2 import PdfReader
from docx import Document

# --- 1. API VERSİYONUNU ÇEKİRDEKTEN KİLİTLEME ---
# Bu ayar, SDK'nın 'v1beta' yerine doğrudan 'v1' API uç noktasına bağlanmasını sağlar.
client._API_VERSION = "v1" 

# Sayfa Ayarları
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı!")
    st.stop()

# --- 2. KURUMSAL KİMLİK ---
EREN_AI_KIMLIK = "Ben Eren AI, Özel Eren Fen ve Teknoloji Lisesi'nin dijital asistanıyım."

# --- 3. YARDIMCI FONKSİYONLAR ---
def dosya_metnini_oku(yuklenen_dosya):
    try:
        if yuklenen_dosya.type == "application/pdf":
            reader = PdfReader(yuklenen_dosya)
            return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        elif yuklenen_dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(yuklenen_dosya)
            return "\n".join([para.text for para in doc.paragraphs])
        return None
    except Exception as e:
        return f"Hata: {e}"

# Modeli en güncel ve kararlı sürümüyle tanımlıyoruz
model_engine = genai.GenerativeModel('gemini-1.5-flash')

# --- 4. ARAYÜZ ---
with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=150)
    st.divider()
    mod = st.selectbox("Asistan Modu", ["Eren AI Asistanı", "Akademik Destek", "Veli Bilgilendirme"])
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Giriş Bölümü
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        yukle = st.file_uploader("Dosya", type=['png','jpg','jpeg','pdf','docx'], label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya bir soru sorun...")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 5. ANALİZ VE YANIT ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        alan = st.empty()
        
        # Kimlik Sorgusu
        if any(k in soru.lower() for k in ["kimsin", "adın ne"]):
            alan.markdown(EREN_AI_KIMLIK)
            st.session_state.messages.append({"role": "assistant", "content": EREN_AI_KIMLIK})
        else:
            alan.markdown("⚡ *Bağlantı v1 üzerinden kuruluyor...*")
            try:
                prompt_list = [f"Sen Eren AI'sın. Mod: {mod}.", soru]
                
                # Dosya Yüklüyse oku ve prompta ekle
                if yukle:
                    if yukle.type.startswith("image/"):
                        prompt_list.append(PIL.Image.open(yukle))
                    else:
                        icerik = dosya_metnini_oku(yukle)
                        if icerik:
                            # Modelin dökümanı görmesi için net bir etiketle ekliyoruz
                            prompt_list.append(f"\n[YÜKLENEN BELGE İÇERİĞİ]:\n{icerik}")

                # API Çağrısı
                yanit = model_engine.generate_content(prompt_list)
                
                if yanit.text:
                    alan.markdown(yanit.text)
                    st.session_state.messages.append({"role": "assistant", "content": yanit.text})
            
            except Exception as e:
                # Eğer hala 404 verirse burası hatayı detaylı gösterir
                alan.error(f"Erişim Hatası: {str(e)}")
