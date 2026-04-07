import streamlit as st
import google.generativeai as genai
import PIL.Image
import os
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document
from pptx import Presentation

# --- 1. KRİTİK: API VERSİYONUNU SİSTEME KAZIMAK ---
# Hata mesajındaki 'v1beta' zorlamasını bu satırla kırıyoruz.
os.environ["GOOGLE_API_VERSION"] = "v1"

# --- 2. SAYFA VE API YAPILANDIRMASI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    # Yapılandırmayı doğrudan v1 üzerinden yapıyoruz
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı! Lütfen Secrets ayarlarını kontrol edin.")
    st.stop()

# Modeli en kararlı ismiyle tanımlıyoruz
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 3. TÜM DOSYA FORMATLARI İÇİN OKUMA MOTORU ---
def dosya_icerigini_oku(dosya):
    try:
        if dosya.type == "application/pdf":
            reader = PdfReader(dosya)
            return "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
        elif dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(dosya)
            return "\n".join([p.text for p in doc.paragraphs])
        elif dosya.type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
            prs = Presentation(dosya)
            metinler = []
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        metinler.append(shape.text)
            return "\n".join(metinler)
        elif dosya.type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "text/csv"]:
            df = pd.read_excel(dosya) if "spreadsheet" in dosya.type else pd.read_csv(dosya)
            return df.to_string()
        return None
    except Exception as e:
        return f"Dosya Okuma Hatası: {str(e)}"

# --- 4. ARAYÜZ (SOL MENÜ, LOGO VE YÜKLEME ALANI) ---
with st.sidebar:
    # Logo hatasını önlemek için güvenli bir başlık ve ikon kullanıyoruz
    st.markdown("## 🛡️ ÖZEL EREN \n### FEN VE TEKNOLOJİ LİSESİ")
    st.divider()
    
    mod = st.selectbox("Asistan Modu", ["Eren AI Asistanı", "Akademik Analiz", "Okul Bilgilendirme"])
    
    st.subheader("📁 Belge Yükle")
    yuklenen_dosya = st.file_uploader(
        "Okul dökümanlarını buraya bırakın", 
        type=['pdf','docx','pptx','xlsx','csv','png','jpg','jpeg']
    )
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

# Ana Ekran Başlığı
st.title("🛡️ Eren AI Portalı")
st.info(f"Mod: {mod} | Sistem Durumu: v1 Kararlı Sürüm")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Mesaj Geçmişini Göster
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. ANALİZ VE YANIT MOTORU ---
soru = st.chat_input("Eren AI'ya sorunuzu iletin...")

if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        cevap_alani = st.empty()
        cevap_alani.markdown("⚡ *Döküman inceleniyor ve yanıt üretiliyor...*")
        
        try:
            # Asistanın temel kimliği ve yüklenecek içerik
            prompt_icerigi = [f"Sen Özel Eren Fen ve Teknoloji Lisesi asistanısın. Modun: {mod}. Soruyu bu kimlikle yanıtla.", soru]
            
            if yuklenen_dosya:
                if yuklenen_dosya.type.startswith("image/"):
                    prompt_icerigi.append(PIL.Image.open(yuklenen_dosya))
                else:
                    metin = dosya_icerigini_oku(yuklenen_dosya)
                    if metin:
                        prompt_icerigi.append(f"\nBELGE İÇERİĞİ:\n{metin}")

            # Yanıt üretimi (Hata mesajındaki 404'ü önlemek için model ismi sadeleştirildi)
            yanit = model.generate_content(prompt_icerigi)
            
            if yanit.text:
                cevap_alani.markdown(yanit.text)
                st.session_state.messages.append({"role": "assistant", "content": yanit.text})
        except Exception as e:
            # Hata verirse detaylı mesaj göster
            cevap_alani.error(f"Sistem Hatası: {str(e)}")
