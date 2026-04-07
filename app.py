import streamlit as st
import google.generativeai as genai
import PIL.Image
import os
from PyPDF2 import PdfReader
from docx import Document

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı!")
    st.stop()

# --- 2. ÖZEL KURUMSAL TANITIM METNİ ---
EREN_AI_KIMLIK = """
Merhaba! Ben **Eren AI**, Özel Eren Fen ve Teknoloji Lisesi için özel olarak geliştirilmiş yapay zeka asistanıyım. 

Temel amacım; okulumuzun yenilikçi ve teknoloji odaklı eğitim vizyonu doğrultusunda öğrencilerimize, öğretmenlerimize ve idari kadromuza kapsamlı bir akademik destek sağlamaktır. 
Derslerinizde karşılaştığınız zorlukları aşmanıza yardımcı olmak, projelerinizde fikir ortağınız olmak ve eğitim süreçlerinizi daha verimli hale getirmek için buradayım. 

Özel Eren Fen ve Teknoloji Lisesi'nin kurumsal değerlerini temsil ederek; profesyonel, yardımcı ve çözüm odaklı bir yaklaşımla her türlü sorunuzda yanınızdayım.
"""

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
        return f"Dosya okunurken hata oluştu: {e}"

@st.cache_resource
def model_getir():
    try:
        mevcut_modeller = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for tercih in ['models/gemini-1.5-flash', 'gemini-1.5-flash', 'models/gemini-pro']:
            if tercih in mevcut_modeller:
                return genai.GenerativeModel(tercih)
        return genai.GenerativeModel(mevcut_modeller[0])
    except:
        return genai.GenerativeModel('gemini-1.5-flash')

model_engine = model_getir()

# --- 4. ARAYÜZ (SIDEBAR) ---
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

with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        yukle = st.file_uploader("Dosya", type=['png','jpg','jpeg','pdf','docx'], label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya bir soru sorun...")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 5. AKILLI YANIT MOTORU ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        alan = st.empty()
        
        # KİMLİK SORGUSU KONTROLÜ
        kimlik_sorulari = ["sen kimsin", "adın ne", "necisin", "kimsin sen", "kendini tanıt"]
        if any(kelime in soru.lower() for kelime in kimlik_sorulari):
            alan.markdown(EREN_AI_KIMLIK)
            st.session_state.messages.append({"role": "assistant", "content": EREN_AI_KIMLIK})
        else:
            alan.markdown("⚡ *Bağlantı kuruluyor...*")
            try:
                # Arka plan talimatı
                talimat = (
                    "Sen Özel Eren Fen ve Teknoloji Lisesi'nin yapay zeka asistanı Eren AI'sın. "
                    f"Şu an '{mod}' modundasın. Daima profesyonel, nazik ve akademik bir dil kullan."
                )
                prompt = [talimat, soru]
                
                # Akıllı Odaklanma Kontrolü
                dosya_kelimeleri = ["dosya", "belge", "doküman", "pdf", "word", "içerik", "yüklediğim"]
                dosyadan_bahsediyor = any(k in soru.lower() for k in dosya_kelimeleri)

                if yukle:
                    if yukle.type.startswith("image/"):
                        prompt.append(PIL.Image.open(yukle))
                    elif dosyadan_bahsediyor:
                        metin = dosya_metnini_oku(yukle)
                        if metin:
                            prompt.append(f"\n--- YÜKLENEN BELGE ---\n{metin}")

                yanit = model_engine.generate_content(prompt)
                
                if yanit.text:
                    alan.markdown(yanit.text)
                    st.session_state.messages.append({"role": "assistant", "content": yanit.text})
                
            except Exception as e:
                alan.error(f"Sistem Hatası: {str(e)}")
