import streamlit as st
import google.generativeai as genai
import PIL.Image
import os

# --- 1. SAYFA VE LOGO ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="centered")

# API Anahtarı (Yayınlarken st.secrets kullanmanı öneririm)
genai.configure(api_key="AIzaSyA46ihIhUys-3GFyfe_GS-M50snUZ1sx5I")

# --- 2. YAN MENÜ ---
with st.sidebar:
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=200)
    st.title("Eren AI Menü")
    secenek = st.selectbox("Modül Seçin:", ("Eren AI Asistanı", "Bilimsel Araştırma", "Kod Yardımı"))
    st.divider()
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

# --- 3. ANA EKRAN VE MESAJ GEÇMİŞİ ---
st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. BİRLEŞİK GİRİŞ ALANI (GÖRSEL OLARAK TEK ALAN) ---
# Bu kısım dosya yükleyici ve yazı alanını bir kutu içine alır
with st.container(border=True):
    col1, col2 = st.columns([1, 4]) # Dosya simgesi/yükleyici ve metin alanı oranı
    
    with col1:
        # Küçük bir dosya yükleme butonu (Sadece simge gibi durur)
        yuklenen_dosya = st.file_uploader("Dosya", type=['png', 'jpg', 'jpeg', 'pdf', 'txt'], label_visibility="collapsed")
    
    with col2:
        # Metin giriş alanı
        prompt = st.chat_input("Mesajınızı yazın veya dosya ekleyin...")

# --- 5. ANALİZ MANTIĞI ---
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("Eren AI analiz ediyor...")
        
        try:
            # Otomatik model seçimi (404 hatasını önlemek için)
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            target_model = next((m for m in available_models if "gemini-1.5-flash" in m), available_models[0])
            model = genai.GenerativeModel(model_name=target_model)
            import streamlit as st
import google.generativeai as genai
import PIL.Image
import os

# --- 1. SAYFA VE LOGO ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="centered")

# API Anahtarı (Yayınlarken st.secrets kullanmanı öneririm)
genai.configure(api_key="AIzaSyA46ihIhUys-3GFyfe_GS-M50snUZ1sx5I")

# --- 2. YAN MENÜ ---
with st.sidebar:
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=200)
    st.title("Eren AI Menü")
    secenek = st.selectbox("Modül Seçin:", ("Eren AI Asistanı", "Bilimsel Araştırma", "Kod Yardımı"))
    st.divider()
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

# --- 3. ANA EKRAN VE MESAJ GEÇMİŞİ ---
st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. BİRLEŞİK GİRİŞ ALANI (GÖRSEL OLARAK TEK ALAN) ---
# Bu kısım dosya yükleyici ve yazı alanını bir kutu içine alır
with st.container(border=True):
    col1, col2 = st.columns([1, 4]) # Dosya simgesi/yükleyici ve metin alanı oranı
    
    with col1:
        # Küçük bir dosya yükleme butonu (Sadece simge gibi durur)
        yuklenen_dosya = st.file_uploader("Dosya", type=['png', 'jpg', 'jpeg', 'pdf', 'txt'], label_visibility="collapsed")
    
    with col2:
        # Metin giriş alanı
        prompt = st.chat_input("Mesajınızı yazın veya dosya ekleyin...")

# --- 5. ANALİZ MANTIĞI ---
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("Eren AI analiz ediyor...")
        
        try:
            # Otomatik model seçimi (404 hatasını önlemek için)
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            target_model = next((m for m in available_models if "gemini-1.5-flash" in m), available_models[0])
            model = genai.GenerativeModel(model_name=target_model)
            import streamlit as st
import google.generativeai as genai
import PIL.Image
import os

# --- 1. SAYFA VE LOGO ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="centered")

# API Anahtarı (Yayınlarken st.secrets kullanmanı öneririm)
genai.configure(api_key="AIzaSyA46ihIhUys-3GFyfe_GS-M50snUZ1sx5I")

