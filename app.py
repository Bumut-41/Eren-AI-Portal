import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from PIL import Image
from pptx import Presentation
import io
import re

# --- AYARLAR ---
st.set_page_config(page_title="Eren AI | Kurumsal", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Key eksik!")
    st.stop()

model = genai.GenerativeModel('gemini-3-flash-preview')

# --- ŞABLON TEMİZLEME MOTORU ---
def sunum_hazirla(icerik):
    try:
        prs = Presentation("template.pptx")
        # Şablonu tamamen boşalt (Eski uçak resimlerini ve latin metinlerini siler)
        while len(prs.slides) > 0:
            rId = prs.slides._sldIdLst[0].rId
            prs.part.drop_rel(rId)
            del prs.slides._sldIdLst[0]
    except:
        prs = Presentation()

    # Modelden gelen "Slayt X:" yapılarını parçala
    slaytlar = re.split(r'Slayt \d+:', icerik)
    for s in slaytlar:
        if len(s.strip()) < 5: continue
        # Şablonun tasarımını (layout) kullanarak yeni slayt ekle
        slide = prs.slides.add_slide(prs.slide_layouts[1] if len(prs.slide_layouts)>1 else prs.slide_layouts[0])
        lines = s.strip().split('\n')
        if slide.shapes.title:
            slide.shapes.title.text = lines[0].replace("*", "")
        if len(lines) > 1 and slide.placeholders:
            body = slide.placeholders[1]
            body.text = "\n".join(lines[1:]).replace("*", "")
            
    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf

# --- ARAYÜZ ---
st.sidebar.title("🛡️ Eren AI v15.5")
st.sidebar.info("Dosya Okuma Garantili Sürüm")

# Dosya Yükleme Alanı (En Üstte ve Sabit)
yuklenen_dosya = st.file_uploader("Analiz Edilecek PDF veya Görsel", type=['pdf', 'png', 'jpg'])

# Kullanıcı Sorusu
soru = st.chat_input("Yüklediğim dosyayı detaylıca analiz et...")

if soru:
    with st.chat_message("user"):
        st.markdown(soru)
    
    with st.chat_message("assistant"):
        islem = st.status("🔍 Dosya katmanları taranıyor...")
        
        # DOSYA İÇERİĞİNİ ZORLA ÇEK
        besleme_listesi = ["Sen Özel Eren Fen ve Teknoloji Lisesi asistanısın. Aşağıdaki dosyayı SADECE içindeki bilgilere sadık kalarak analiz et."]
        
        if yuklenen_dosya:
            if yuklenen_dosya.type == "application/pdf":
                okuyucu = PdfReader(yuklenen_dosya)
                metin = "\n".join([sayfa.extract_text() for sayfa in okuyucu.pages if sayfa.extract_text()])
                if metin:
                    besleme_listesi.append(f"DOSYA İÇERİĞİ:\n{metin}")
                    islem.write("✅ PDF metni başarıyla çıkarıldı.")
            elif yuklenen_dosya.type.startswith("image/"):
                besleme_listesi.append(Image.open(yuklenen_dosya))
                islem.write("✅ Görsel verisi işleme alındı.")
        
        besleme_listesi.append(f"Kullanıcı İsteği: {soru}")
        
        try:
            # Modeli Çalıştır
            yanit = model.generate_content(besleme_listesi)
            islem.update(label="✅ Analiz Bitti", state="complete")
            
            st.markdown(yanit.text)
            
            # Sunum İndirme Butonu
            st.divider()
            st.download_button("📊 Sunumu İndir (Kurumsal Şablon)", 
                             data=sunum_hazirla(yanit.text), 
                             file_name="Eren_AI_Analiz.pptx")
                             
        except Exception as e:
            st.error(f"Hata oluştu: {e}")
