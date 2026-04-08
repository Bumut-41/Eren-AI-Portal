import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from PIL import Image, ImageDraw
import pdf2image
import pandas as pd
from docx import Document
from pptx import Presentation
import io
import re # Metin temizleme için

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

# --- GELİŞMİŞ DOSYA ÜRETİM MOTORLARI (v14.3) ---

def metin_temizle(metin):
    # Markdown ve LaTeX sembollerini temizler
    metin = metin.replace('**', '').replace('*', '').replace('$', '')
    metin = metin.replace('\\times', 'x').replace('\\cdot', '.').replace('^{', '^').replace('}', '')
    return metin.strip()

def word_olustur(icerik):
    doc = Document()
    doc.add_heading('Özel Eren Fen ve Teknoloji Lisesi', 0)
    for line in icerik.split('\n'):
        temiz_line = line.replace('**', '').replace('$', '')
        if temiz_line.startswith('Slayt') or temiz_line.startswith('###'):
            doc.add_heading(temiz_line.replace('#', '').strip(), level=1)
        else:
            doc.add_paragraph(temiz_line)
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def pptx_olustur(icerik):
    prs = Presentation()
    # İçeriği "Slayt" anahtar kelimesine göre böl
    parcalar = re.split(r'Slayt \d+:', icerik)
    
    for i, parca in enumerate(parcalar):
        if len(parca.strip()) < 10: continue
        
        slide_layout = prs.slide_layouts[1]
        slide = prs.slides.add_slide(slide_layout)
        
        satirlar = parca.strip().split('\n')
        
        # Başlık temizleme
        slide.shapes.title.text = metin_temizle(satirlar[0])
        
        # İçerik temizleme ve maddeleştirme
        tf = slide.placeholders[1].text_frame
        tf.text = "" # Temiz başla
        
        for satir in satirlar[1:]:
            temiz_satir = metin_temizle(satir)
            if temiz_satir:
                p = tf.add_paragraph()
                p.text = temiz_satir
                p.level = 0

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
        d.text((20, y), metin_temizle(satir)[:85], fill=(0, 0, 0))
        y += 25
    buffer = io.BytesIO()
    img.save(buffer, format=format)
    buffer.seek(0)
    return buffer

# --- DOSYA OKUMA VE ARAYÜZ ---
def metin_ayikla(dosya):
    try:
        if dosya.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return "\n".join([p.text for p in Document(dosya).paragraphs])
        elif "spreadsheet" in dosya.type or "csv" in dosya.type:
            df = pd.read_excel(dosya) if "spreadsheet" in dosya.type else pd.read_csv(dosya)
            return f"TABLO VERİSİ:\n{df.to_string()}"
        return None
    except Exception as e:
        return f"Dosya Okuma Hatası: {e}"

with st.sidebar:
    try: st.image("Logo.png", use_container_width=True)
    except: st.subheader("🛡️ Eren AI")
    st.markdown("### **Akademik Çıktı Merkezi v14.3**")
    st.info("PowerPoint ve Metin temizleme motoru optimize edildi.")
    st.divider()
    st.caption("© 2026 Eren Eğitim Kurumları")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        dosya = st.file_uploader("Dosya", type=['pdf','docx','xlsx','pptx','csv','png','jpg','jpeg'], key="eren_master_v14_3", label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Ders notu, sunum taslağı veya analiz isteyin...")

if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"): st.markdown(soru)

    with st.chat_message("assistant"):
        durum = st.status("🛡️ Eren AI Akademik Analiz Yapıyor...")
        try:
            system_instruction = f"""
            Sen Özel Eren Fen ve Teknoloji Lisesi akademik asistanısın. {OKUL_BILGILERI}
            
            ÖNEMLİ: Sunum taleplerinde daima "Slayt 1: [Başlık]", "Slayt 2: [Başlık]" yapısını kullan. 
            Matematiksel ifadeleri sade yazmaya çalış.
            """
            
            prompt_parts = [system_instruction, soru]
            
            if dosya:
                # Dosya işleme mantığı (v14.2 ile aynı)
                if any(k in soru.lower() for k in ["dosya", "oku", "analiz"]):
                    if dosya.type.startswith("image/"):
                        prompt_parts.append(Image.open(dosya))
                    elif dosya.type == "application/pdf":
                        reader = PdfReader(dosya)
                        pdf_metni = "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
                        prompt_parts.append(f"İÇERİK:\n{pdf_metni}")
                    else:
                        ek_metin = metin_ayikla(dosya)
                        if ek_metin: prompt_parts.append(f"İÇERİK:\n{ek_metin}")

            response = model.generate_content(prompt_parts)
            
            if response:
                durum.update(label="✅ Çıktılar Optimize Edildi", state="complete")
                st.markdown(response.text)
                
                st.divider()
                st.write("📥 **Temizlenmiş Akademik Dosyalar:**")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1: st.download_button("📄 Word Belgesi", data=word_olustur(response.text), file_name="Eren_AI_Not.docx")
                with col2: st.download_button("📊 Sunum (PPTX)", data=pptx_olustur(response.text), file_name="Eren_AI_Sunum.pptx")
                with col3: st.download_button("📈 Excel Tablo", data=excel_olustur(response.text), file_name="Eren_AI_Veri.xlsx")
                with col4: st.download_button("🖼️ PNG Görsel", data=gorsel_olustur(response.text, "PNG"), file_name="Eren_AI_Ozet.png")

                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
        except Exception as e:
            st.error(f"Sistem hatası: {str(e)}")
