import streamlit as st
import google.generativeai as genai
import PIL.Image
import os
from PyPDF2 import PdfReader
from docx import Document

# --- 1. KURUMSAL KİMLİK VE SAYFA AYARLARI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

# Kurumsal Tanıtım Metni
EREN_AI_KIMLIK = """
Merhaba! Ben **Eren AI**, Özel Eren Fen ve Teknoloji Lisesi için özel olarak geliştirilmiş resmi yapay zeka asistanıyım. 

Temel amacım; okulumuzun yenilikçi ve teknoloji odaklı eğitim vizyonu doğrultusunda öğrencilerimize, öğretmenlerimize ve idari kadromuza kapsamlı bir akademik destek sağlamaktır. Derslerinizde karşılaştığınız zorlukları aşmanıza yardımcı olmak, projelerinizde fikir ortağınız olmak ve eğitim süreçlerinizi daha verimli hale getirmek için buradayım. 
"""

# --- 2. API VE MODEL YAPILANDIRMASI (404 ÇÖZÜMÜ) ---
# Secrets üzerinden API anahtarını alır
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Hata: API Anahtarı bulunamadı! Lütfen Streamlit Secrets ayarlarını kontrol edin.")
    st.stop()

@st.cache_resource
def model_yukle():
    # 404 hatalarını önlemek için en kararlı modeli seçer
    try:
        return genai.GenerativeModel('gemini-1.5-flash')
    except:
        return genai.GenerativeModel('gemini-pro')

model_engine = model_yukle()

# --- 3. BELGE OKUMA FONKSİYONU (WEB/SUNUCU TARAFLI) ---
def belge_icerigini_oku(dosya):
    try:
        if dosya.type == "application/pdf":
            reader = PdfReader(dosya)
            metin = ""
            for sayfa in reader.pages:
                eklenen = sayfa.extract_text()
                if eklenen: metin += eklenen + "\n"
            return metin
        elif dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(dosya)
            return "\n".join([p.text for p in doc.paragraphs])
        return None
    except Exception as e:
        return f"Dosya okuma hatası: {e}"

# --- 4. KULLANICI ARAYÜZÜ ---
with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    # Logo dosyası varsa gösterir
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=150)
    st.divider()
    mod = st.selectbox("Asistan Modu", ["Eren AI Asistanı", "Akademik Destek", "Veli Bilgilendirme"])
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Dosya Yükleme ve Soru Girişi
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        yuklenen_dosya = st.file_uploader("Dosya", type=['png','jpg','jpeg','pdf','docx'], label_visibility="collapsed")
    with c2:
        kullanici_sorusu = st.chat_input("Eren AI'ya bir soru sorun...")

# Sohbet Geçmişini Ekrana Bas
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 5. YANIT MOTORU VE AKILLI ODAKLANMA ---
if kullanici_sorusu:
    st.session_state.messages.append({"role": "user", "content": kullanici_sorusu})
    with st.chat_message("user"):
        st.markdown(kullanici_sorusu)

    with st.chat_message("assistant"):
        cevap_alani = st.empty()
        
        # Kimlik Sorgusu Kontrolü
        if any(k in kullanici_sorusu.lower() for k in ["kimsin", "adın ne", "necisin", "kendini tanıt"]):
            cevap_alani.markdown(EREN_AI_KIMLIK)
            st.session_state.messages.append({"role": "assistant", "content": EREN_AI_KIMLIK})
        
        else:
            cevap_alani.markdown("⚡ *Eren AI Bağlantı kuruluyor...*")
            try:
                baglam = f"Sen Özel Eren Fen ve Teknoloji Lisesi asistanı Eren AI'sın. Mod: {mod}."
                prompt_parcalari = [baglam, kullanici_sorusu]
                
                # Soru dosyayla mı ilgili?
                dosya_iliskisi = any(k in kullanici_sorusu.lower() for k in ["dosya", "belge", "pdf", "içerik", "oku", "özet"])

                if yuklenen_dosya:
                    if yuklenen_dosya.type.startswith("image/"):
                        prompt_parcalari.append(PIL.Image.open(yuklenen_dosya))
                    elif dosya_iliskisi:
                        metin = belge_icerigini_oku(yuklenen_dosya)
                        if metin:
                            prompt_parcalari.append(f"\n--- YÜKLENEN BELGE METNİ ---\n{metin}")

                yanit = model_engine.generate_content(prompt_parcalari)
                
                if yanit.text:
                    cevap_alani.markdown(yanit.text)
                    st.session_state.messages.append({"role": "assistant", "content": yanit.text})
            
            except Exception as e:
                cevap_alani.error(f"Sistem Hatası: {str(e)}")
