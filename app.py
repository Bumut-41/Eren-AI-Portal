import streamlit as st
import google.generativeai as genai
import os

st.title("🛡️ Eren AI Sistem Denetimi")

# API Anahtarını al
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    st.write("### 🔍 Sistem Analiz Ediliyor...")
    
    # 1. Mevcut Kütüphane Versiyonu
    st.info(f"SDK Versiyonu: {genai.__version__}")
    
    # 2. Erişilebilir Modelleri Listele
    try:
        models = [m.name for m in genai.list_models()]
        st.success("✅ Modellere erişim sağlandı!")
        st.write("**Erişilebilir Modeller:**", models)
        
        if "models/gemini-1.5-flash" in models:
            st.balloons()
            st.write("🚀 **Müjde:** Gemini 1.5 Flash sisteminizde tanımlı.")
    except Exception as e:
        st.error(f"❌ Model Listeleme Hatası: {e}")
        st.warning("Bu hata, API anahtarının yetkisiz olduğunu veya versiyon uyuşmazlığını gösterir.")

else:
    st.error("API Anahtarı bulunamadı! Lütfen Secrets kısmını kontrol edin.")
