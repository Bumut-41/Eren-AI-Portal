import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from PIL import Image, ImageDraw
import pdf2image
import pandas as pd
from docx import Document
from pptx import Presentation
import io

# --- SİSTEM AYARLARI ---
st.set_page_config(page_title="Eren AI | Akademik Portal", page_icon="🛡️", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı!")
    st.stop()

model = genai.GenerativeModel('gemini-3-flash-preview')

# --- ÖZEL EREN FEN VE TEKNOLOJİ LİSESİ BİLGİ TABANI ---
OKUL_BILGILERI = "Kurum: Özel Eren Fen ve Teknoloji Lisesi | Web: https://eren.k12.tr/"

# --- DOSYA ÜRETİM MOTORLARI (v14.1) ---

def word_olustur(icerik):
    doc = Document()
    doc.add_heading('Özel Eren Fen ve Teknoloji Lisesi', 0)
    doc.add_paragraph(icerik)
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def pptx_olustur(icerik):
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = "Eren AI Akademik Notlar"
    slide.placeholders[1].text = icerik[:1000] # İlk 1000 karakteri slayta ekler
    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer

def excel_olustur(icerik):
    # Metni satırlara bölüp Excel'e aktarır
    df = pd.DataFrame(icerik.split('\n'), columns=["Akademik İçerik"])
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    buffer.seek(0)
    return buffer

def gorsel_olustur(icerik, format="PNG"):
    # Basit bir görsel oluşturma motoru
    img = Image.new('RGB', (800, 1000), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((20, 20), "Özel Eren Fen ve Teknoloji Lisesi", fill=(26, 95, 122))
    y = 60
    for satir in icerik.split('\n')[:35]: # Maksimum 35 satır yazar
        d.text((20, y), satir[:90], fill=(0, 0, 0))
        y += 25
    buffer = io.BytesIO()
    img.save(buffer, format=format)
    buffer.seek(0)
    return buffer

# --- DOSYA OKUMA FONKSİYONU ---
def metin_ayikla(dosya):
    try:
        if dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return "\n".join([p.text for p in Document(dosya).paragraphs])
        elif "spreadsheet" in dosya.type or "csv" in dosya.type:
            df = pd.read_excel(dosya) if "spreadsheet" in dosya.type else pd.read_csv(dosya)
            return f"TABLO VERİSİ:\n{df.to_string()}"
        elif "presentationml" in dosya.type:
            prs = Presentation(dosya)
            return "\n".join([shape.text for slide in prs.slides for shape in slide.shapes if hasattr(shape, "text")])
        return None
    except Exception as e:
        return f"Dosya Okuma Hatası: {e}"

# --- SOL MENÜ ---
with st.sidebar:
    try:
        st.image("Logo.png", use_container_width=True)
    except:
        st.subheader("🛡️ Eren AI")
    
    st.markdown("### **Çoklu Format Desteği v14.1**")
    st.info("İçerikleri Word, Excel, PPT veya Görsel olarak indirebilirsiniz.")
    st.divider()
    st.caption("© 2026 Eren Eğitim Kurumları")

# --- SOHBET GEÇMİŞİ ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- GİRİŞ PANELİ ---
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        dosya = st.file_uploader("Dosya", type=['pdf','docx','xlsx','pptx','csv','png','jpg','jpeg'], key="eren_final_v14", label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Ders notu hazırlatın veya dosya analiz ettirin...")

# --- AKILLI İŞLEMCİ ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        durum = st.status("🛡️ Eren AI İçeriği Hazırlıyor...")
        
        try:
            system_instruction = f"""
            Sen Özel Eren Fen ve Teknoloji Lisesi'nin resmi "Eren AI" akademik asistanısın. {OKUL_BILGILERI}
            TEMEL KAYNAĞIN: https://eren.k12.tr/

            KRİTİK KURALLAR: 
            1. BAĞLAM YÖNETİMİ: Kullanıcı doğrudan dosyaya referans vermedikçe dosyayı görmezden gel.
            2. ÖĞRETMEN DESTEĞİ: Quiz, ödev veya ders notu taleplerini Fen Lisesi standartlarında cevap anahtarıyla hazırla.
            3. ÇIKTI FORMATI: Yanıtlarını her zaman çok düzenli ve başlıklar kullanarak ver.
            """
            
            prompt_parts = [system_instruction, soru]
            
            if dosya:
                analiz_kelimeleri = ["dosya", "belge", "doküman", "özet", "listele", "tablo", "analiz", "oku", "yüklediğim", "quiz", "soru", "ödev"]
                if any(kelime in soru.lower() for kelime in analiz_kelimeleri):
                    if dosya.type.startswith("image/"):
                        prompt_parts.append(Image.open(dosya))
                    elif dosya.type == "application/pdf":
                        reader = PdfReader(dosya)
                        pdf_metni = "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
                        if len(pdf_metni.strip()) > 50:
                            prompt_parts.append(f"İLGİLİ DOSYA İÇERİĞİ:\n{pdf_metni}")
                        else:
                            dosya.seek(0)
                            prompt_parts.extend(pdf2image.convert_from_bytes(dosya.read())[:5])
                    else:
                        ek_metin = metin_ayikla(dosya)
                        if ek_metin: prompt_parts.append(f"İLGİLİ DOSYA İÇERİĞİ:\n{ek_metin}")

            response = model.generate_content(prompt_parts)
            
            if response:
                durum.update(label="✅ Hazır", state="complete")
                st.markdown(response.text)
                
                # İNDİRME BUTONLARI
                st.divider()
                st.write("📥 **Bu içeriği şu formatta indir:**")
                
                b1, b2, b3, b4, b5 = st.columns(5)
                with b1:
                    st.download_button("📄 Word", data=word_olustur(response.text), file_name="Eren_AI_DersNotu.docx")
                with b2:
                    st.download_button("📊 PPTX", data=pptx_olustur(response.text), file_name="Eren_AI_Sunum.pptx")
                with b3:
                    st.download_button("📈 Excel", data=excel_olustur(response.text), file_name="Eren_AI_Tablo.xlsx")
                with b4:
                    st.download_button("🖼️ PNG", data=gorsel_olustur(response.text, "PNG"), file_name="Eren_AI_Gorsel.png")
                with b5:
                    st.download_button("📷 JPG", data=gorsel_olustur(response.text, "JPEG"), file_name="Eren_AI_Gorsel.jpg")

                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
        except Exception as e:
            durum.update(label="❌ Hata", state="error")
            st.error(f"Sistem hatası: {str(e)}")
