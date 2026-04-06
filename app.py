import streamlit as st
import google.generativeai as genai
import PIL.Image
import os

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

# --- 2. API ANAHTARI VE GÜVENLİK ---
# Önemli: Secrets kısmında GOOGLE_API_KEY tanımlı olmalıdır
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Hata: Streamlit Secrets kısmına GOOGLE_API_KEY ekleyin!")
    st.stop()

# --- 3. YAN MENÜ VE SEÇİM ALANLARI ---
with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=150)
    
    # İstediğin seçim alanı
    st.subheader("Modül Seçin:")
    modul = st.selectbox(
        "Asistan Modu",
        ["Eren AI Asistanı", "Akademik Destek", "Veli Bilgilendirme"],
        label_visibility="collapsed"
    )
    
    st.info(f"Aktif Mod: {modul}")
    st.divider()
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

# --- 4. MESAJ GEÇMİŞİ ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. ANA EKRAN VE DOSYA YÜKLEME ALANI ---
st.title("🛡️ Eren AI Portalı")

# Dosya yükleme kutusunu tekrar ekliyoruz
with st.container(border=True):
    col1, col2 = st.columns([1, 4]) 
    with col1:
        yuklenen_dosya = st.file_uploader("Dosya", type=['png', 'jpg', 'jpeg', 'pdf'], label_visibility="collapsed")
    with col2:
        prompt = st.chat_input("Mesajınızı yazın veya dosya ekleyin...")

# --- 6. CEVAP ÜRETME (HATASIZ YAPI) ---
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("Eren AI analiz ediyor... 🛡️")
        
        try:
            # Model ismini API versiyonuna uygun şekilde seçiyoruz
            model = genai.GenerativeModel(
                model_name='gemini-1.5-flash',
                system_instruction=f"""
                Sen Özel Eren Fen ve Teknoloji Lisesi'nin resmi asistanısın. 
                Şu an '{modul}' modunda hizmet veriyorsun. 
                Okul müdürü: Mert Kadıoğlu. 
                Resmi web sitesi: www.eren.k12.tr.
                Cevaplarını okulun vizyonuna uygun, bilimsel ve nazik bir dille ver.
                """
            )

            # İçerik hazırlama (Metin + Dosya)
            icerik = [prompt]
            if yuklenen_dosya:
                if yuklenen_dosya.type.startswith("image/"):
                    icerik.append(PIL.Image.open(yuklenen_dosya))
                elif yuklenen_dosya.type == "application/pdf":
                    icerik.append({"mime_type": "application/pdf", "data": yuklenen_dosya.read()})

            response = model.generate_content(icerik)
            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            # Hataları gizlemeden ama kullanıcıyı yormadan göster
            st.error(f"Sistemde bir güncelleme yapılıyor, lütfen tekrar deneyin. (Detay: {str(e)})")
