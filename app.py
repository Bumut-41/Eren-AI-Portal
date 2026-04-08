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

# --- GELİŞMİŞ DOSYA ÜRETİM MOTORLARI (v14.2) ---

def word_olustur(icerik):
    doc = Document()
    doc.add_heading('Özel Eren Fen ve Teknoloji Lisesi', 0)
    for line in icerik.split('\n'):
        if line.startswith('Slayt') or line.startswith('###') or line.startswith('**Slayt'):
            doc.add_heading(line.replace('#', '').strip(), level=1)
        else:
            doc.add_paragraph(line)
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def pptx_olustur(icerik):
    prs = Presentation()
    # İçeriği "Slayt" anahtar kelimesine göre bölerek sayfalar oluşturur
    parcalar = icerik.split('Slayt')
    for i, parca in enumerate(parcalar):
        if len(parca.strip()) < 10: continue
        
        slide_layout = prs.slide_layouts[1]
        slide = prs.slides.add_slide(slide_layout)
        
        satirlar = parca.strip().split('\n')
        # Slayt başlığını temizle ve ayarla
        slide.shapes.title.text = satirlar[0].replace(':', '').strip()
        
        # İçeriği madde işaretleri olarak ekle
        tf = slide.placeholders[1].text_frame
        tf.text = "\n".join(satirlar[1:])

    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer

def excel_olustur(icerik):
    df = pd.DataFrame(icerik.split('\n'), columns=["Akademik İçerik"])
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    buffer.seek(0)
    return buffer

def gorsel_olustur(icerik, format="PNG"):
    img = Image.new('RGB', (800, 1200), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((20, 20), "Özel Eren Fen ve Teknoloji Lisesi", fill=(26, 95, 122))
    y = 70
    for satir in icerik.split('\n')[:40]:
        d.text((20, y), satir[:85], fill=(0, 0, 0))
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
    
    st.markdown("### **Akademik Çıktı Merkezi v14.2**")
    st.info("Sunum, Ders Notu ve Tablo üretim modülleri optimize edildi.")
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
        dosya = st.file_uploader("Dosya", type=['pdf','docx','xlsx','pptx','csv','png','jpg','jpeg'], key="eren_master_v14", label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Ders notu, sunum taslağı veya analiz isteyin...")

# --- AKILLI İŞLEMCİ ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        durum = st.status("🛡️ Eren AI Akademik Analiz Yapıyor...")
        
        try:
            system_instruction = f"""
            Sen Özel Eren Fen ve Teknoloji Lisesi akademik asistanısın. {OKUL_BILGILERI}
            
            ÖNEMLİ: Eğer kullanıcı bir sunum veya ders notu hazırlamanı isterse, yanıtını "Slayt 1: Başlık", "Slayt 2: Başlık" formatında bölümlere ayırarak ver. 
            Bu, dosyaların düzgün oluşturulması için kritiktir.
            """
            
            prompt_parts = [system_instruction, soru]
            
            if dosya:
                # Akıllı bağlam kontrolü
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
                durum.update(label="✅ İçerik Hazır", state="complete")
                st.markdown(response.text)
                
                # İNDİRME PANELİ
                st.divider()
                st.write("📥 **Akademik Dosya Çıktıları:**")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.download_button("📄 Word Belgesi", data=word_olustur(response.text), file_name="Eren_AI_Ders_Notu.docx")
                with col2:
                    st.download_button("📊 Sunum (PPTX)", data=pptx_olustur(response.text), file_name="Eren_AI_Sunum.pptx")
                with col3:
                    st.download_button("📈 Excel Tablo", data=excel_olustur(response.text), file_name="Eren_AI_Veri.xlsx")
                with col4:
                    st.download_button("🖼️ PNG Görsel", data=gorsel_olustur(response.text, "PNG"), file_name="Eren_AI_Ozet.png")

                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
        except Exception as e:
            durum.update(label="❌ Hata", state="error")
            st.error(f"Sistem hatası: {str(e)}")
