import streamlit as st
import google.generativeai as genai
import PIL.Image
import os
from PyPDF2 import PdfReader
from docx import Document

# --- 1. KRİTİK HATA DÜZELTMESİ (v1beta Hatası İçin) ---
os.environ["GOOGLE_API_VERSION"] = "v1"

# Sayfa Ayarları
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı!")
    st.stop()

# --- 2. ÖZEL KURUMSAL TANITIM ---
EREN_AI_KIMLIK = """
Merhaba! Ben **Eren AI**, Özel Eren Fen ve Teknoloji Lisesi asistanıyım. 
Okulumuzun akademik vizyonuyla size destek olmak için buradayım.
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
    # Hata almamak için doğrudan güncel modeli çağırıyoruz
    return genai.GenerativeModel('gemini-1.5-flash')

model_engine = model_getir()

# --- 4. ARAYÜZ (SIDEBAR) ---
with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    # Logo yoksa hata vermemesi için kontrol
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

# Sohbet Geçmişi
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
        
        # KİMLİK SORGUSU
        kimlik_sorulari = ["sen kimsin", "adın ne", "necisin", "kimsin sen", "kendini tanıt"]
        if any(kelime in soru.lower() for kelime in kimlik_sorulari):
            alan.markdown(EREN_AI_KIMLIK)
            st.session_state.messages.append({"role": "assistant", "content": EREN_AI_KIMLIK})
        else:
            alan.markdown("⚡ *Bağlantı kuruluyor...*")
            try:
                talimat = (
                    "Sen Özel Eren Fen ve Teknoloji Lisesi'nin asistanısın. "
                    f"Mod: {mod}. Profesyonel ve akademik bir dil kullan."
                )
                prompt = [talimat, soru]
                
                # --- DOSYA OKUMA SİSTEMİ (BOZULMAYAN YAPI) ---
                if yukle:
                    if yukle.type.startswith("image/"):
                        prompt.append(PIL.Image.open(yukle))
                    else:
                        metin = dosya_metnini_oku(yukle)
                        if metin:
                            # Dosya yüklüyse prompt'a doğrudan ekle (Burası okumayı garanti eder)
                            prompt.append(f"\nBELGE İÇERİĞİ:\n{metin}")

                yanit = model_engine.generate_content(prompt)
                
                if yanit.text:
                    alan.markdown(yanit.text)
                    st.session_state.messages.append({"role": "assistant", "content": yanit.text})
                
            except Exception as e:
                # 404 hatasını yakalayıp kullanıcıya v1'e geçildiğini bildirir
                alan.error(f"Sistem Hatası: {str(e)}")
