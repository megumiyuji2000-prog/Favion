import streamlit as st
import google.generativeai as genai
from groq import Groq
from openai import OpenAI
from PIL import Image
from datetime import datetime
import pytz, time, requests, io, urllib.parse, base64, re

try:
    from gtts import gTTS
    TTS = True
except: TTS = False

st.set_page_config(page_title="Falio AI", page_icon="logo.png", layout="wide", initial_sidebar_state="collapsed")

try:
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    GROQ_KEY = st.secrets["GROQ_API_KEY"]
    DEEPSEEK_KEY = st.secrets["DEEPSEEK_API_KEY"]
except: st.error("API Key belum diisi. Manage app → Settings → Secrets"); st.stop()

ss = st.session_state
if "messages" not in ss: ss.messages = []
if "chat_count" not in ss: ss.chat_count = 0
if "last_generated_prompt" not in ss: ss.last_generated_prompt = None
if "audio_processed_id" not in ss: ss.audio_processed_id = None
if "selected_model" not in ss: ss.selected_model = "gemini"

MAX_CHAT = 100
IS_DARK = not (6 <= datetime.now(pytz.timezone('Asia/Jakarta')).hour < 18)
T = {"bg": "#0A0A0B" if IS_DARK else "#FFFFFF", "chat_bg": "#18181B" if IS_DARK else "#F4F4F5", "user_bg": "#27272A" if IS_DARK else "#E4E4E7", "text": "#E4E4E7" if IS_DARK else "#18181B", "border": "#27272A" if IS_DARK else "#E4E4E7", "badge_bg": "#18181B" if IS_DARK else "#F4F4F5", "badge_text": "#A1A1AA" if IS_DARK else "#71717A", "primary": "#A78BFA"}
BLACKLIST = ["bom","senjata","bunuh","bunuh diri","teroris","narkoba","bokep","hentai","porn","seks","sex","bugil","telanjang","memek","jembut","kontol","ngentot","coli","masturbasi","ganja","sabu","ekstasi","heroin","kokain"]

def cek_sensitif(t):
    for k in BLACKLIST:
        if k in t.lower(): return True, k
    return False, None

