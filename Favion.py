import streamlit as st
import google.generativeai as genai
from groq import Groq
from PIL import Image
from datetime import datetime
import pytz, time, requests, io, urllib.parse, base64, re, uuid

try:
    from gtts import gTTS
    TTS = True
except: TTS = False

st.set_page_config(page_title="Falio AI", page_icon="logo.png", layout="wide", initial_sidebar_state="expanded")

try:
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]; GROQ_KEY = st.secrets["GROQ_API_KEY"]; DEEPSEEK_KEY = st.secrets["DEEPSEEK_API_KEY"]
except: st.error("API Key belum diisi. Manage app → Settings → Secrets"); st.stop()

ss = st.session_state
if "sessions" not in ss: ss.sessions = {"default": {"title":"Obrolan Baru","messages":[]}}
if "active" not in ss: ss.active = "default"
if "chat_count" not in ss: ss.chat_count = 0
if "last_generated_prompt" not in ss: ss.last_generated_prompt = None
if "audio_id" not in ss: ss.audio_id = None
if "model" not in ss: ss.model = "gemini"
if "theme" not in ss: ss.theme = "auto"
if "memory" not in ss: ss.memory = []
if "pending" not in ss: ss.pending = None
if "feedback" not in ss: ss.feedback = {}
MAX_CHAT = 100

if ss.theme == "auto": DARK = not (6 <= datetime.now(pytz.timezone('Asia/Jakarta')).hour < 18)
elif ss.theme == "dark": DARK = True
else: DARK = False
T = {"bg":"#0A0A0B" if DARK else "#FFF","chat":"#18181B" if DARK else "#F4F4F5","user":"#27272A" if DARK else "#E4E4E7","text":"#E4E4E7" if DARK else "#18181B","muted":"#A1A1AA" if DARK else "#71717A","border":"#27272A" if DARK else "#E4E4E7","primary":"#A78BFA"}

BLACK = ["bom","senjata","bunuh","teroris","narkoba","bokep","hentai","porn","seks","sex","bugil","telanjang","memek","kontol","ngentot","coli","masturbasi","ganja","sabu","ekstasi","heroin","kokain"]
def cek_sensitif(t):
    for k in BLACK:
        if k in t.lower(): return True, k
    return False, None

