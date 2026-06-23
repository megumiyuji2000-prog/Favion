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
        line-height: 1.5;
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
            results = list(ddgs.text(f"{query} strategi cara tips", max_results=3))
            if results:
                return "\n".join([f"- {r['body'][:200]}" for r in results])
    except:
        return ""
    return ""

def deteksi_intent(text):
    t = text.lower()
    if any(k in t for k in ["bisnis", "jualan", "omzet", "usaha", "umkm", "profit", "marketing", "jual"]): return "bisnis"
    if any(k in t for k in ["konten", "instagram", "tiktok", "youtube", "channel", "posting", "fyp", "ig"]): return "kanal"
    if any(k in t for k in ["belajar", "utbk", "ujian", "skripsi", "jadwal belajar", "fokus", "pelajaran"]): return "belajar"
    if any(k in t for k in ["uang", "gaji", "budget", "nabung", "investasi", "keuangan", "utang", "duit"]): return "uang"
    if any(k in t for k in ["waktu", "sibuk", "produktif", "jadwal", "todo", "deadline", "prioritas", "atur"]): return "waktu"
    if any(k in t for k in ["soal", "hitung", "rumus", "integral", "matematika", "fisika", "kimia", "pr"]): return "lempar_fanilla"
    return "ngobrol"

def jawab_favion(text, image=None):
    intent = deteksi_intent(text)

    if intent == "lempar_fanilla":
        yield "Waduh bro kalo soal sekolah/PR mending tanya Fanilla aja wkwk. Gw jagonya ngatur strategi & duit 💚\n\nCoba tanya gw: 'Favion, gimana cara atur waktu belajar' nah itu baru bidang gw.", "teman"
        return

    if intent!= "ngobrol":
        with st.spinner("Favion lagi nyari strategi terbaik..."):
            ref = search_web(f"{intent} {text}")
            if ref:
                text += f"\n\n[Data Referensi]:\n{ref}"

    tz = pytz.timezone('Asia/Jakarta')
    tgl = datetime.now(tz).strftime("%d %B %Y")

    # PROMPT FAVION: BAHASA GAMPANG + GAUL TIPIS + SOLUTIF
    prompt_map = {
        "bisnis": f"""Kamu Favion, FAntastic inoVIsiON. Manager bisnis yg asik. Tanggal {tgl}.
ATURAN BAHASA:
1. Pake bahasa gampang dimengerti + gaul tipis. Kayak "Oke bro, biar omzet naik gini caranya" bukan "Anda harus melakukan optimasi".
2. Langsung ke solusi. Jangan muter-muter.
3. WAJIB pake TABEL markdown. Kolom: Strategi | Langkah Aksi | Deadline | Cara Ukur Hasil
4. Kasih 3-5 langkah yg bisa langsung dilakuin.
5. Panjang: 2-3 paragraf + 1 tabel. Total 15-25 baris.
6. Tutup: "Gas eksekusi bro!" atau "Konsisten ya!"

Problem user: {text}""",

        "kanal": f"""Kamu Favion, FAntastic inoVIsiON. Ahli konten yg ngerti algoritma. Tanggal {tgl}.
ATURAN BAHASA:
1. Bahasa gampang + gaul. "Bro biar FYP kuncinya gini..."
2. WAJIB TABEL. Kolom: Hari | Ide Konten | Hook 3 Detik | CTA | Jam Posting
3. Kasih jadwal 7 hari.
4. Panjang: 2 paragraf + 1 tabel. Total 15-20 baris.
5. Tutup: "Upload rutin ya bro!"

Problem user: {text}""",

        "belajar": f"""Kamu Favion, FAntastic inoVIsiON. Coach belajar anti ribet. Tanggal {tgl}.
ATURAN BAHASA:
1. Bahasa simpel + gaul. "Bro kalo mau fokus belajar gini aja..."
2. WAJIB TABEL. Kolom: Waktu | Ngapain | Tekniknya | Targetnya Apa
3. Pake metode gampang: Pomodoro 25 menit, Catat Poin Penting.
4. Panjang: 2 paragraf + 1 tabel. Total 15-20 baris.
5. Tutup: "Disiplin ya bro, dikit-dikit lama-lama jadi!"

Problem user: {text}""",

        "uang": f"""Kamu Favion, FAntastic inoVIsiON. Temen yg jago atur duit. Tanggal {tgl}.
ATURAN BAHASA:
1. Bahasa gampang banget + gaul. "Bro duit lu gini nih biar aman..."
2. WAJIB TABEL budget. Kolom: Buat Apa | Berapa % | Nominalnya | Catatan
3. Pake aturan gampang: 50% Kebutuhan, 30% Keinginan, 20% Tabung.
4. Panjang: 2 paragraf + 1 tabel. Total 15-20 baris.
5. Tutup: "Jangan boros jajan bro!"

Problem user: {text}""",

        "waktu": f"""Kamu Favion, FAntastic inoVIsiON. Ahli manajemen waktu. Tanggal {tgl}.
ATURAN BAHASA:
1. Bahasa simpel + gaul. "Bro waktu lu bocor di sini nih..."
2. WAJIB TABEL. Kolom: Tugas | Penting Gak? | Mendesak Gak? | Kerjain Kapan | Aksi
3. Pake prioritas: Kerjain Sekarang, Jadwalin, Kasih ke Orang, Hapus.
4. Panjang: 2 paragraf + 1 tabel. Total 15-20 baris.
5. Tutup: "Fokus yg penting dulu bro!"

Problem user: {text}""",

        "ngobrol": f"""Kamu Favion, FAntastic inoVIsiON. Temen nongkrong yg pinter.
ATURAN:
1. Bahasa gaul, empati, simpel. "Wkwk sama bro" "Anjir semangat lu"
2. PANJANG: 1-2 paragraf MAX. Pendek aja.
3. Kalo bisa selipin 1 tips hidup kecil yg gampang.
4. Jangan sok manager. Jadi temen aja.
5. Jangan sebut "AI".

Chat: {text}"""
    }

    prompt = prompt_map[intent]

    if image:
        prompt += "\n\nUser upload gambar. Kalo isinya jadwal/catatan/todo/tulisan, scan dan ubah jadi tabel rapi + kasih saran biar lebih efisien. Kalo foto random, komen kayak temen. Pake bahasa gampang."
        st.toast("Favion scan gambar lu...", icon="🔍")
    else:
        st.toast("Favion nyusun solusi...", icon="🎯")

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
            yield "Limit harian abis bro. Besok jam 7 pagi reset. Rehat dulu kita 😴", "ngobrol"
        else:
            yield "Error bro, coba lagi ya.", "ngobrol"

# ==================== UI ====================
if len(st.session_state.messages) == 0:
    st.markdown('<div class="favion-title">Favion AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="favion-subtitle">FAntastic inoVIsiON<br>Fantastic Problem, A Fantastic Solution<br>Manager Bisnis, Kanal, Belajar, Uang, Waktu 📸</div>', unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("intent") and msg["role"] == "assistant":
            badge_map = {
                "bisnis": "💼 Bisnis", "kanal": "📱 Kanal", "belajar": "📚 Belajar",
                "uang": "💰 Uang", "waktu": "⏰ Waktu", "ngobrol": "💬 Ngobrol",
                "lempar_fanilla": "🎓 Tanya Fanilla"
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
        txt = prompt.get("text", "Favion, tolong rapihin jadwal di foto ini.")
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
