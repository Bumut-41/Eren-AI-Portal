import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from PIL import Image
from docx import Document
from pptx import Presentation
import io
import re

# --- SİSTEM AYARLARI ---
st.set_page_config(page_title="Eren AI | Kurumsal Portal", page_icon="🛡️", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı!")
    st.stop()

model = genai.GenerativeModel('gemini-3-flash-preview')

# --- KURUMSAL TABAN ---
OKUL_BILGILERI = "Özel Eren Fen ve Teknoloji Lisesi (https://eren.k12.tr/)"

def metin_temizle(metin):
    metin = re.sub(r'\*\*|\$|\*', '', metin)
    return metin.strip()

def pptx_olustur(icerik):
    try:
        prs = Presentation("template.pptx")
        while len(prs.slides) > 0:
            r_id = prs.slides._sldIdLst[0].rId
            prs.part.drop_rel(r_id)
            del prs.slides._sldIdLst[0]
    except:
        prs = Presentation()
    
    parcalar = re.split(r'Slayt \d+:', icerik)
    for parca in parcalar:
        if len(parca.strip()) < 10: continue
        layout = prs.slide_layouts[1] if len(prs.slide_layouts) > 1 else prs.slide_layouts[0]
        slide = prs.slides.add_slide(layout)
        satirlar = parca.strip().split('\n')
        if slide.shapes.title: slide.shapes.title.text = metin_temizle(satirlar[0])
        for shape in slide.placeholders:
            if shape.placeholder_format.type == 2:
                tf = shape.text_frame
                tf.text = ""
                for satir in satirlar[1:]:
                    temiz = metin_temizle(satir)
                    if temiz:
                        p = tf.add_paragraph()
                        p.text = temiz
                        p.level = 0
    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer

# --- ANA ARAYÜZ ---
with st.sidebar:
    st.title("🛡️ Eren AI")
    st.info("v15.4: Zorunlu Dosya Analizi Aktif")

if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# Giriş Alanı
with st.container():
    yuklenen_dosya = st.file_uploader("Özetlenecek Belgeyi Yükleyin", type=['pdf','docx','png','jpg','pptx'], key="main_uploader")
    soru = st.chat_input("Yüklediğim dosyayı özetle veya analiz et...")

if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"): st.markdown(soru)

    with st.chat_message("assistant"):
        islem = st.status("🛡️ Dosya içeriği zorla okunuyor...")
        try:
            # ÖNCE DOSYA İÇERİĞİNİ HAZIRLA
            dosya_icerigi = ""
            gorsel_verisi = None

            if yuklenen_dosya:
                if yuklenen_dosya.type.startswith("image/"):
                    gorsel_verisi = Image.open(yuklenen_dosya)
                    dosya_icerigi = "[Görsel Yüklendi]"
                elif yuklenen_dosya.type == "application/pdf":
                    reader = PdfReader(yuklenen_dosya)
                    pdf_text = ""
                    for page in reader.pages:
                        pdf_text += page.extract_text() + "\n"
                    dosya_icerigi = f"DİKKAT! KULLANICI ŞU DOSYAYI YÜKLEDİ VE ÖZETİNİ İSTİYOR:\n--- DOSYA METNİ ---\n{pdf_text}\n--- METİN SONU ---"
            
            # MODELİ BESLE (Dosya içeriğini en tepeye koyduk)
            besleme = []
            if dosya_icerigi: besleme.append(dosya_icerigi)
            if gorsel_verisi: besleme.append(gorsel_verisi)
            
            besleme.append(f"Talimat: Sen {OKUL_BILGILERI} asistanısın. Eğer yukarıda bir dosya metni varsa SADECE O METNİ kullanarak '{soru}' isteğini yerine getir. Eğer dosya yoksa kullanıcıyı uyar. Sunum formatı: 'Slayt X: [Başlık]'.")
            
            response = model.generate_content(besleme)
            
            if response:
                islem.update(label="✅ Analiz Tamamlandı", state="complete")
                st.markdown(response.text)
                
                # Sadece cevap geldiyse butonları göster
                st.divider()
                c1, c2 = st.columns(2)
                with c1: st.download_button("📊 Sunum Olarak İndir", data=pptx_olustur(response.text), file_name="Analiz_Sunum.pptx")
                with c2: st.download_button("📄 Metin Olarak İndir", data=io.BytesIO(response.text.encode()), file_name="Analiz.txt")
                
                st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Kritik Hata: {e}")
