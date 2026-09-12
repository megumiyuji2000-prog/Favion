import streamlit as st
import google.generativeai as genai
from groq import Groq
from PIL import Image
from datetime import datetime
import pytz, time, requests, io, urllib.parse, base64, re

try:
    from gtts import gTTS
    TTS = True
except: TTS = False

st.set_page_config(page_title="Falio AI", page_icon="logo.png", layout="centered", initial_sidebar_state="expanded")

try:
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]; GROQ_KEY = st.secrets["GROQ_API_KEY"]; DEEPSEEK_KEY = st.secrets["DEEPSEEK_API_KEY"]
except: st.error("API Key belum diisi."); st.stop()

ss = st.session_state
for k, v in {"messages":[], "chat_count":0, "last_prompt":None, "audio_id":None, "model":"gemini", "pending":None}.items():
    if k not in ss: ss[k] = v
MAX_CHAT = 100
MODELS = {"gemini":"✨ Gemini", "groq":"⚡ Groq", "deepseek":"🧠 DeepSeek"}

DARK = not (6 <= datetime.now(pytz.timezone('Asia/Jakarta')).hour < 18)
T = {"bg":"#0A0A0B" if DARK else "#FFF", "chat":"#18181B" if DARK else "#F4F4F5", "user":"#27272A" if DARK else "#E4E4E7",
     "text":"#E4E4E7" if DARK else "#18181B", "muted":"#A1A1AA" if DARK else "#71717A",
     "border":"#27272A" if DARK else "#E4E4E7", "primary":"#A78BFA"}

BLACK = ["bom","senjata","bunuh","teroris","narkoba","bokep","hentai","porn","seks","sex","bugil","telanjang","memek","kontol","ngentot","coli","masturbasi","ganja","sabu","ekstasi","heroin","kokain"]
def cek_sensitif(t):
    for k in BLACK:
        if k in t.lower(): return True, k
    return False, None

