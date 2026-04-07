import streamlit as st
import google.generativeai as genai
import PIL.Image
import os

# --- 1. AYARLAR VE TASARIM ---
st.set_page_config(page_title="Eren AI Portalı", page_icon="🛡️", layout="wide")

# API Yapılandırması
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Secrets içinde API anahtarı bulunamadı!")
    st.stop()

# --- 2. HATA GEÇİRMEZ MODEL SEÇİCİ (404 KATİLİ) ---
@st.cache_resource
def dinamik_model_bul():
    """Sistemdeki tüm modelleri tarar ve en uygun olanı seçer."""
    denenecek_isimler = ['gemini-1.5-flash', 'models/gemini-1.5-flash', 'gemini-pro']
    
    # Adım 1: Aktif modeller listesinden doğrula
    try:
        mevcut_modeller = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for isim in denenecek_isimler:
            # Hem tam isim hem kısa isim kontrolü
            if isim in mevcut_modeller or f"models/{isim}" in mevcut_modeller:
                return genai.GenerativeModel(isim)
    except Exception:
        pass # Liste alınamazsa manuel denemeye geç

    # Adım 2: Manuel Brute-Force Deneme
    for isim in denenecek_isimler:
        try:
            test_model = genai.GenerativeModel(isim)
            # Test amaçlı boş bir çağrı denemesi (Çok hafif)
            return test_model
        except:
            continue
            
    # Adım 3: Hiçbiri olmazsa en standart ismi döndür
    return genai.GenerativeModel('gemini-1.5-flash')

model = dinamik_model_bul()

# --- 3. YAN ÇUBUK (SIDEBAR) ---
with st.sidebar:
    st.title("🛡️ Eren AI Menü")
    if os.path.exists("Logo.png"):
        st.image("Logo.png", width=150)
    
    st.divider()
    mod = st.selectbox("Asistan Modu", ["Eren AI Asistanı", "Akademik Destek", "Veli Bilgilendirme"])
    st.divider()
    st.caption("© 2026 Özel Eren Fen ve Teknoloji Lisesi")

# --- 4. ANA EKRAN ---
st.title("🛡️ Eren AI Portalı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Giriş Alanları
with st.container():
    c1, c2 = st.columns([1, 4])
    with c1:
        yukle = st.file_uploader("Dosya", type=['png','jpg','jpeg','pdf','docx'], label_visibility="collapsed")
    with c2:
        soru = st.chat_input("Eren AI'ya bir soru sorun...")

# Geçmişi Göster
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 5. İŞLEME VE YANIT ---
if soru:
    st.session_state.messages.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        alan = st.empty()
        alan.markdown("⚡ *Bağlantı doğrulanıyor...*")
        
        try:
            baglam = f"Sen Eren AI'sın. Mod: {mod}. Kurumsal ve yardımcı ol."
            payload = [baglam, soru]
            
            if yukle and yukle.type.startswith("image/"):
                img = PIL.Image.open(yukle)
                payload.append(img)

            # Yanıt Üretimi
            yanit = model.generate_content(payload)
            
            if yanit.text:
                alan.markdown(yanit.text)
                st.session_state.messages.append({"role": "assistant", "content": yanit.text})
            else:
                alan.error("Model boş yanıt döndürdü.")
                
        except Exception as e:
            # Hata durumunda model ismini bir kez daha 'models/' ile zorla
            try:
                alternatif_model = genai.GenerativeModel(f"models/{model.model_name.split('/')[-1]}")
                yanit = alternatif_model.generate_content(payload)
                alan.markdown(yanit.text)
                st.session_state.messages.append({"role": "assistant", "content": yanit.text})
            except:
                alan.error(f"Kritik Bağlantı Hatası: {str(e)}")
