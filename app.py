import streamlit as st
import google.generativeai as genai
import PIL.Image
import os
from PyPDF2 import PdfReader
from docx import Document
import io

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

# API Yapılandırması
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Secrets içinde API anahtarı bulunamadı!")
    st.stop()

# --- 2. DOSYA OKUMA FONKSİYONU ---
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

# --- 3. DİNAMİK MODEL SEÇİCİ (404 VE VERSİYON ÇÖZÜMÜ) ---
@st.cache_resource
def model_getir():
    # Sistemdeki aktif modelleri tarayarak 404 hatasını engeller
    try:
        mevcut_modeller = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for tercih in ['models/gemini-1.5-flash', 'gemini-1.5-flash', 'models/gemini-pro']:
            if tercih in mevcut_modeller:
                return genai.GenerativeModel(tercih)
        return genai.GenerativeModel(mevcut_modeller[0])
    except:
        return genai.GenerativeModel('gemini-1.5-flash')

model_engine = model_getir()

# --- 4. TASARIM VE SIDEBAR (YAN ÇUBUK) ---
with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=150) # Tasarımı korur
    
    st.divider()
    mod = st.selectbox("Asistan Modu", ["Eren AI Asistanı", "Akademik Destek", "Veli Bilgilendirme"])
    st.divider()
    st.caption("© Baris Umut / 2026 Özel Eren Fen ve Teknoloji Lisesi")

# Ana Ekran Başlığı
st.title("🛡️ Eren AI Portalı")

# Sohbet Geçmişi
if "messages" not in st.session_state:
    st.session_state.messages = []

# Giriş Alanları (Üstte Sabit Tasarım)
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        yukle = st.file_uploader("Dosya Seç", type=['png','jpg','jpeg','pdf','docx'], label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya bir soru sorun...")

# Eski Mesajları Yazdır
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 5. AKILLI YANIT VE ODAKLANMA MANTIĞI ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("⚡ *İşleniyor...*")
        
        try:
            # Sistem talimatı
            prompt_parcalari = [f"Sen Eren AI'sın. Mod: {mod}. Kurumsal ve yardımcı ol.", soru]
            
            # Akıllı Odaklanma: Soru dosyayla mı ilgili?
            dosya_anahtar_kelimeler = ["dosya", "belge", "doküman", "pdf", "word", "içerik", "yüklediğim", "bu", "özetle", "anlat"]
            dosya_sorusu_mu = any(kelime in soru.lower() for kelime in dosya_anahtar_kelimeler)

            if yukle:
                if yukle.type.startswith("image/"):
                    prompt_parcalari.append(PIL.Image.open(yukle))
                elif dosya_sorusu_mu:
                    # Sadece dosya sorulduğunda içeriği ekle
                    icerik_metni = dosya_metnini_oku(yukle)
                    if icerik_metni:
                        prompt_parcalari.append(f"\n--- BELGE İÇERİĞİ ---\n{icerik_metni}")

            # Yanıt üret
            yanit = model_engine.generate_content(prompt_parcalari)
            
            if yanit.text:
                placeholder.markdown(yanit.text)
                st.session_state.messages.append({"role": "assistant", "content": yanit.text})
            else:
                placeholder.error("Modelden yanıt alınamadı.")
                
        except Exception as e:
            placeholder.error(f"Sistem Hatası: {str(e)}")
