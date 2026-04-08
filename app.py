import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from PIL import Image
import io

# --- SİSTEM AYARLARI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Anahtarı bulunamadı!")
    st.stop()

# --- MODEL TANIMLAMA ---
# Görsel ve Metin kapasitesi en yüksek model
model = genai.GenerativeModel('gemini-3-flash-preview')

# --- GELİŞMİŞ DOSYA İŞLEME ---
def dosyayi_hazirla(yuklenen_dosya):
    try:
        if yuklenen_dosya.type == "application/pdf":
            reader = PdfReader(yuklenen_dosya)
            metin = "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
            
            # Eğer metin boşsa (dosya taranmış bir dökümansa), PDF'i modele görsel olarak sunamayız.
            # Bu durumda kullanıcıya uyarı verip metin girişi isteyeceğiz.
            return metin, "pdf"
        
        elif yuklenen_dosya.type.startswith("image/"):
            return Image.open(yuklenen_dosya), "image"
            
        return None, None
    except Exception as e:
        return f"Hata: {e}", "error"

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

# Giriş Bölümü
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        dosya = st.file_uploader("Dosya", type=['pdf','png','jpg','jpeg'], key="eren_file", label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya sorunuzu iletin...")

# --- İŞLEME ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        durum = st.status("🛡️ Eren AI dökümanı derinlemesine inceliyor...")
        
        try:
            prompt_list = [f"Sen Eren AI'sın. Mod: {mod}. Profesyonel bir okul asistanısın."]
            
            if dosya:
                veri, tip = dosyayi_hazirla(dosya)
                
                if tip == "image":
                    prompt_list.append(veri) # Görseli listeye ekle
                    prompt_list.append(f"Yukarıdaki görseli analiz et ve şu soruyu yanıtla: {soru}")
                    durum.write("🖼️ Görsel analiz ediliyor...")
                elif tip == "pdf":
                    if veri and len(veri.strip()) > 10:
                        # Metin bulunduysa metin üzerinden ilerle
                        prompt_list.append(f"Aşağıdaki döküman metnine göre soruyu yanıtla:\n\n{veri}\n\nSORU: {soru}")
                        durum.write(f"📝 {len(veri)} karakter metin başarıyla okundu.")
                    else:
                        # Metin bulunamadıysa uyarı ver
                        st.warning("⚠️ Bu PDF'den metin okunamadı (PDF taranmış bir resim olabilir mi?). Lütfen metni kopyalayıp yapıştırın veya dökümanın fotoğrafını yükleyin.")
                        prompt_list.append(soru)
            else:
                prompt_list.append(soru)

            # YANIT ÜRETİMİ
            response = model.generate_content(prompt_list)
            
            if response.text:
                durum.update(label="✅ Analiz Tamamlandı", state="complete")
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
        except Exception as e:
            durum.update(label="❌ Hata", state="error")
            st.error(f"Bir sorun oluştu: {str(e)}")
