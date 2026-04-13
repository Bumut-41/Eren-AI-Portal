import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from PIL import Image
import io
import datetime

# --- DÖKÜMAN VE VERİ İŞLEME KÜTÜPHANELERİ ---
from docx import Document 
from pptx import Presentation 
import pandas as pd 
from fpdf import FPDF # fpdf2 kütüphanesinden gelir
from docx2python import docx2python 
from pptx import Presentation as ReadPPTX 

# --- SİSTEM AYARLARI ---
st.set_page_config(page_title="Eren AI | Akademik Portal", page_icon="🛡️", layout="wide")

# API Anahtarı Kontrolü
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı (GOOGLE_API_KEY) bulunamadı! Lütfen secrets.toml dosyasını kontrol edin.")
    st.stop()

model = genai.GenerativeModel('gemini-3-flash-preview')

# --- ÖZEL EREN FEN VE TEKNOLOJİ LİSESİ SABİTLERİ ---
OKUL_BILGILERI = "Kurum: Özel Eren Fen ve Teknoloji Lisesi | Akademik Yapay Zeka Sistemi"

# --- DÖKÜMAN ÜRETİM MOTORLARI (v26.1 GÜNCEL) ---

def create_word_file(text, topic):
    doc = Document()
    doc.add_heading('Özel Eren Fen ve Teknoloji Lisesi', 0)
    doc.add_heading(f'Akademik Çalışma Fasikülü: {topic}', level=1)
    doc.add_paragraph(f"Rapor Tarihi: {datetime.datetime.now().strftime('%d/%m/%Y')}")
    doc.add_paragraph("-" * 30)
    doc.add_paragraph(text)
    doc.add_paragraph("\n\n© Eren AI Education - Akademik Rehberlik Birimi")
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

def create_pdf_file(text, topic):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        # Standart font (Türkçe karakter desteği için fpdf2 gereklidir)
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Ozel Eren Fen ve Teknoloji Lisesi", ln=True, align='C')
        pdf.ln(10)
        # Metni Latin-1'e güvenli şekilde kodla (Hata önleyici)
        safe_text = text.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 10, txt=safe_text)
        return pdf.output(dest='S')
    except Exception as e:
        return f"PDF Hatası: {str(e)}".encode()

def create_pptx_file(text, topic):
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = topic
    slide.placeholders[1].text = "Eren AI Akademik Sunum Serisi"
    
    slide2 = prs.slides.add_slide(prs.slide_layouts[1])
    slide2.shapes.title.text = "Analiz Özeti"
    slide2.placeholders[1].text = text[:1000] + "..."
    
    bio = io.BytesIO()
    prs.save(bio)
    return bio.getvalue()

# --- DOSYA OKUMA MOTORLARI ---

def read_file_content(uploaded_file):
    content = ""
    try:
        if uploaded_file.type == "application/pdf":
            reader = PdfReader(uploaded_file)
            for page in reader.pages:
                content += page.extract_text() + "\n"
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            content = docx2python(uploaded_file).text
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
            prs = ReadPPTX(uploaded_file)
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        content += shape.text + "\n"
        elif uploaded_file.name.endswith(('xlsx', 'csv')):
            df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('xlsx') else pd.read_csv(uploaded_file)
            content = df.to_string()
    except Exception as e:
        content = f"Dosya okuma hatası: {str(e)}"
    return content

# --- ARAYÜZ VE SOHBET MANTIĞI ---

with st.sidebar:
    st.title("🛡️ Eren AI Education")
    st.subheader("v26.1 Akademik Portal")
    st.success("Anayasal Mod Aktif")
    st.info("Bu sistem, Özel Eren Fen ve Teknoloji Lisesi standartlarında derinlemesine analiz yapar.")
    st.divider()
    st.caption("© 2026 Eren Eğitim Kurumları")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Giriş ve Dosya Alanı
with st.container():
    uploaded_file = st.file_uploader("Ödev veya Veri Dosyası Yükle", type=['pdf','docx','xlsx','pptx','csv','png','jpg','jpeg'])
    user_input = st.chat_input("Analiz için sorunuzu yazın...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.status("🔍 Eren AI Akademik Süzgeçten Geçiriyor...") as status:
            try:
                # Anayasal Talimat Seti
                instruction = f"""
                Sen Eren AI'sın. {OKUL_BILGILERI}. 
                Giriş cümlen: 'Eren AI, Özel Eren Fen ve Teknoloji Lisesi'nin Yapay Zekası olarak size hizmet ediyorum.'
                
                KURALLAR:
                1. Materyaldeki her soruyu ## SORU [NO] şeklinde tek tek analiz et.
                2. '📚 Kavramsal ve Bilimsel Derinlik', '🔍 Analitik İnceleme ve Çözüm Stratejisi', '💡 Analitik Sorgulama ve Sentez' başlıklarını kullan.
                3. Doğrudan cevap verme, Sokratik yöntemle öğret.
                """
                
                prompt = [instruction, user_input]
                if uploaded_file:
                    if uploaded_file.type.startswith("image/"):
                        prompt.append(Image.open(uploaded_file))
                    else:
                        prompt.append(f"DOSYA İÇERİĞİ:\n{read_file_content(uploaded_file)}")

                response = model.generate_content(prompt)
                full_text = response.text
                
                st.markdown(full_text)
                st.session_state.messages.append({"role": "assistant", "content": full_text})
                
                # --- ÇIKTI PANELİ ---
                st.divider()
                st.write("### 📥 Akademik Çıktı Merkezi")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.download_button("📄 Word Fasikül", create_word_file(full_text, "Akademik Analiz"), "ErenAI_Analiz.docx")
                with col2:
                    st.download_button("📕 PDF Rapor", create_pdf_file(full_text, "Akademik Analiz"), "ErenAI_Analiz.pdf")
                with col3:
                    st.download_button("📽️ Sunum (PPTX)", create_pptx_file(full_text, "Akademik Sunum"), "ErenAI_Sunum.pptx")
                
                status.update(label="✅ Analiz Tamamlandı", state="complete")
            
            except Exception as e:
                st.error(f"Kritik Hata: {str(e)}")
                status.update(label="❌ Hata Oluştu", state="error")
