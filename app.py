import streamlit as st
import google.generativeai as genai
import PIL.Image
import os
from PyPDF2 import PdfReader
from docx import Document

# --- 1. SAYFA AYARLARI VE KURUMSAL KİMLİK ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

# Kurumsal Tanıtım Metni
EREN_AI_KIMLIK = """
Merhaba! Ben **Eren AI**, Özel Eren Fen ve Teknoloji Lisesi için özel olarak geliştirilmiş yapay zeka asistanıyım. 

Temel amacım; okulumuzun yenilikçi ve teknoloji odaklı eğitim vizyonu doğrultusunda öğrencilerimize, öğretmenlerimize ve idari kadromuza kapsamlı bir akademik destek sağlamaktır. 
Derslerinizde karşılaştığınız zorlukları aşmanıza yardımcı olmak, projelerinizde fikir ortağınız olmak ve eğitim süreçlerinizi daha verimli hale getirmek için buradayım. 

Özel Eren Fen ve Teknoloji Lisesi'nin kurumsal değerlerini temsil ederek; profesyonel, yardımcı ve çözüm odaklı bir yaklaşımla her türlü sorunuzda yanınızdayım.
"""

# --- 2. API VE MODEL YAPILANDIRMASI (404 ÇÖZÜMÜ) ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı! Lütfen Streamlit Secrets kısmını kontrol edin.")
    st.stop()

@st.cache_resource
def model_hazirla():
    # 404 hatalarını önlemek için dinamik model seçimi
    try:
        modeller = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        tercihler = ['models/gemini-1.5-flash', 'gemini-1.5-flash', 'models/gemini-pro']
        for t in tercihler:
            if t in modeller:
                return genai.GenerativeModel(t)
        return genai.GenerativeModel(modeller[0])
    except:
        return genai.GenerativeModel('gemini-1.5-flash')

model_engine = model_hazirla()

# --- 3. DOSYA OKUMA FONKSİYONLARI (PDF OKUYAMAMA ÇÖZÜMÜ) ---
def metin_ayikla(dosya):
    try:
        if dosya.type == "application/pdf":
            okuyucu = PdfReader(dosya)
            return "\n".join([sayfa.extract_text() for sayfa in okuyucu.pages if sayfa.extract_text()])
        elif dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(dosya)
            return "\n".join([p.text for p in doc.paragraphs])
        return None
    except Exception as e:
        return f"Hata: {e}"

# --- 4. ARAYÜZ TASARIMI ---
with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=150)
    st.divider()
    mod = st.selectbox("Asistan Modu", ["Eren AI Asistanı", "Akademik Destek", "Veli Bilgilendirme"])
    st.divider()
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Dosya Yükleme ve Giriş Alanı
with st.container():
    col1, col2 = st.columns([1, 4])
    with col1:
        yuklenen_dosya = st.file_uploader("Dosya Seç", type=['png','jpg','jpeg','pdf','docx'], label_visibility="collapsed")
    with col2:
        kullanici_sorusu = st.chat_input("Eren AI'ya bir soru sorun...")

# Sohbet Geçmişini Göster
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 5. YANIT ÜRETİM MANTIĞI (AKILLI ODAKLANMA) ---
if kullanici_sorusu:
    st.session_state.messages.append({"role": "user", "content": kullanici_sorusu})
    with st.chat_message("user"):
        st.markdown(kullanici_sorusu)

    with st.chat_message("assistant"):
        cevap_alani = st.empty()
        
        # 1. Kimlik Kontrolü
        if any(k in kullanici_sorusu.lower() for k in ["kimsin", "adın ne", "necisin"]):
            cevap_alani.markdown(EREN_AI_KIMLIK)
            st.session_state.messages.append({"role": "assistant", "content": EREN_AI_KIMLIK})
        
        else:
            cevap_alani.markdown("⚡ *İşleniyor...*")
            try:
                # Arka Plan Komutu
                talimat = f"Sen Özel Eren Fen ve Teknoloji Lisesi resmi asistanı Eren AI'sın. Mod: {mod}."
                prompt_parcalari = [talimat, kullanici_sorusu]
                
                # 2. Akıllı Dosya Odaklanma
                # Sadece soruda dosya/belge kelimesi geçiyorsa içeriği modele ekle
                dosya_kelimeleri = ["dosya", "belge", "pdf", "içerik", "yüklediğim", "oku", "özet"]
                dosyaya_baksin_mi = any(k in kullanici_sorusu.lower() for k in dosya_kelimeleri)

                if yuklenen_dosya:
                    if yuklenen_dosya.type.startswith("image/"):
                        prompt_parcalari.append(PIL.Image.open(yuklenen_dosya))
                    elif dosyaya_baksin_mi:
                        icerik = metin_ayikla(yuklenen_dosya)
                        if icerik:
                            prompt_parcalari.append(f"\n--- BELGE İÇERİĞİ ---\n{icerik}")

                # Modelden Yanıt Al
                response = model_engine.generate_content(prompt_parcalari)
                
                if response.text:
                    cevap_alani.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
            
            except Exception as e:
                cevap_alani.error(f"Sistem Hatası: {str(e)}")