st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html,body,[class*="css"]{{font-family:'Inter',sans-serif;transition:background-color .3s,color .3s}}
#MainMenu,footer,header{{visibility:hidden}}
.stApp{{background:{T['bg']}}}
.block-container{{padding-top:1.5rem!important;padding-bottom:180px!important;max-width:42rem!important;margin:auto!important}}
/* SIDEBAR KANAN */
[data-testid="stSidebar"]{{left:auto!important;right:0!important;border-left:1px solid {T['border']};border-right:none!important;background:{T['chat']}}}
[data-testid="stSidebar"] *{{color:{T['text']}}}
[data-testid="collapsedControl"]{{left:auto!important;right:.5rem!important;top:.5rem!important}}
/* HEADER */
.falio-head{{display:flex;align-items:center;gap:10px}}
.falio-head img{{width:32px;height:32px;border-radius:8px}}
.falio-head b{{color:{T['text']};font-size:1.15rem;font-weight:700}}
/* CHAT BUBBLES */
.stChatMessage{{padding:.3rem 0!important}}
[data-testid="stChatMessageContent"]{{background:{T['chat']}!important;border-radius:16px!important;padding:14px 18px!important;color:{T['text']}!important;border:1px solid {T['border']};line-height:1.7;font-size:.94rem}}
.stChatMessage[data-testid*="user"] [data-testid="stChatMessageContent"]{{background:{T['user']}!important}}
/* INPUT */
.stChatInput{{position:fixed!important;bottom:20px!important;left:50%!important;transform:translateX(-50%)!important;width:calc(100% - 20px)!important;max-width:42rem!important;padding:0 1rem!important;z-index:1001!important}}
.stChatInput>div{{background:{T['bg']}!important;border:1.5px solid {T['primary']}!important;border-radius:24px!important;padding:4px 8px!important}}
.stChatInput textarea{{font-size:.98rem!important;color:{T['text']}!important}}
.stChatInput button[kind="secondary"] svg{{fill:#EF4444!important}}
.stChatInput button[kind="primary"] svg{{fill:{T['primary']}!important}}
/* WELCOME */
.welcome{{text-align:center;margin-top:5vh;margin-bottom:1.5rem}}
.welcome h1{{font-size:2rem;font-weight:700;color:{T['text']};margin-bottom:.4rem}}
.welcome p{{color:{T['muted']};font-size:.95rem}}
.sug-label{{color:{T['muted']};font-size:.72rem;font-weight:600;text-transform:uppercase;letter-spacing:.1em;margin:22px 0 10px;text-align:center}}
/* BUTTONS */
.stButton>button{{background:{T['chat']}!important;color:{T['text']}!important;border:1px solid {T['border']}!important;border-radius:12px!important;padding:10px 14px!important;font-weight:500!important;font-size:.88rem!important;transition:all .15s!important}}
.stButton>button:hover{{border-color:{T['primary']}!important;background:{T['user']}!important}}
/* TYPING */
.typing{{display:flex;gap:6px;padding:10px 0}}
.typing span{{width:8px;height:8px;background:{T['primary']};border-radius:50%;display:inline-block;animation:w 1.4s infinite}}
.typing span:nth-child(2){{animation-delay:.15s}}
.typing span:nth-child(3){{animation-delay:.3s}}
@keyframes w{{0%,60%,100%{{transform:translateY(0);opacity:.4}}30%{{transform:translateY(-6px);opacity:1}}}}
.foot{{text-align:center;font-size:.68rem;color:{T['muted']};margin-top:2rem}}
/* SELECTBOX */
[data-baseweb="select"]>div{{background:{T['chat']}!important;border-color:{T['border']}!important;color:{T['text']}!important;border-radius:10px!important}}
/* METRIC */
[data-testid="stMetricValue"]{{color:{T['primary']}!important;font-size:1.4rem!important}}
</style>""", unsafe_allow_html=True)

# HEADER + MODEL SWITCHER DI CHAT
try:
    with open("logo.png","rb") as f: _l = base64.b64encode(f.read()).decode()
    logo_html = f'<img src="data:image/png;base64,{_l}">'
except: logo_html = ''

hc1, hc2 = st.columns([3, 2])
with hc1:
    st.markdown(f'<div class="falio-head">{logo_html}<b>Falio AI</b></div>', unsafe_allow_html=True)
with hc2:
    ss.model = st.selectbox("Model", list(MODELS.keys()), format_func=lambda x: MODELS[x],
                            index=list(MODELS.keys()).index(ss.model), label_visibility="collapsed",
                            help="Ganti otak AI kapan saja")

genai.configure(api_key=GEMINI_KEY)
gemini_model = genai.GenerativeModel('gemini-2.5-flash')
groq_client = Groq(api_key=GROQ_KEY)
def toast(m,i="🎯"): st.toast(m, icon=i)

def stt(b):
    try:
        toast("Ubah suara ke teks...","⏳")
        t = groq_client.audio.transcriptions.create(file=("a.wav",b), model="whisper-large-v3", language="id", response_format="text", temperature=0.0).strip()
        return "" if len(t)<3 or t.lower() in ["dan abroh","terima kasih","you",""] else t
    except Exception as e: toast(f"STT: {str(e)[:30]}","❌"); return ""

def tts(text):
    if not TTS: return []
    try:
        text = re.sub(r'[#*`\-_]','',text); text = re.sub(r'\[([^\]]+)\]\([^\)]+\)',r'\1',text).strip()
        ch = []; t = text
        while t:
            if len(t)<=3000: ch.append(t); break
            p = t[:3000].rfind('. '); p = 3000 if p==-1 else p
            ch.append(t[:p+1]); t = t[p+1:].strip()
        out = []
        for c in ch:
            fp = io.BytesIO(); gTTS(text=c, lang='id').write_to_fp(fp); fp.seek(0); out.append(fp)
        return out
    except: return []

def butuh_link(t):
    t = t.lower()
    kp = ["rusak","copot","hilang","patah","pecah","habis","beli","ganti","butuh","cari","rekomendasi","sparepart","suku cadang","dimana beli"]
    kt = ["cara","gimana","bagaimana","tutorial","langkah","memasak","memasang","memakai","mencopot","menggunakan","pasang"]
    return any(k in t for k in kp) and not any(k in t for k in kt)

def keyword(t):
    stop = ["saya","aku","gue","punya","ini","itu","yang","kok","sih","dong","ya","mulu","terus","sering","kenapa"]
    t = re.sub(r'[^\w\s]','',t.lower())
    return " ".join([w for w in t.split() if w not in stop and len(w)>2][:4])

def tingkat(t):
    t = t.lower()
    if any(k in t for k in ["solusi","selesaikan","masalah","problem","gimana caranya","bantu atasi","bingung","pusing","rusak","copot","hilang","patah"]): return "problem_solver"
    if any(k in t for k in ["ubah jadi","jadiin","remix","ganti style","versi"]) and ss.last_prompt: return "remix"
    if any(k in t for k in ["gambar","bikin","lukis","draw","buatin","generate"]): return "image"
    return "ngobrol"

def gen_img(p):
    toast("Maaf jika hasil kurang memuaskan 🙏","🎨"); ss.last_prompt = p
    u = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(p[:200])}?width=1024&height=1024&nologo=true&seed={int(time.time())%10000}"
    try:
        r = requests.get(u, timeout=45)
        return (Image.open(io.BytesIO(r.content)).convert("RGB"), None) if r.status_code==200 else (None,"Server penuh")
    except: return None, "Error"

def remix(pr):
    if not ss.last_prompt: return None, "Buat gambar dulu"
    fp = f"{ss.last_prompt}, {pr}"; return gen_img(fp)

def img_bytes(img):
    b = io.BytesIO(); img.save(b, format="PNG"); return b.getvalue()

def call_ds(p):
    try:
        toast("DeepSeek...","🚀")
        h = {"Authorization": f"Bearer {DEEPSEEK_KEY}","Content-Type":"application/json"}
        d = {"model":"deepseek-chat","messages":[{"role":"user","content":p}],"stream":False}
        r = requests.post("https://api.deepseek.com/chat/completions", headers=h, json=d, timeout=60)
        return r.json()["choices"][0]["message"]["content"] if r.status_code==200 else None
    except: return None

def kirim_ai(prompt, image=None):
    s, kata = cek_sensitif(prompt)
    if s: return [("text", f"Maaf, aku gak bisa bantu soal '{kata}'. Itu konten sensitif.\n\nKalau kamu ada masalah, ngobrol sama orang dewasa yang dipercaya ya.", "ngobrol", ss.model)]
    lv = tingkat(prompt)
    if lv == "image":
        im, e = gen_img(prompt)
        return [("image", im, lv, ss.model)] if im else [("text", f"Gagal: {e}", "ngobrol", ss.model)]
    if lv == "remix":
        im, e = remix(prompt)
        return [("image", im, "remix", ss.model)] if im else [("text", f"Gagal: {e}", "ngobrol", ss.model)]
    pl = butuh_link(prompt); kw = keyword(prompt) if pl else ""
    tgl = datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%d %B %Y')
    if pl:
        ls = f"https://shopee.co.id/search?keyword={urllib.parse.quote(kw)}"
        lt = f"https://www.tokopedia.com/search?st=product&q={urllib.parse.quote(kw)}"
        li = f'ATURAN: Setelah solusi WAJIB tambah:\n### Rekomendasi Produk\n- **Shopee**: [Cari di Shopee]({ls})\n- **Tokopedia**: [Cari di Tokopedia]({lt})'
    else: li = "ATURAN: User hanya butuh tutorial. JANGAN beri link produk."
    sysp = f"""Anda Falio AI, asisten AI 2026 yang cerdas, teliti, akurat. Tanggal: {tgl}.
PRINSIP: akurasi, kejelasan, solutif, empati, keamanan.
FORMAT PROBLEM SOLVER:
Basa basi-
[empati + validasi]
Oke jadi begini caranya
1. [Diagnosis + solusi]
2. [Solusi lanjutan]
3. [Pencegahan]
Jadi gitu cara mengatasinya
[Rangkum + tutup "Sudah paham kan?"]
{li}
TEKNIS: Heading ###, bullet -, bold **teks**, link [Nama](url). Tolak konten dewasa/kekerasan/senjata/narkoba/ilegal."""
    full = sysp + f"\n\nJenis: {lv}\nPertanyaan: {prompt}"
    ph = st.empty()
    with ph.container():
        with st.chat_message("assistant"): st.markdown('<div class="typing"><span></span><span></span><span></span></div>', unsafe_allow_html=True)
    order = [ss.model] + [m for m in ["gemini","groq","deepseek"] if m != ss.model]
    res = None
    for tm in order:
        try:
            if tm == "gemini":
                toast("Gemini...","✨")
                c = [full] + ([image] if image else [])
                r = gemini_model.generate_content(c, stream=True)
                txt = "".join([x.text for x in r if x.text])
            elif tm == "groq":
                toast("Groq...","⚡")
                ch = groq_client.chat.completions.create(messages=[{"role":"user","content":full}], model="llama-3.3-70b-versatile", stream=True)
                txt = "".join([x.choices[0].delta.content for x in ch if x.choices[0].delta.content])
            else: txt = call_ds(full)
            if txt: res = [("text", txt, lv, tm)]; break
        except Exception as e:
            err = str(e)
            if "401" in err: toast("API Key salah","❌")
            elif "429" in err: toast("Limit abis, coba model lain...","⚠️")
            if tm == order[-1]: res = [("text", f"Error: {err[:80]}", "ngobrol", ss.model)]
    ph.empty()
    return res or [("text","Error gak dikenal.","ngobrol", ss.model)]

# SIDEBAR KANAN
with st.sidebar:
    st.markdown("### ⚙️ Pengaturan")
    st.metric("💬 Sisa chat hari ini", f"{MAX_CHAT - ss.chat_count}/{MAX_CHAT}")
    st.divider()
    if st.button("🔄 Mulai obrolan baru", use_container_width=True):
        ss.messages = []; st.rerun()
    if ss.messages:
        md = "# Obrolan Falio AI\n\n"
        for m in ss.messages:
            role = "**Kamu**" if m["role"]=="user" else "**Falio**"
            md += f"{role}: {m['content'] if m['type']=='text' else '*(gambar)*'}\n\n"
        st.download_button("💾 Simpan obrolan", md, file_name="falio_chat.md", use_container_width=True)
    st.divider()
    st.markdown("**💡 Tips**")
    st.caption("• Ganti model kapan saja di kanan atas")
    st.caption("• Kirim suara lewat tombol 🎤")
    st.caption("• Upload gambar lewat tombol 📎")
    st.caption("• Falio ingat konteks obrolan")

# AREA CHAT
if not ss.messages:
    st.markdown('<div class="welcome"><h1>Halo! 👋</h1><p>Aku Falio AI, siap bantu kamu hari ini.</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="sug-label">Coba tanya ini</div>', unsafe_allow_html=True)
    sugs = [("🖼️","Buat gambar kucing astronot"),("💡","Cara atasi laptop lemot"),
            ("🎓","Jelaskan AI dengan analogi sederhana"),("✍️","Tulis caption IG soal produktivitas")]
    c1, c2 = st.columns(2)
    for i, (ic, txt) in enumerate(sugs):
        with (c1 if i%2==0 else c2):
            if st.button(f"{ic}  {txt}", key=f"sg_{i}", use_container_width=True):
                ss.pending = txt; st.rerun()

for i, m in enumerate(ss.messages):
    with st.chat_message(m["role"]):
        if m["type"] == "image":
            st.image(m["content"], use_container_width=True)
            st.download_button("📥 Unduh gambar", img_bytes(m["content"]), f"falio_{i}.png", "image/png", key=f"dl_{i}", use_container_width=True)
        else:
            st.markdown(m["content"], unsafe_allow_html=True)
            if m["role"] == "assistant":
                used = MODELS.get(m.get("model"), "AI")
                a1, a2 = st.columns([4, 1])
                with a1: st.caption(f"🤖 dijawab oleh {used}")
                with a2:
                    if TTS and st.button("🔊", key=f"tts_{i}", help="Dengarkan"):
                        for a in tts(m["content"]): st.audio(a, format='audio/mp3')

# INPUT
av = st.audio_input("🎤 Rekam suara", key=f"au_{ss.chat_count}", label_visibility="collapsed")
if av and ss.audio_id != id(av):
    ss.audio_id = id(av)
    vt = stt(av.getvalue())
    if vt: ss.pending = vt; st.rerun()

p = st.chat_input("Tanya Falio apa saja...", accept_file=True, file_type=["jpg","png","jpeg","webp"])
if ss.pending and not p:
    p = type("P", (), {"text": ss.pending, "files": None})(); ss.pending = None

if p:
    if ss.chat_count >= MAX_CHAT:
        st.error("Sesi hari ini habis. Kembali besok 🙏"); st.stop()
    ss.chat_count += 1
    utext = getattr(p, "text", None) or ""
    ufiles = getattr(p, "files", None)
    ufile = ufiles[0] if ufiles else None
    uimg = None
    if ufile:
        uimg = Image.open(ufile).convert("RGB")
        ss.messages.append({"role":"user","type":"image","content":uimg})
    if utext: ss.messages.append({"role":"user","type":"text","content":utext})
    for tipe, konten, *rest in kirim_ai(utext, uimg):
        lv = rest[0] if rest else "ngobrol"; md = rest[1] if len(rest)>1 else ss.model
        ss.messages.append({"role":"assistant","type":tipe,"content":konten,"tingkat":lv,"model":md})
    st.rerun()

st.markdown('<div class="foot">falio™ — product of F.N.L</div>', unsafe_allow_html=True)
