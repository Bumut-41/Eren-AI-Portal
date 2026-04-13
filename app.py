import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from PIL import Image
import io
import datetime

# --- DÖKÜMAN KÜTÜPHANELERİ ---
from docx import Document 
from pptx import Presentation 
import pandas as pd 
from fpdf import FPDF # fpdf2 kütüphanesi
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

# --- GÜNCEL DÖKÜMAN ÜRETİM MOTORLARI ---

def create_word_file(text, topic):
    doc = Document()
    doc.add_heading('Özel Eren Fen ve Teknoloji Lisesi', 0)
    doc.add_heading(f'Akademik Çalışma Fasikülü: {topic}', level=1)
    doc.add_paragraph(text)
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

def create_pdf_file(text):
    # "fname" hatasını önlemek için output() kullanımı güncellendi
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Ozel Eren Fen ve Teknoloji Lisesi", ln=True, align='C')
    pdf.ln(10)
    # Metni güvenli karakterlere dönüştür
    safe_text = text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, txt=safe_text)
    # Çıktıyı bayt dizisi olarak döndür
    return pdf.output()

def create_pptx_file(text, topic):
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = topic
    slide.placeholders[1].text = text[:800]
    bio = io.BytesIO()
    prs.save(bio)
    return bio.getvalue()

# --- DOSYA OKUMA MOTORU ---
def read_file_content(uploaded_file):
    content = ""
    try:
        if uploaded_file.type == "application/pdf":
            reader = PdfReader(uploaded_file)
            for page in reader.pages:
                content += page.extract_text() + "\n"
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            content = docx2python(uploaded_file).text
        elif uploaded_file.name.endswith(('xlsx', 'csv')):
            df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('xlsx') else pd.read_csv(uploaded_file)
            content = df.to_string()
    except Exception as e:
        content = f"Okuma Hatası: {str(e)}"
    return content

# --- ANA PANEL ---
with st.sidebar:
    st.markdown("### 🛡️ Eren AI Education")
    st.info("Kurumsal Akademik Portal v26.2")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

uploaded_file = st.file_uploader("Dosya Yükle", type=['pdf','docx','xlsx','pptx','csv','png','jpg','jpeg'])
user_input = st.chat_input("Sorunuzu buraya yazın...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.status("🔍 İşleniyor...") as status:
            prompt = [f"Sen Eren AI'sın. Özel Eren Fen ve Teknoloji Lisesi için derin akademik analiz yap.", user_input]
            if uploaded_file:
                if uploaded_file.type.startswith("image/"):
                    prompt.append(Image.open(uploaded_file))
                else:
                    prompt.append(read_file_content(uploaded_file))

            response = model.generate_content(prompt)
            full_text = response.text
            st.markdown(full_text)
            st.session_state.messages.append({"role": "assistant", "content": full_text})

            st.divider()
            st.write("### 📥 Akademik Çıktı Merkezi")
            c1, c2, c3 = st.columns(3)
            c1.download_button("📄 Word", create_word_file(full_text, "Analiz"), "ErenAI.docx")
            c2.download_button("📕 PDF", create_pdf_file(full_text), "ErenAI.pdf")
            c3.download_button("📽️ PPTX", create_pptx_file(full_text, "Sunum"), "ErenAI.pptx")
            status.update(label="✅ Tamamlandı", state="complete")
