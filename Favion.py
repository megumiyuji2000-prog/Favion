import streamlit as st
import google.generativeai as genai
from PIL import Image
from datetime import datetime, timedelta
import pytz
from duckduckgo_search import DDGS
import pandas as pd
import re

st.set_page_config(page_title="Favion AI", page_icon="🎯", layout="centered", initial_sidebar_state="collapsed")

# ==================== CSS FAVION - HIJAU TOSKA MANAGER ====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
    #MainMenu, footer, header {visibility: hidden;}

    /* Favion Theme: Teal/Green = Growth, Money, Action */
 .stApp,.main { background-color: #0A0F0D; }
 .block-container {
        padding-top: 2rem!important;
        padding-bottom: 8rem!important;
        max-width: 48rem!important;
    }
 .favion-title {
        text-align: center;
        font-size: 2.25rem;
        font-weight: 700;
        background: linear-gradient(90deg, #10B981 0%, #34D399 50%, #6EE7B7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem;
        letter-spacing: -0.02em;
    }
 .favion-subtitle {
        text-align: center;
        color: #6B7280;
        font-size: 0.95rem;
        margin-bottom: 3rem;
    }
 .stChatMessage {
        background-color: transparent!important;
        padding: 0.75rem 0!important;
        margin: 0!important;
    }
    [data-testid="stChatMessageContent"] {
        background-color: #111827!important;
        border-radius: 18px!important;
        padding: 12px 16px!important;
        color: #E5E7EB!important;
        line-height: 1.65;
        border: 1px solid #1F2937;
        font-size: 0.95rem;
    }
 .stChatMessage[data-testid*="user"] [data-testid="stChatMessageContent"] {
        background-color: #1F2937!important;
        border: 1px solid #374151;
    }
 .stChatInput {
        position: fixed!important;
        bottom: 0!important;
        left: 0!important;
        right: 0!important;
        background: linear-gradient(180deg, rgba(10,15,13,0) 0%, #0A0F0D 30%)!important;
        padding: 1rem 1rem 1.5rem 1rem!important;
        max-width: 48rem!important;
        margin: 0 auto!important;
        backdrop-filter: blur(8px);
    }
 .stChatInput > div {
        background-color: #111827!important;
        border: 1px solid #10B981!important;
        border-radius: 26px!important;
        box-shadow: 0 4px 12px rgba(16,185,129,0.2);
    }
 .stChatInput input { color: #E5E7EB!important; font-size: 0.95rem!important; padding: 14px 18px!important; }
 .stChatInput input::placeholder { color: #6B7280!important; }
 .stImage img { border-radius: 14px!important; border: 1px solid #1F2937; margin: 8px 0; }
 .stToast { background-color: #111827!important; border: 1px solid #10B981!important; border-radius: 12px!important; }

    /* Tabel Favion */
 .stDataFrame { border: 1px solid #1F2937!important; border-radius: 12px!important; }
 .stDataFrame thead tr th { background-color: #10B981!important; color: #0A0F0D!important; font-weight: 600!important; }
 .stDataFrame tbody tr td { background-color: #111827!important; color: #E5E7EB!important; }

 .favion-badge {
        display: inline-block;
        font-size: 0.75rem;
        padding: 4px 10px;
        border-radius: 12px;
        margin-bottom: 8px;
        font-weight: 600;
        background-color: #065F46;
        color: #A7F3D0;
    }
</style>
""", unsafe_allow_html=True)

# ==================== INIT ====================
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash')
except:
    st.error("API Key belum diset bro.")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])

# ==================== FAVION BRAIN ====================
def search_web(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(f"{query} strategi tips", max_results=3))
            if results:
                return "\n".join([f"- {r['body'][:200]}" for r in results])
    except:
        return ""
    return ""

def deteksi_intent(text):
    """Deteksi Favion harus ngapain: bisnis, kanal, belajar, uang, waktu"""
    t = text.lower()

    if any(k in t for k in ["bisnis", "jualan", "omzet", "usaha", "umkm", "profit", "marketing"]):
        return "bisnis"
    if any(k in t for k in ["konten", "instagram", "tiktok", "youtube", "channel", "posting", "fyp"]):
        return "kanal"
    if any(k in t for k in ["belajar", "utbk", "ujian", "skripsi", "jadwal belajar", "fokus"]):
        return "belajar"
    if any(k in t for k in ["uang", "gaji", "budget", "nabung", "investasi", "keuangan", "utang"]):
        return "uang"
    if any(k in t for k in ["waktu", "sibuk", "produktif", "jadwal", "todo", "deadline", "prioritas"]):
        return "waktu"
    if any(k in t for k in ["soal", "hitung", "rumus", "integral", "matematika", "fisika"]):
        return "lempar_fanilla"
    return "ngobrol"

def jawab_favion(text, image=None):
    """Favion = Manager segala hal. Bukan dosen."""
    intent = deteksi_intent(text)

    # Kalau nanya soal, lempar ke Fanilla
    if intent == "lempar_fanilla":
        yield "Waduh bro kalo soal sekolah/PR tanya Fanilla aja wkwk. Gw jagonya ngatur strategi & duit 💚\n\nCoba lu tanya gw: 'Favion, gimana cara atur waktu belajar' nah itu baru bidang gw.", "teman"
        return

    # Search strategi terbaru
    if intent!= "ngobrol":
        with st.spinner("Favion lagi riset strategi..."):
            ref = search_web(f"{intent} {text}")
            if ref:
                text += f"\n\n[Data Pasar]:\n{ref}"

    tz = pytz.timezone('Asia/Jakarta')
    tgl = datetime.now(tz).strftime("%d %B %Y")

    prompt_map = {
        "bisnis": f"""Kamu Favion, FAntastic inoVIsiON. Manager bisnis temen lu. Tanggal {tgl}.
ATURAN:
1. Bahasa: Gaul tapi solutif. "Oke bro, buat naikin omzet lu gini..."
2. OUTPUT: Wajib pake TABEL markdown. Kolom: Strategi | Aksi | Deadline | Metrik
3. Kasih 3-5 langkah konkret. Jangan teori doang.
4. Panjang: 2-4 paragraf + 1 tabel. Total 15-30 baris.
5. Tutup: "Gas eksekusi bro!" atau "Konsisten kuncinya!"

Misi user: {text}""",

        "kanal": f"""Kamu Favion, FAntastic inoVIsiON. Content strategist temen lu. Tanggal {tgl}.
ATURAN:
1. Bahasa: Gaul, paham algoritma. "Bro biar FYP gini..."
2. OUTPUT: Wajib TABEL. Kolom: Hari | Ide Konten | Hook | CTA | Jam Post
3. Kasih 7 hari content calendar.
4. Panjang: 2-3 paragraf + 1 tabel. Total 15-25 baris.
5. Tutup: "Konsisten upload ya!"

Misi user: {text}""",

        "belajar": f"""Kamu Favion, FAntastic inoVIsiON. Coach belajar temen lu. Tanggal {tgl}.
ATURAN:
1. Bahasa: Gaul tapi disiplin. "Bro kalo mau lolos UTBK gini..."
2. OUTPUT: TABEL. Kolom: Waktu | Kegiatan | Teknik | Target
3. Pake metode: Pomodoro, Feynman, Active Recall.
4. Panjang: 2-3 paragraf + 1 tabel. Total 15-25 baris.
5. Tutup: "Disiplin ya bro!"

Misi user: {text}""",

        "uang": f"""Kamu Favion, FAntastic inoVIsiON. Financial advisor temen lu. Tanggal {tgl}.
ATURAN:
1. Bahasa: Gaul tapi bijak. "Bro duit lu gini nih..."
2. OUTPUT: TABEL budget. Kolom: Pos | Alokasi % | Nominal | Catatan
3. Pake aturan 50/30/20 atau 40/30/20/10.
4. Panjang: 2-3 paragraf + 1 tabel. Total 15-25 baris.
5. Tutup: "Jangan jajan boba mulu bro!"

Misi user: {text}""",

        "waktu": f"""Kamu Favion, FAntastic inoVIsiON. Time management coach temen lu. Tanggal {tgl}.
ATURAN:
1. Bahasa: Gaul tapi tegas. "Bro waktu lu bocor di sini..."
2. OUTPUT: TABEL Eisenhower. Kolom: Tugas | Urgent | Penting | Aksi | Deadline
3. Prioritas: Do, Schedule, Delegate, Delete.
4. Panjang: 2-3 paragraf + 1 tabel. Total 15-25 baris.
5. Tutup: "Fokus yg penting bro!"

Misi user: {text}""",

        "ngobrol": f"""Kamu Favion, FAntastic inoVIsiON. Temen nongkrong yg pinter ngatur hidup.
ATURAN:
1. Bahasa: Gaul abis, empati, informatif. "Anjir sama bro" "Wkwk gila lu"
2. PANJANG: 1-2 paragraf MAX. Jangan panjang.
3. Topik: Bebas. Curhat, becanda, motivasi.
4. Kalo bisa, selipin 1 tips manajemen hidup kecil.
5. Jangan sebut "AI/model".

Chat: {text}"""
    }

    prompt = prompt_map[intent]

    if image:
        prompt += "\n\nUser upload gambar. Scan gambar itu. Kalo isinya jadwal/catatan/todo, ubah jadi tabel rapi + kasih saran optimasi. Kalo foto random, komen kayak temen."
        st.toast("Favion lagi scan gambar...", icon="🔍")
    else:
        st.toast("Favion nyusun strategi...", icon="🎯")

    try:
        if image:
            res = st.session_state.chat.send_message([prompt, image], stream=True)
        else:
            res = st.session_state.chat.send_message(prompt, stream=True)

        for chunk in res:
            if chunk.text:
                yield chunk.text, intent
    except Exception as e:
        if "429" in str(e):
            yield "Limit harian abis bro. Besok jam 7 pagi reset. Istirahat dulu kita 😴", "ngobrol"
        else:
            yield "Error bro, coba lagi ya.", "ngobrol"

# ==================== UI ====================
if len(st.session_state.messages) == 0:
    st.markdown('<div class="favion-title">Favion AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="favion-subtitle">FAntastic inoVIsiON<br>Manager Bisnis, Kanal, Belajar, Uang, Waktu. Upload foto jadwal lu 📸</div>', unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("intent") and msg["role"] == "assistant":
            badge_map = {
                "bisnis": "💼 Bisnis", "kanal": "📱 Kanal", "belajar": "📚 Belajar",
                "uang": "💰 Uang", "waktu": "⏰ Waktu", "ngobrol": "💬 Ngobrol",
                "lempar_fanilla": "🎓 Lempar Fanilla"
            }
            label = badge_map.get(msg["intent"], "🎯 Favion")
            st.markdown(f'<div class="favion-badge">{label}</div>', unsafe_allow_html=True)

        if msg["type"] == "image":
            st.image(msg["content"], caption=msg.get("caption"))
        else:
            st.markdown(msg["content"])

prompt = st.chat_input("Tanya Favion soal bisnis, kanal, belajar...", accept_file=True, file_type=["jpg", "jpeg", "png"])

if prompt:
    intent_aktif = "ngobrol"
    if prompt.get("files"):
        img = Image.open(prompt["files"][0])
        txt = prompt.get("text", "Favion, tolong rapihin jadwal di foto ini jadi tabel.")
        st.session_state.messages.append({"role": "user", "content": img, "type": "image", "caption": txt})
        with st.chat_message("user"):
            st.image(img, caption=txt)
        with st.chat_message("assistant"):
            ph = st.empty()
            out = ""
            for c, m in jawab_favion(txt, image=img):
                out += c
                intent_aktif = m
                ph.markdown(out + "▌")
            ph.markdown(out)
            st.session_state.messages.append({"role": "assistant", "content": out, "type": "text", "intent": intent_aktif})
    elif prompt.get("text"):
        txt = prompt["text"]
        st.session_state.messages.append({"role": "user", "content": txt, "type": "text"})
        with st.chat_message("user"):
            st.markdown(txt)
        with st.chat_message("assistant"):
            ph = st.empty()
            out = ""
            for c, m in jawab_favion(txt):
                out += c
                intent_aktif = m
                ph.markdown(out + "▌")
            ph.markdown(out)
            st.session_state.messages.append({"role": "assistant", "content": out, "type": "text", "intent": intent_aktif})
    st.rerun()