st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html,body,[class*="css"]{{font-family:'Inter',sans-serif;transition:background-color 0.5s ease,color 0.5s ease}}
#MainMenu,footer,header{{visibility:hidden}}
.stApp,.main{{background-color:{T['bg']};transition:background-color 0.5s ease}}
.block-container{{padding-top:1rem!important;padding-bottom:240px!important;max-width:48rem!important}}
.orion-logo{{position:fixed;top:16px;right:16px;z-index:999;width:32px;height:32px}}
.orion-logo img{{border-radius:8px;transition:all 0.5s ease}}
.chat-counter{{position:fixed;top:60px;right:16px;z-index:999;background:{T['chat_bg']};border:1px solid {T['border']};border-radius:20px;padding:6px 14px;font-size:0.8rem;color:{T['badge_text']};font-weight:600;transition:all 0.5s ease}}
.stButton>button[data-testid="scroll-btn"]{{position:fixed!important;bottom:160px!important;right:20px!important;width:36px!important;height:36px!important;background:{T['chat_bg']}!important;border:1px solid {T['border']}!important;border-radius:50%!important;z-index:998!important;cursor:pointer!important;display:flex!important;align-items:center!important;justify-content:center!important;box-shadow:0 2px 8px rgba(0,0,0,.25)!important;padding:0!important;min-height:36px!important;transition:all 0.5s ease}}
.meta-opening{{margin-top:15vh;margin-bottom:2rem}}
.meta-title{{font-size:2.25rem;font-weight:700;color:{T['text']};margin-bottom:2rem;line-height:1.1;letter-spacing:-0.02em;transition:color 0.5s ease}}
.meta-btn{{display:flex;width:100%;text-align:left;padding:16px 20px;margin-bottom:14px;background-color:{T['chat_bg']};border:1px solid {T['border']};border-radius:28px;color:{T['text']};font-size:1rem;cursor:pointer;transition:all.2s;align-items:center}}
.meta-btn:hover{{border-color:{T['primary']};background-color:{T['user_bg']}}}
.meta-btn-icon{{margin-right:14px;font-size:1.2rem}}
.stChatMessage{{padding:0.5rem 0!important}}
[data-testid="stChatMessageAvatar"]{{background-color:#EF4444!important}}
.stChatMessage[data-testid*="assistant"] [data-testid="stChatMessageAvatar"]{{background-color:#F97316!important}}
[data-testid="stChatMessageContent"]{{background-color:{T['chat_bg']}!important;border-radius:20px!important;padding:16px 20px!important;color:{T['text']}!important;border:1px solid {T['border']};line-height:1.7;font-size:0.95rem;margin-left:8px!important;transition:all 0.5s ease}}
.stChatMessage[data-testid*="user"] [data-testid="stChatMessageContent"]{{background-color:{T['user_bg']}!important}}
.stChatInput{{position:fixed!important;bottom:45px!important;left:50%!important;transform:translateX(-50%)!important;width:calc(100% - 20px)!important;max-width:48rem!important;padding:0 1rem!important;background:{T['bg']}!important;z-index:1001!important;height:52px!important;transition:all 0.5s ease}}
.stChatInput>div{{background-color:{T['bg']}!important;border:1.5px solid {T['primary']}!important;border-radius:28px!important;padding:4px 8px!important;height:52px!important;transition:all 0.5s ease}}
.stChatInput textarea{{font-size:1rem!important;min-height:42px!important;color:{T['text']}!important;transition:color 0.5s ease}}
/* Tombol + Upload: MERAH, dipencet jadi PUTIH */
.stChatInput button[kind="secondary"] svg{{fill:#EF4444!important;transition:fill 0.2s ease}}
.stChatInput button[kind="secondary"]:active svg{{fill:#FFFFFF!important}}
.stChatInput button[kind="secondary"]:hover svg{{fill:#DC2626!important}}
/* Tombol send */
.stChatInput button[kind="primary"] svg{{fill:{T['primary']}!important;transition:fill 0.5s ease}}
.orion-badge{{display:inline-block;font-size:.7rem;padding:4px 10px;border-radius:12px;margin-bottom:10px;margin-right:6px;font-weight:600;background-color:{T['badge_bg']};color:{T['badge_text']};border:1px solid {T['border']};transition:all 0.5s ease}}
.model-badge{{background:#A78BFA;color:white}}
.footer-fnl{{position:fixed;bottom:8px;left:16px;transform:none;font-size:0.7rem;color:{T['badge_text']};z-index:1000;transition:color 0.5s ease}}
.typing-indicator{{display:flex;align-items:center;gap:12px;padding:12px 4px;height:40px}}
.typing-indicator span{{width:12px;height:12px;background-color:#000;border-radius:50%;display:inline-block;animation:wave 1.8s infinite ease-in-out}}
.typing-indicator span:nth-child(1){{animation-delay:0s}}
.typing-indicator span:nth-child(2){{animation-delay:0.2s}}
.typing-indicator span:nth-child(3){{animation-delay:0.4s}}
@keyframes wave{{0%,60%,100%{{transform:translateY(0)}} 30%{{transform:translateY(-16px)}}}}
</style>""", unsafe_allow_html=True)

try:
    with open("logo.png", "rb") as f: data = base64.b64encode(f.read()).decode()
    st.markdown(f'<div class="orion-logo"><img src="data:image/png;base64,{data}"></div>', unsafe_allow_html=True)
except: pass

st.markdown(f'<div class="chat-counter">waktu ngobrol {ss.chat_count}/{MAX_CHAT}</div>', unsafe_allow_html=True)

genai.configure(api_key=GEMINI_KEY)
gemini_model = genai.GenerativeModel('gemini-2.5-flash')
groq_client = Groq(api_key=GROQ_KEY)
deepseek_client = OpenAI(api_key=DEEPSEEK_KEY, base_url="https://api.deepseek.com")

def toast(msg, icon="🎯"): st.toast(msg, icon=icon)

def transcribe_audio(audio_bytes):
    try:
        toast("Lagi ubah suara jadi teks...", "⏳")
        t = groq_client.audio.transcriptions.create(file=("audio.wav", audio_bytes), model="whisper-large-v3", language="id", response_format="text", temperature=0.0).strip()
        if len(t) < 3 or t.lower() in ["dan abroh", "terima kasih", "you", ""]: toast("Suara gak kedeteksi jelas", "⚠️"); return ""
        return t
    except Exception as e: toast(f"STT Error: {str(e)[:30]}", "❌"); return ""

def text_to_speech(text):
    if not TTS: return []
    try:
        text = re.sub(r'[#*`\-_]', '', text); text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text).strip()
        chunks = []; t = text
        while t:
            if len(t) <= 3000: chunks.append(t); break
            p = t[:3000].rfind('. '); p = 3000 if p == -1 else p
            chunks.append(t[:p + 1]); t = t[p + 1:].strip()
        audios = []
        for c in chunks:
            tts = gTTS(text=c, lang='id', slow=False); fp = io.BytesIO(); tts.write_to_fp(fp); fp.seek(0); audios.append(fp)
        return audios
    except: return []

def butuh_link_produk(text):
    t = text.lower()
    kp = ["rusak","copot","hilang","patah","pecah","habis","beli","ganti","butuh","cari","rekomendasi","yang bagus","sparepart","suku cadang","minta link","dimana beli"]
    kt = ["cara","gimana","bagaimana","tutorial","langkah","memasak","memasang","memakai","mencopot","menggunakan","pasang"]
    return any(k in t for k in kp) and not any(k in t for k in kt)

def extract_keyword_produk(text):
    stop = ["saya","aku","gue","punya","ini","itu","yang","kok","sih","dong","ya","mulu","terus","sering","kenapa"]
    text = re.sub(r'[^\w\s]', '', text.lower())
    return " ".join([w for w in text.split() if w not in stop and len(w) > 2][:4])

def deteksi_tingkat(t):
    t = t.lower()
    if any(k in t for k in ["solusi","pecahkan","selesaikan","masalah","problem","gimana caranya","bantu atasi","jalan keluar","saran","bingung","pusing","rusak","copot","hilang","patah"]): return "problem_solver"
    if any(k in t for k in ["ubah jadi","jadiin","remix","ganti style","versi","ganti jadi"]) and ss.last_generated_prompt: return "remix"
    if any(k in t for k in ["gambar","bikin","lukis","draw","buatin","generate"]): return "image"
    return "ngobrol"

def generate_gambar(p):
    toast("Maaf jika hasilnya kurang memuaskan 🙏", "🎨"); ss.last_generated_prompt = p
    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(p[:200])}?width=1024&height=1024&nologo=true&seed={int(time.time()) % 10000}"
    try:
        r = requests.get(url, timeout=45)
        return (Image.open(io.BytesIO(r.content)).convert("RGB"), None) if r.status_code == 200 else (None, "Server penuh")
    except: return None, "Error"

def remix_gambar_hasil_generate(pr):
    if not ss.last_generated_prompt: return None, "Buat gambar dulu baru bisa di-remix"
    toast("Maaf jika hasilnya kurang memuaskan 🙏", "✨")
    fp = f"{ss.last_generated_prompt}, {pr}"; ss.last_generated_prompt = fp
    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(fp[:200])}?width=1024&height=1024&nologo=true&seed={int(time.time()) % 10000}"
    try:
        r = requests.get(url, timeout=45)
        return (Image.open(io.BytesIO(r.content)).convert("RGB"), None) if r.status_code == 200 else (None, "Gagal remix")
    except: return None, "Error remix"

def image_to_bytes(img):
    buf = io.BytesIO(); img.save(buf, format="PNG"); return buf.getvalue()

def kirim_ke_ai(prompt, image=None):
    is_sensitif, kata = cek_sensitif(prompt)
    if is_sensitif: return [("text", f"Maaf, aku gak bisa bantu soal '{kata}' ya. Itu termasuk konten sensitif/berbahaya.\n\nKalau kamu lagi ada masalah, coba ngobrol sama orang dewasa yang kamu percaya. Aku bisa bantu topik lain yang positif kok!", "ngobrol")]
    
    tingkat = deteksi_tingkat(prompt)
    if tingkat == "image": img, err = generate_gambar(prompt); return [("image", img, tingkat)] if img else [("text", f"Gagal membuat gambar: {err}", "ngobrol")]
    if tingkat == "remix": img, err = remix_gambar_hasil_generate(prompt); return [("image", img, "remix")] if img else [("text", f"Gagal remix: {err}", "ngobrol")]
    
    perlu_link = butuh_link_produk(prompt); keyword = extract_keyword_produk(prompt) if perlu_link else ""
    tgl = datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%d %B %Y')
    
    if perlu_link:
        ls = f"https://shopee.co.id/search?keyword={urllib.parse.quote(keyword)}"
        lt = f"https://www.tokopedia.com/search?st=product&q={urllib.parse.quote(keyword)}"
        link_instruksi = f'ATURAN PRODUK: User butuh barang. Setelah solusi, WAJIB tambahkan:\n### Rekomendasi Produk\nBerikut link untuk mencari "{keyword}":\n- **Shopee**: [Cari di Shopee]({ls})\n- **Tokopedia**: [Cari di Tokopedia]({lt})'
    else: link_instruksi = "ATURAN PRODUK: User hanya butuh tutorial. JANGAN berikan link produk."
    
    sys_p = f"""Anda adalah Falio AI, asisten AI yang sangat cerdas, teliti, dan akurat. Tanggal: {tgl}.\n\nPRINSIP UTAMA:\n1. AKURASI: Jawaban harus 100% benar.\n2. KEJELASAN: Bahasa Indonesia baku, mudah dipahami.\n3. SOLUTIF: Langkah konkret.\n4. EMPATI: Tunjukkan pemahaman.\n5. KEAMANAN: Tolak permintaan berbahaya/ilegal dengan sopan.\n\nFORMAT PROBLEM SOLVER:\nBasa basi-\n[Tunjukkan empati + validasi + harapan]\n\nOke jadi begini caranya\n1. [Langkah 1: Diagnosis + solusi + contoh]\n2. [Langkah 2: Solusi lanjutan + contoh]\n3. [Langkah 3: Pencegahan + contoh]\n\nJadi gitu cara mengatasinya\n[Rangkum inti. Motivasi. Tawarkan bantuan. Tutup "Sudah paham kan?"]\n\n{link_instruksi}\n\nATURAN TEKNIS:\n1. Jangan sebut "AI". Anda adalah Falio AI.\n2. Gunakan ### untuk heading, `-` untuk bullet, **bold** untuk penekanan.\n3. Untuk link: [Nama Toko](url_lengkap)\n4. Jawab langsung ke inti.\n5. TOLAK konten dewasa/kekerasan/senjata/narkoba/ilegal."""
    
    full_p = sys_p + f"\n\nJenis: {tingkat}\nPertanyaan user: {prompt}"
    loading_placeholder = st.empty()
    with loading_placeholder.container():
        with st.chat_message("assistant"): st.markdown('<div class="typing-indicator"><span></span><span></div>', unsafe_allow_html=True)
    
    model_order = [ss.selected_model]
    if ss.selected_model == "gemini": model_order += ["groq", "deepseek"]
    elif ss.selected_model == "groq": model_order += ["gemini", "deepseek"]
    else: model_order += ["gemini", "groq"]
    
    result = None
    for try_model in model_order:
        try:
            if try_model == "gemini":
                toast("Pake Gemini...", "✨"); content = [full_p]
                if image: content.append(image)
                res = gemini_model.generate_content(content, stream=True)
                full_text = "".join([c.text for c in res if c.text])
            elif try_model == "groq":
                toast("Pake Groq...", "⚡")
                chat = groq_client.chat.completions.create(messages=[{"role": "user", "content": full_p}], model="llama-3.3-70b-versatile", stream=True)
                full_text = "".join([c.choices[0].delta.content for c in chat if c.choices[0].delta.content])
            else:  # deepseek
                toast("Pake DeepSeek...", "🚀")
                chat = deepseek_client.chat.completions.create(messages=[{"role": "user", "content": full_p}], model="deepseek-chat", stream=True)
                full_text = "".join([c.choices[0].delta.content for c in chat if c.choices[0].delta.content])
            if full_text: result = [("text", full_text, tingkat, try_model)]; break
        except Exception as e:
            err = str(e)
            if "401" in err: toast("API Key salah/expired", "❌")
            elif "429" in err: toast("Limit abis, coba model lain...", "⚠️")
            elif "quota" in err.lower(): toast("Quota abis", "⚠️")
            if try_model == model_order[-1]: result = [("text", f"Error: {err[:80]}. Cek API Key di Secrets.", "ngobrol")]
    loading_placeholder.empty()
    return result if result else [("text", "Error gak dikenal.", "ngobrol")]

with st.sidebar:
    st.markdown("### ⚙️ Manage Falio")
    m = st.selectbox("Pilih Model AI", ["Gemini 2.5 Flash", "Llama 3.3 70B Groq", "DeepSeek-V3"], index=["gemini","groq","deepseek"].index(ss.selected_model))
    ss.selected_model = {"Gemini 2.5 Flash":"gemini", "Llama 3.3 70B Groq":"groq", "DeepSeek-V3":"deepseek"}[m]
    if st.button("🗑️ Hapus Semua Chat"): ss.messages = []; ss.chat_count = 0; st.rerun()
    st.metric("Chat Tersisa", f"{MAX_CHAT - ss.chat_count}/{MAX_CHAT}")

if not ss.messages:
    st.markdown('<div class="meta-opening"><div class="meta-title">Ada yang bisa<br>Falio bantu?</div><button class="meta-btn"><span class="meta-btn-icon">🖼️</span> Buat gambar</button><button class="meta-btn"><span class="meta-btn-icon">💡</span> Bantu selesaikan masalah</button><button class="meta-btn"><span class="meta-btn-icon">🎓</span> Belajar dan berkembang</button></div>', unsafe_allow_html=True)

if MAX_CHAT - ss.chat_count == 3: st.toast("Sesi ngobrol hampir habis", icon="⚠️")

for i, msg in enumerate(ss.messages):
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            bc = msg.get("tingkat", "ngobrol")
            bt = {"image": "🎨 GAMBAR", "remix": "✨ REMIX", "ngobrol": "💬 NGOBROL", "problem_solver": "💡 SOLUSI"}.get(bc, "💬")
            model_name = {"gemini":"Gemini", "groq":"Groq", "deepseek":"DeepSeek"}.get(msg.get("model"), "AI")
            st.markdown(f'<div class="orion-badge {bc}">{bt}</div><div class="orion-badge model-badge">{model_name}</div>', unsafe_allow_html=True)
        if msg["type"] == "image":
            st.image(msg["content"], use_container_width=True)
            st.download_button("📥 Unduh", image_to_bytes(msg["content"]), f"falio_{i}.png", "image/png", key=f"dl_{i}", use_container_width=True)
        else:
            st.markdown(msg["content"], unsafe_allow_html=True)
            if msg["role"] == "assistant" and msg["type"] == "text" and TTS:
                if st.button("🔊", key=f"tts_{i}", help="Dengarkan"):
                    audio_files = text_to_speech(msg["content"])
                    if audio_files:
                        for audio_fp in audio_files: st.audio(audio_fp, format='audio/mp3')

if len(ss.messages) > 3:
    col1, col2 = st.columns([10, 1])
    with col2:
        if st.button("↓", key="scroll-btn", help="Scroll ke bawah"): st.markdown("<script>window.scrollTo({top:document.body.scrollHeight,behavior:'smooth'});</script>", unsafe_allow_html=True)

audio_value = st.audio_input("Rekam suara", key=f"audio_recorder_{ss.chat_count}", label_visibility="collapsed")
if audio_value:
    current_audio_id = id(audio_value)
    if ss.audio_processed_id!= current_audio_id:
        ss.audio_processed_id = current_audio_id
        voice_text = transcribe_audio(audio_value.getvalue())
        if voice_text:
            if ss.chat_count >= MAX_CHAT: st.error("Sesi ngobrol hari ini sudah habis"); st.stop()
            ss.chat_count += 1
            ss.messages.append({"role": "user", "type": "text", "content": voice_text})
            hasil = kirim_ke_ai(voice_text, None)
            for tipe, konten, *rest in hasil:
                tingkat = rest[0] if rest else "ngobrol"
                model = rest[1] if len(rest) > 1 else ss.selected_model
                ss.messages.append({"role": "assistant", "type": tipe, "content": konten, "tingkat": tingkat, "model": model})
            st.rerun()

prompt = st.chat_input("Tanya Falio AI...", accept_file=True, file_type=["jpg", "png", "jpeg"])
if prompt:
    if ss.chat_count >= MAX_CHAT: st.error("Sesi ngobrol hari ini sudah habis. Silakan kembali besok 🙏"); st.stop()
    ss.chat_count += 1
    user_text = prompt.text if hasattr(prompt, 'text') else (prompt.get("text", "") if isinstance(prompt, dict) else prompt)
    user_file = prompt.files[0] if hasattr(prompt, 'files') and prompt.files else (prompt.get("files", [None])[0] if isinstance(prompt, dict) and prompt.get("files") else None)
    user_img = None
    if user_file: user_img = Image.open(user_file).convert("RGB"); ss.messages.append({"role": "user", "type": "image", "content": user_img})
    if user_text: ss.messages.append({"role": "user", "type": "text", "content": user_text})
    hasil = kirim_ke_ai(user_text, user_img)
    for tipe, konten, *rest in hasil:
        tingkat = rest[0] if rest else "ngobrol"
        model = rest[1] if len(rest) > 1 else ss.selected_model
        ss.messages.append({"role": "assistant", "type": tipe, "content": konten, "tingkat": tingkat, "model": model})
    st.rerun()

st.markdown('<div class="footer-fnl">falio™ is product of F.N.L</div>', unsafe_allow_html=True)