st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html,body,[class*="css"]{{font-family:'Inter',sans-serif;transition:background-color .4s,color .4s}}
#MainMenu,footer,header{{visibility:hidden}}
.stApp,.main{{background-color:{T['bg']}}}
.block-container{{padding-top:1.2rem!important;padding-bottom:200px!important;max-width:44rem!important;margin:auto!important}}
.falio-logo{{position:fixed;top:14px;left:18px;z-index:999;display:flex;align-items:center;gap:10px}}
.falio-logo img{{width:30px;height:30px;border-radius:8px}}
.falio-logo span{{color:{T['text']};font-weight:700;font-size:1rem}}
.stChatMessage{{padding:.4rem 0!important}}
[data-testid="stChatMessageContent"]{{background:{T['chat']}!important;border-radius:18px!important;padding:14px 18px!important;color:{T['text']}!important;border:1px solid {T['border']};line-height:1.7;font-size:.94rem}}
.stChatMessage[data-testid*="user"] [data-testid="stChatMessageContent"]{{background:{T['user']}!important}}
.stChatInput{{position:fixed!important;bottom:20px!important;left:50%!important;transform:translateX(-50%)!important;width:calc(100% - 20px)!important;max-width:44rem!important;padding:0 1rem!important;z-index:1001!important}}
.stChatInput>div{{background:{T['bg']}!important;border:1.5px solid {T['primary']}!important;border-radius:26px!important;padding:4px 8px!important}}
.stChatInput textarea{{font-size:.98rem!important;color:{T['text']}!important}}
.stChatInput button[kind="secondary"] svg{{fill:#EF4444!important}}
.stChatInput button[kind="primary"] svg{{fill:{T['primary']}!important}}
.badge{{display:inline-block;font-size:.68rem;padding:3px 9px;border-radius:10px;margin-right:6px;margin-bottom:8px;font-weight:600;background:{T['chat']};color:{T['muted']};border:1px solid {T['border']}}}
.badge.model{{background:{T['primary']};color:#fff;border:none}}
.hero{{text-align:center;margin-top:12vh;margin-bottom:2rem}}
.hero h1{{font-size:2.5rem;font-weight:700;color:{T['text']};margin-bottom:.6rem;line-height:1.1}}
.hero p{{color:{T['muted']};font-size:.95rem}}
.sug-title{{color:{T['muted']};font-size:.78rem;font-weight:600;text-transform:uppercase;letter-spacing:.08em;margin:22px 0 10px}}
.stButton>button{{background:{T['chat']}!important;color:{T['text']}!important;border:1px solid {T['border']}!important;border-radius:14px!important;text-align:left!important;padding:12px 16px!important;font-weight:500!important;font-size:.9rem!important}}
.stButton>button:hover{{border-color:{T['primary']}!important;background:{T['user']}!important}}
.typing{{display:flex;gap:6px;padding:10px 0}}
.typing span{{width:8px;height:8px;background:{T['primary']};border-radius:50%;display:inline-block;animation:w 1.4s infinite}}
.typing span:nth-child(2){{animation-delay:.15s}}.typing span:nth-child(3){{animation-delay:.3s}}
@keyframes w{{0%,60%,100%{{transform:translateY(0);opacity:.4}}30%{{transform:translateY(-6px);opacity:1}}}}
.foot{{position:fixed;bottom:4px;left:16px;font-size:.68rem;color:{T['muted']};z-index:1000}}
[data-testid="stSidebar"]{{background:{T['chat']};border-right:1px solid {T['border']}}}
[data-testid="stSidebar"] *{{color:{T['text']}}}
</style>""", unsafe_allow_html=True)

try:
    with open("logo.png","rb") as f: _l = base64.b64encode(f.read()).decode()
    st.markdown(f'<div class="falio-logo"><img src="data:image/png;base64,{_l}"><span>Falio AI</span></div>', unsafe_allow_html=True)
except: pass

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
    if any(k in t for k in ["ubah jadi","jadiin","remix","ganti style","versi"]) and ss.last_generated_prompt: return "remix"
    if any(k in t for k in ["gambar","bikin","lukis","draw","buatin","generate"]): return "image"
    return "ngobrol"

def gen_img(p):
    toast("Maaf jika hasil kurang memuaskan 🙏","🎨"); ss.last_generated_prompt = p
    u = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(p[:200])}?width=1024&height=1024&nologo=true&seed={int(time.time())%10000}"
    try:
        r = requests.get(u, timeout=45)
        return (Image.open(io.BytesIO(r.content)).convert("RGB"), None) if r.status_code==200 else (None,"Server penuh")
    except: return None, "Error"

def remix(pr):
    if not ss.last_generated_prompt: return None, "Buat gambar dulu"
    fp = f"{ss.last_generated_prompt}, {pr}"; ss.last_generated_prompt = fp
    return gen_img(fp)

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

def mem_ctx():
    return ("\nMEMORI PENGGUNA:\n- " + "\n- ".join(ss.memory[-8:])) if ss.memory else ""

def kirim_ai(prompt, image=None):
    s, kata = cek_sensitif(prompt)
    if s: return [("text", f"Maaf, aku gak bisa bantu soal '{kata}'. Itu konten sensitif.\n\nKalau kamu ada masalah, ngobrol sama orang dewasa yang dipercaya ya. Aku bisa bantu topik lain!", "ngobrol", ss.model)]
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
    sysp = f"""Anda Falio AI, asisten AI generasi 2026 yang cerdas, teliti, akurat. Tanggal: {tgl}.{mem_ctx()}
PRINSIP: akurasi, kejelasan, solutif, empati, keamanan.
FORMAT PROBLEM SOLVER:
Basa basi-
[empati + validasi]
Oke jadi begini caranya
1. [Diagnosis + solusi]
2. [Solusi lanjutan]
3. [Pencegahan]
Jadi gitu cara mengatasinya
[Rangkum + motivasi + tutup "Sudah paham kan?"]
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

def copy_btn(text, key):
    enc = base64.b64encode(text.encode()).decode()
    st.markdown(f"""<button onclick="navigator.clipboard.writeText(atob('{enc}'));this.innerText='✓';setTimeout(()=>this.innerText='📋',1500)" style="background:{T['chat']};color:{T['text']};border:1px solid {T['border']};border-radius:8px;padding:4px 10px;font-size:.72rem;cursor:pointer;font-weight:600">📋</button>""", unsafe_allow_html=True)

def save_title(p):
    s = ss.sessions[ss.active]
    if s["title"] == "Obrolan Baru" and p: s["title"] = p[:40] + ("..." if len(p)>40 else "")

with st.sidebar:
    st.markdown("### ⚙️ Kontrol")
    ml = st.selectbox("Model AI", ["Gemini 2.5 Flash","Llama 3.3 70B (Groq)","DeepSeek-V3"], index=["gemini","groq","deepseek"].index(ss.model))
    ss.model = {"Gemini 2.5 Flash":"gemini","Llama 3.3 70B (Groq)":"groq","DeepSeek-V3":"deepseek"}[ml]
    ss.theme = st.radio("Tema", ["auto","light","dark"], index=["auto","light","dark"].index(ss.theme), horizontal=True)
    st.divider()
    st.markdown("### 💬 Sesi")
    names = {k: v["title"] for k, v in ss.sessions.items()}
    pick = st.selectbox("Pilih Sesi", list(names.keys()), format_func=lambda x: names[x], index=list(names.keys()).index(ss.active))
    ss.active = pick
    c1, c2 = st.columns(2)
    with c1:
        if st.button("➕ Baru", use_container_width=True):
            nid = uuid.uuid4().hex[:8]
            ss.sessions[nid] = {"title":"Obrolan Baru","messages":[]}
            ss.active = nid; st.rerun()
    with c2:
        if st.button("🗑️ Hapus", use_container_width=True):
            if len(ss.sessions) > 1: del ss.sessions[ss.active]; ss.active = list(ss.sessions.keys())[0]
            else: ss.sessions[ss.active]["messages"] = []
            st.rerun()
    msgs = ss.sessions[ss.active]["messages"]
    if msgs:
        md = f"# {ss.sessions[ss.active]['title']}\n\n"
        for m in msgs:
            role = "**User**" if m["role"]=="user" else "**Falio**"
            md += f"{role}: {m['content'] if m['type']=='text' else '*(gambar)*'}\n\n"
        st.download_button("📥 Ekspor (.md)", md, file_name=f"falio_{ss.active}.md", use_container_width=True)
    st.divider()
    st.metric("Chat Tersisa", f"{MAX_CHAT - ss.chat_count}/{MAX_CHAT}")
    if ss.memory:
        with st.expander(f"🧠 Memori ({len(ss.memory)})"):
            for i, m in enumerate(ss.memory): st.caption(f"{i+1}. {m}")
            if st.button("Kosongkan", use_container_width=True): ss.memory = []; st.rerun()

msgs = ss.sessions[ss.active]["messages"]
if not msgs:
    st.markdown('<div class="hero"><h1>Halo, ada yang bisa<br>Falio bantu?</h1><p>Asisten AI 2026 — multimodal, kontekstual, punya memori.</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="sug-title">Coba salah satu</div>', unsafe_allow_html=True)
    sugs = [("🖼️","Buat gambar kucing astronot di bulan"),("💡","Bantu atasi laptop lemot"),("🎓","Jelaskan quantum computing dengan analogi sederhana"),("✍️","Tulis caption Instagram tentang produktivitas pagi")]
    cols = st.columns(2)
    for i, (ic, txt) in enumerate(sugs):
        with cols[i%2]:
            if st.button(f"{ic}  {txt}", key=f"sg_{i}", use_container_width=True): ss.pending = txt; st.rerun()

for i, m in enumerate(msgs):
    with st.chat_message(m["role"]):
        if m["role"] == "assistant":
            bc = m.get("tingkat","ngobrol")
            bt = {"image":"🎨 Gambar","remix":"✨ Remix","ngobrol":"💬 Ngobrol","problem_solver":"💡 Solusi"}.get(bc,"💬")
            mn = {"gemini":"Gemini","groq":"Groq","deepseek":"DeepSeek"}.get(m.get("model"),"AI")
            st.markdown(f'<span class="badge">{bt}</span><span class="badge model">{mn}</span>', unsafe_allow_html=True)
        if m["type"] == "image":
            st.image(m["content"], use_container_width=True)
            st.download_button("📥 Unduh", img_bytes(m["content"]), f"falio_{i}.png", "image/png", key=f"dl_{i}", use_container_width=True)
        else:
            st.markdown(m["content"], unsafe_allow_html=True)
            if m["role"] == "assistant":
                c1, c2, c3, c4 = st.columns([1,1,1,5])
                with c1: copy_btn(m["content"], f"cp_{i}")
                with c2:
                    if TTS and st.button("🔊", key=f"tts_{i}", help="Dengarkan"):
                        for a in tts(m["content"]): st.audio(a, format='audio/mp3')
                with c3:
                    fb = ss.feedback.get(i)
                    if st.button("✅" if fb=="up" else "👍", key=f"up_{i}"):
                        ss.feedback[i] = "up"; toast("Makasih feedbacknya!","👍"); st.rerun()
                with c4:
                    if st.button("👎" if fb!="down" else "📝", key=f"dn_{i}"):
                        ss.feedback[i] = "down"; toast("Maaf ya, aku catat untuk perbaikan","📝"); st.rerun()

av = st.audio_input("🎤 Rekam suara", key=f"au_{ss.chat_count}", label_visibility="collapsed")
if av and ss.audio_id != id(av):
    ss.audio_id = id(av)
    vt = stt(av.getvalue())
    if vt: ss.pending = vt; st.rerun()

p = st.chat_input("Tanya Falio AI...", accept_file=True, file_type=["jpg","png","jpeg","webp"])
if ss.pending and not p:
    p = type("P", (), {"text": ss.pending, "files": None})(); ss.pending = None

if p:
    if ss.chat_count >= MAX_CHAT: st.error("Sesi hari ini habis. Kembali besok 🙏"); st.stop()
    ss.chat_count += 1
    utext = getattr(p, "text", None) or ""
    ufiles = getattr(p, "files", None)
    ufile = ufiles[0] if ufiles else None
    uimg = None
    if ufile:
        uimg = Image.open(ufile).convert("RGB")
        msgs.append({"role":"user","type":"image","content":uimg})
    if utext:
        msgs.append({"role":"user","type":"text","content":utext})
        save_title(utext)
    for tipe, konten, *rest in kirim_ai(utext, uimg):
        lv = rest[0] if rest else "ngobrol"; md = rest[1] if len(rest)>1 else ss.model
        msgs.append({"role":"assistant","type":tipe,"content":konten,"tingkat":lv,"model":md})
    if utext and len(utext)>12 and any(k in utext.lower() for k in ["aku suka","nama aku","aku tinggal","aku kerja","hobi aku","aku punya"]):
        ss.memory.append(utext[:120])
    st.rerun()

st.markdown('<div class="foot">falio™ — product of F.N.L</div>', unsafe_allow_html=True)
