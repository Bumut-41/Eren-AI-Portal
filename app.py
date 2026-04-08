import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import pandas as pd
from docx import Document
from pptx import Presentation
from PIL import Image

# --- SİSTEM AYARLARI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı!")
    st.stop()

# --- VERİ AYIKLAMA MOTORU ---
def veri_ayikla(belge):
    try:
        if belge.type == "application/pdf":
            pdf = PdfReader(belge)
            return "\n".join([sayfa.extract_text() for sayfa in pdf.pages if sayfa.extract_text()])
        elif belge.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return "\n".join([p.text for p in Document(belge).paragraphs])
        elif "spreadsheet" in belge.type or "csv" in belge.type:
            df = pd.read_excel(belge) if "spreadsheet" in belge.type else pd.read_csv(belge)
            return f"Tablo Verisi:\n{df.head(50).to_string()}"
        return None
    except Exception as e:
        return f"HATA: {str(e)}"

# --- MODEL ---
# Listenizde çalıştığı kesinleşen en güncel önizleme modeli
model = genai.GenerativeModel('gemini-3-flash-preview')

# --- ARAYÜZ ---
with st.sidebar:
    st.title("🛡️ Eren AI")
    st.markdown("### Özel Eren Fen ve Teknoloji Lisesi")
    st.divider()
    mod = st.selectbox("Asistan Modu", ["Döküman Analizi", "Genel Asistan"])

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Giriş ve Dosya Paneli
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        # 'key' kullanımı dosyanın bellekte kalmasını sağlar
        dosya = st.file_uploader("Dosya Seç", type=['pdf','docx','xlsx','csv','png','jpg'], key="eren_uploader", label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya sorunuzu iletin...")

# --- İŞLEME ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        durum = st.status("🛡️ İşlem başlatıldı...")
        
        try:
            icerik_metni = ""
            gorsel_verisi = None
            
            # DOSYA KONTROLÜ
            if dosya:
                durum.write(f"📂 Dosya tespit edildi: {dosya.name}")
                if dosya.type.startswith("image/"):
                    gorsel_verisi = Image.open(dosya)
                    durum.write("🖼️ Görsel işleniyor...")
                else:
                    icerik_metni = veri_ayikla(dosya)
                    if icerik_metni:
                        durum.write(f"✅ {len(icerik_metni)} karakter metin ayıklandı.")
                    else:
                        durum.warning("⚠️ Dosya bulundu ancak metin çıkarılamadı.")

            # PROMPT PAKETLEME
            sistem_talimati = f"Sen Eren AI'sın. Profesyonel okul asistanısın. Yüklenen dosyaları dikkatle oku. Mod: {mod}."
            
            if icerik_metni:
                # Dosya içeriğini sorunun başına KESİN olarak ekliyoruz
                tam_mesaj = f"{sistem_talimati}\n\n--- DOSYA İÇERİĞİ ---\n{icerik_metni}\n\n--- SORU ---\n{soru}"
            else:
                tam_mesaj = f"{sistem_talimati}\n\n{soru}"

            # YANIT ÜRETİMİ
            if gorsel_verisi:
                response = model.generate_content([sistem_talimati, soru, gorsel_verisi])
            else:
                response = model.generate_content(tam_mesaj)
            
            if response.text:
                durum.update(label="✅ Analiz Tamamlandı", state="complete")
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            durum.update(label="❌ Hata Oluştu", state="error")
            st.error(f"Sistem hatası: {str(e)}")