# --- 2. YAN MENÜ ---
with st.sidebar:
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=200)
    st.title("Eren AI Menü")
    secenek = st.selectbox("Modül Seçin:", ("Eren AI Asistanı", "Bilimsel Araştırma", "Kod Yardımı"))
    st.divider()
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

# --- 3. ANA EKRAN VE MESAJ GEÇMİŞİ ---
st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. BİRLEŞİK GİRİŞ ALANI (GÖRSEL OLARAK TEK ALAN) ---
# Bu kısım dosya yükleyici ve yazı alanını bir kutu içine alır
with st.container(border=True):
    col1, col2 = st.columns([1, 4]) # Dosya simgesi/yükleyici ve metin alanı oranı
    
    with col1:
        # Küçük bir dosya yükleme butonu (Sadece simge gibi durur)
        yuklenen_dosya = st.file_uploader("Dosya", type=['png', 'jpg', 'jpeg', 'pdf', 'txt'], label_visibility="collapsed")
    
    with col2:
        # Metin giriş alanı
        prompt = st.chat_input("Mesajınızı yazın veya dosya ekleyin...")

# --- 5. ANALİZ MANTIĞI ---
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("Eren AI analiz ediyor...")
        try:
            # Otomatik model seçimi (404 hatasını önlemek için mevcut kodun kalıyor)
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            target_model = next((m for m in available_models if "gemini-1.5-flash" in m), available_models[0])
            
            # ESKİ SATIRI SİLİP YERİNE BUNU YAPIŞTIR:
            model = genai.GenerativeModel(
                model_name=target_model,
                system_instruction="""
                Sen Özel Eren Fen ve Teknoloji Lisesi'nin resmi yapay zeka asistanısın. 
                Adın 'Eren AI'. Görevin öğrencilerimize ve öğretmenlerimize bilimsel, 
                edebe uygun ve akademik destek vermektir. 
                Cevaplarında nazik olmalı ve okulumuzun bilim ve teknoloji odaklı vizyonunu yansıtmalısın. 
                Sana 'kimsin' denildiğinde Özel Eren Fen ve Teknoloji Lisesi asistanı olduğunu söylemelisin.
                """
            )





            
            icerik = [prompt]
            if yuklenen_dosya:
                # PDF/Görsel İşleme
                if yuklenen_dosya.type == "application/pdf":
                    icerik.append({"mime_type": "application/pdf", "data": yuklenen_dosya.read()})
                elif yuklenen_dosya.type.startswith("image/"):
                    icerik.append(PIL.Image.open(yuklenen_dosya))
                else:
                    icerik.append(yuklenen_dosya.getvalue().decode("utf-8"))

            response = model.generate_content(icerik)
            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            st.error(f"Hata: {str(e)}")
            icerik = [prompt]
            if yuklenen_dosya:
                # PDF/Görsel İşleme
                if yuklenen_dosya.type == "application/pdf":
                    icerik.append({"mime_type": "application/pdf", "data": yuklenen_dosya.read()})
                elif yuklenen_dosya.type.startswith("image/"):
                    icerik.append(PIL.Image.open(yuklenen_dosya))
                else:
                    icerik.append(yuklenen_dosya.getvalue().decode("utf-8"))

            response = model.generate_content(icerik)
            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            st.error(f"Hata: {str(e)}")
            icerik = [prompt]
            if yuklenen_dosya:
                # PDF/Görsel İşleme
                if yuklenen_dosya.type == "application/pdf":
                    icerik.append({"mime_type": "application/pdf", "data": yuklenen_dosya.read()})
                elif yuklenen_dosya.type.startswith("image/"):
                    icerik.append(PIL.Image.open(yuklenen_dosya))
                else:
                    icerik.append(yuklenen_dosya.getvalue().decode("utf-8"))

            response = model.generate_content(icerik)
            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            st.error(f"Hata: {str(e)}")
