import streamlit as st
import google.generativeai as genai
import qrcode
from io import BytesIO
import time
import json
from datetime import datetime

# --- KONFIGURÁCIÓ ÉS ÁLLAPOT KEZELÉS ---
def init_session_state():
    """Munkamenet változóinak inicializálása."""
    defaults = {
        "messages": [],
        "total_tokens": 0,
        "estimated_cost": 0.0,
        "api_key_configured": False,
        "available_models": ["gemini-1.5-flash", "gemini-1.5-pro"]
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

st.set_page_config(
    page_title="UniMate Pro",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Mobilbarát css ---
st.markdown("""
    <style>
        /* itt egy kis mobil optimalizálás */
        @media (max-width: 640px) {
            .main .block-container { padding: 1rem; }
            .stSidebar { width: 250px !important; }
        }
        
        .stChatMessage {
            border-radius: 15px;
            padding: 15px;
            margin-bottom: 10px;
            border: 1px solid #f0f2f6;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        h1 { font-weight: 800 !important; color: #1E3A8A; }
        
        /* Gombok kerekítése jobb kinézethez */
        .stButton>button {
            border-radius: 10px;
            font-weight: 600;
        }
    </style>
""", unsafe_allow_html=True)

# --- AI LOGIKA MODUL ---
class AIManager:
    @staticmethod
    def setup_api(api_key):
        if api_key:
            try:
                genai.configure(api_key=api_key)
                models = genai.list_models()
                st.session_state.available_models = [
                    m.name.replace('models/', '') 
                    for m in models if 'generateContent' in m.supported_generation_methods
                ]
                st.session_state.api_key_configured = True
                return True
            except Exception as e:
                st.sidebar.error(f"API Hiba: {e}")
                return False
        return False

    @staticmethod
    def generate_response(system_prompt, user_prompt, model_name, temp):
        if not st.session_state.api_key_configured:
            st.error("Kérlek, add meg az API kulcsot az oldalsávban!")
            return None
        
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_prompt
            )
            
            with st.spinner("🤖 UniMate gondolkodik..."):
                response = model.generate_content(
                    user_prompt,
                    generation_config=genai.types.GenerationConfig(temperature=temp)
                )
            
            # Token és költség becslés (kb. 4 karakter = 1 token)
            tokens = (len(user_prompt) + len(response.text)) // 4
            st.session_state.total_tokens += tokens
            st.session_state.estimated_cost += (tokens / 1_000_000) * 0.075 # flash árfolyam
            
            return response.text
        except Exception as e:
            st.error(f"⚠️ Hiba történt: {str(e)}")
            return None

# --- SEGÉDFÜGGVÉNYEK ---
def generate_qr_code():
    """QR kódot generál az app eléréséhez."""
    try:
        url = "https://unimatee.streamlit.app" 
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except:
        return None

# --- OLDALSÁV (SIDEBAR) ---
with st.sidebar:
    st.header("🔑 Hozzáférés")
    api_key_input = st.text_input("Google Gemini API Key", type="password")
    if api_key_input:
        AIManager.setup_api(api_key_input)
    
    st.divider()
    
    st.header("⚙️ Beállítások")
    sel_model = st.selectbox("Modell választása", st.session_state.available_models)
    sel_temp = st.slider("Kreativitás", 0.0, 1.0, 0.7)
    
    st.divider()
    
    # Statisztika
    st.subheader("📊 Munkamenet")
    st.caption(f"Tokenek: {st.session_state.total_tokens}")
    st.caption(f"Becsült költség: ${st.session_state.estimated_cost:.5f}")
    
    st.divider()
    
    # Mobil elérés QR
    qr_code = generate_qr_code()
    if qr_code:
        st.image(qr_code, caption="Megnyitás telefonon", width=150)
    
    if st.button("🗑️ Chat törlése"):
        st.session_state.messages = []
        st.rerun()

# --- UI MODULOK (FUNKCIÓK) ---
def render_regulations():
    st.subheader("📄 Szabályzat Elemző")
    st.info("Másold be az egyetemi szabályzat részletét az egyszerűsített elemzéshez.")
    text = st.text_area("Szöveg helye:", height=200, placeholder="Ide jöhet a szabályzat...")
    
    if st.button("🔍 Elemzés futtatása"):
        if text:
            res = AIManager.generate_response("Te egy egyetemi jogi szakértő vagy. Magyarázd el a szabályzatot közérthetően, pontokba szedve.", text, sel_model, sel_temp)
            if res:
                st.markdown("### 📋 Elemzés eredménye")
                st.markdown(res)

def render_thesis():
    st.subheader("💡 Szakdolgozat Mentor")
    topic = st.text_input("Téma megnevezése:", placeholder="pl. Mesterséges intelligencia az oktatásban")
    
    if st.button("🚀 Terv generálása"):
        if topic:
            res = AIManager.generate_response("Te egy tudományos mentor vagy. Készíts részletes kutatási tervet, vázlatot és javasolt módszertant.", topic, sel_model, sel_temp)
            if res:
                st.success("A vázlat elkészült!")
                st.markdown(res)

def render_email():
    st.subheader("📧 Email Generátor")
    raw_info = st.text_area("Miről szóljon az email?", placeholder="pl. Kérem a Tanár urat, hogy fogadja el a késői leadást...")
    
    if st.button("✍️ Email megírása"):
        if raw_info:
            res = AIManager.generate_response("Profi egyetemi titkár vagy. Írj egy formális, udvarias emailt az alábbi infók alapján.", raw_info, sel_model, sel_temp)
            if res:
                st.code(res, language="markdown")
                st.info("A fenti kódot kimásolhatod a jobb felső sarokban lévő gombbal.")

def render_chatbot():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Kérdezz bármit az UniMate-től..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        res = AIManager.generate_response("Te UniMate vagy, egy barátságos és okos egyetemi asszisztens. Használj formázást, listákat és emojikat.", prompt, sel_model, sel_temp)
        
        if res:
            st.session_state.messages.append({"role": "assistant", "content": res})
            with st.chat_message("assistant"):
                st.markdown(res)
            
            # Export lehetőség
           # chat_data = json.dumps(st.session_state.messages, indent=4, ensure_ascii=False)
           # st.download_button("📥 Chat mentése", chat_data, file_name="unimate_chat.json")
            chat_text = f"UniMate Chat Napló - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            chat_text += "="*30 + "\n\n"

            for msg in st.session_state.messages:
                sender = "HALLGATÓ" if msg["role"] == "user" else "UNIMATE"
                chat_text += f"[{sender}]:\n{msg['content']}\n"
                chat_text += "-"*20 + "\n"

# Letöltő gomb TXT-ben
            st.download_button(
                label="📥 Chat mentése (.txt)",
                data=chat_text,
                file_name=f"unimate_chat_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain"
)

# --- Home Page ---
def main():
    st.title("🎓 UniMate – Intelligens Asszisztens")
    st.markdown("##### Minden, amire egy egyetemi hallgatónak szüksége lehet.")

    tabs = st.tabs(["💬 Chatbot", "📄 Szabályzat", "💡 Szakdolgozat", "📧 Email"])
    
    with tabs[0]: render_chatbot()
    with tabs[1]: render_regulations()
    with tabs[2]: render_thesis()
    with tabs[3]: render_email()

if __name__ == "__main__":
    main()
