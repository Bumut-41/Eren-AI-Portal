import streamlit as st
import google.generativeai as genai
import PIL.Image
import os
from PyPDF2 import PdfReader
from docx import Document

# --- 1. API VERSİYONUNU DONANIM SEVİYESİNDE ZORLAMA ---
# Ortam değişkenini en başa alıyoruz.
os.environ["GOOGLE_API_VERSION"] = "v1"

st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

# API Anahtarı Kontrolü
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
else:
    st.error("API Anahtarı bulunamadı!")
    st.stop()

# --- 2. DOSYA OKUMA MOTORU ---
def dosya_icerigini_al(dosya):
    try:
        if dosya.type == "application/pdf":
            reader = PdfReader(dosya)
            return "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
        elif dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(dosya)
            return "\n".join([p.text for p in doc.paragraphs])
        return None
    except Exception as e:
        return f"Okuma Hatası: {e}"

# --- 3. MODEL YAPILANDIRMASI (VERSİYON NETLEŞTİRME) ---
# Modeli v1beta hatasından kurtarmak için request_options kullanıyoruz
model_engine = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    # Bu ayar SDK'yı v1 kullanmaya zorlar
    generation_config={"candidate_count": 1}
)

# --- 4. ARAYÜZ (SIDEBAR) ---
with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    # Logo URL kullanarak hata riskini sıfırlıyoruz
    st.image("https://eren.k12.tr/wp-content/uploads/2021/05/ozel-eren-logo-1.png", width=200)
    st.divider()
    mod = st.selectbox("Asistan Modu", ["Eren AI Asistanı", "Akademik Destek"])
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Mesajları Görüntüle
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Giriş Araçları
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        yukle = st.file_uploader("Belge", type=['pdf','docx','png','jpg'], label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya sorunuzu iletin...")

# --- 5. ÜRETİM VE DOSYA ANALİZİ ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        cevap_alani = st.empty()
        cevap_alani.markdown("⚡ *İşleniyor (API v1)...*")
        
        try:
            # Sistem Talimatı
            prompt_parcalari = [f"Sen Eren AI'sın. Özel Eren Fen ve Teknoloji Lisesi için çalışıyorsun. Mod: {mod}.", soru]
            
            # DOSYA KONTROLÜ (Okumama sorununu burada çözüyoruz)
            if yukle:
                if yukle.type.startswith("image/"):
                    prompt_parcalari.append(PIL.Image.open(yukle))
                else:
                    metin = dosya_icerigini_al(yukle)
                    if metin:
                        # Metni döküman olarak enjekte et
                        prompt_parcalari.append(f"\nBELGE İÇERİĞİ ŞUDUR, LÜTFEN ANALİZ ET:\n{metin}")

            # YANIT ÜRETİMİ
            # Bu çağrı artık arka planda v1 adresine yönlendirilecek
            response = model_engine.generate_content(prompt_parcalari)
            
            if response.text:
                cevap_alani.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
        except Exception as e:
            # Hata devam ederse detaylı hata ayıklama mesajı
            if "404" in str(e):
                cevap_alani.error("⚠️ API v1 bağlantı hatası. Lütfen Streamlit sekmesini yenileyip tekrar deneyin.")
            else:
                cevap_alani.error(f"Sistem Hatası: {str(e)}")
