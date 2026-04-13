import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from PIL import Image, ImageDraw, ImageFont
import io
import datetime

# --- DÖKÜMAN KÜTÜPHANELERİ ---
from docx import Document 
from pptx import Presentation 
import pandas as pd 
from fpdf import FPDF 
from docx2python import docx2python 
from pptx import Presentation as ReadPPTX 

# --- SİSTEM AYARLARI ---
st.set_page_config(page_title="Eren AI | Akademik Portal", page_icon="🛡️", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı!")
    st.stop()

model = genai.GenerativeModel('gemini-3-flash-preview')

# --- DÖKÜMAN ÜRETİM FONKSİYONLARI ---

def create_word(text, topic):
    doc = Document()
    doc.add_heading('Özel Eren Fen ve Teknoloji Lisesi', 0)
    doc.add_heading(f'Akademik Fasikül: {topic}', level=1)
    doc.add_paragraph(text)
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Ozel Eren Fen ve Teknoloji Lisesi", ln=True, align='C')
    pdf.ln(10)
    safe_text = text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, txt=safe_text)
    return pdf.output()

def create_pptx(text, topic):
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = topic
    slide.placeholders[1].text = text[:800]
    bio = io.BytesIO()
    prs.save(bio)
    return bio.getvalue()

def create_excel(text):
    df = pd.DataFrame({"Analiz": [text[:500]], "Tarih": [datetime.datetime.now()]})
    bio = io.BytesIO()
    with pd.ExcelWriter(bio, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return bio.getvalue()

def create_image(text):
    img = Image.new('RGB', (800, 600), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((10,10), f"Eren AI Analiz - {datetime.date.today()}", fill=(0,0,0))
    d.text((10,50), text[:500], fill=(50,50,50))
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    return bio.getvalue()

# --- SOL MENÜ (ANAYASAL SABİT) ---
with st.sidebar:
    st.markdown("### **🛡️ Eren AI Education**")
    st.markdown("**Eren Yapay Zeka Sistemleri**")
    st.success("**Anayasal Mod:** Her soru için bireysel ve derin analiz zorunludur.")
    
    st.markdown("---")
    st.markdown("### **📖 Sistem Rehberi**")
    st.info("""
    1. **Akademik dökümanlarınızı** "Dosya Yükleme" alanından iletebilirsiniz.
    2. Sorularınızı **metin alanına girerek** etkileşimi başlatabilirsiniz.
    """)
    st.divider()
    st.caption("© 2026 Eren Eğitim Kurumları")

# --- ANA ARAYÜZ ---
st.title("🛡️ Akademik Müfredat ve Analiz Portalı")

# Soru ve Dosya Girişini Birleştiriyoruz
with st.container(border=True):
    uploaded_file = st.file_uploader("Dosya Yükleme (PDF, Word, Excel, PPTX, Görsel)", type=['pdf','docx','xlsx','pptx','csv','png','jpg','jpeg'], label_visibility="collapsed")
    user_input = st.chat_input("Eren AI'a sormak istediğin soruyu bu alana girebilirsiniz.")

# Sohbet Alanı
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- İŞLEMCİ ---
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.status("🔍 Eren AI Akademik Analizi Yürütüyor...") as status:
            instruction = """Sen Eren AI'sın. Özel Eren Fen ve Teknoloji Lisesi'nin Yapay Zekasısın.
            Giriş: 'Eren AI, Özel Eren Fen ve Teknoloji Lisesi'nin Yapay Zekası olarak size hizmet ediyorum.'
            1. Her soruyu teker teker analiz et.
            2. Kavramsal Derinlik, Analitik İnceleme ve Analitik Sorgulama başlıklarını kullan.
            3. Sokratik yöntemle öğret, doğrudan cevap verme."""
            
            prompt = [instruction, user_input]
            if uploaded_file:
                # Dosya okuma logic buraya gelecek (v26.2'deki gibi)
                prompt.append("Dosya yüklendi.")

            response = model.generate_content(prompt)
            full_text = response.text
            st.markdown(full_text)
            st.session_state.messages.append({"role": "assistant", "content": full_text})

            # DÖKÜMAN PANELİ (Görsel Dahil)
            st.divider()
            st.write("### 📥 Akademik Çıktı Merkezi")
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.download_button("📄 Word", create_word(full_text, "Analiz"), "ErenAI.docx")
            c2.download_button("📕 PDF", create_pdf(full_text), "ErenAI.pdf")
            c3.download_button("📽️ PPTX", create_pptx(full_text, "Sunum"), "ErenAI.pptx")
            c4.download_button("📊 Excel", create_excel(full_text), "ErenAI.xlsx")
            c5.download_button("🖼️ Görsel", create_image(full_text), "ErenAI.png")
            
            status.update(label="✅ Analiz ve Dökümanlar Hazır", state="complete")
