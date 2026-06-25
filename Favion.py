import streamlit as st
import google.generativeai as genai
from groq import Groq
from PIL import Image
from datetime import datetime, timedelta
import pytz, time, requests, io, urllib.parse, base64, re

st.set_page_config(page_title="Falio AI", page_icon="logo.png", layout="wide", initial_sidebar_state="collapsed")

try:
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    GROQ_KEY = st.secrets["GROQ_API_KEY"]
except: st.error("API Key belum diisi. Manage app → Settings → Secrets"); st.stop()

ss = st.session_state
if "messages" not in ss: ss.messages = []
if "chat_count" not in ss: ss.chat_count = 0
if "last_generated_prompt" not in ss: ss.last_generated_prompt = None
if "audio_processed_id" not in ss: ss.audio_processed_id = None
if "selected_model" not in ss: ss.selected_model = "gemini"
if "mode" not in ss: ss.mode = "normal"
if "aib_chats" not in ss: ss.aib_chats = []

MAX_CHAT = 70
IS_DARK = not (6 <= datetime.now(pytz.timezone('Asia/Jakarta')).hour < 18)
T = {"bg": "#0A0A0B" if IS_DARK else "#FFFFFF", "chat_bg": "#18181B" if IS_DARK else "#F4F4F5", "user_bg": "#27272A" if IS_DARK else "#E4E4E7", "text": "#E4E4E7" if IS_DARK else "#18181B", "border": "#27272A" if IS_DARK else "#E4E4E7", "badge_bg": "#18181B" if IS_DARK else "#F4F4F5", "badge_text": "#A1A1AA" if IS_DARK else "#71717A", "primary": "#A78BFA", "danger": "#EF4444"}
BLACKLIST = ["bom","senjata","bunuh","bunuh diri","teroris","narkoba","bokep","hentai","porn","seks","sex","bugil","telanjang","memek","jembut","kontol","ngentot","coli","masturbasi","ganja","sabu","ekstasi","heroin","kokain"]

def cek_sensitif(t):
    for k in BLACKLIST:
        if k in t.lower(): return True, k
    return False, None

def hapus_aib_expired():
    now = datetime.now(pytz.timezone('Asia/Jakarta'))
    ss.aib_chats = [c for c in ss.aib_chats if now - c['time'] < timedelta(hours=24)]

st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html,body,[class*="css"]{{font-family:'Inter',sans-serif}}
#MainMenu,footer,header{{visibility:hidden}}
.stApp,.main{{background-color:{T['bg']}}}
.block-container{{padding-top:1rem!important;padding-bottom:240px!important;max-width:48rem!important}}
.orion-logo{{position:fixed;top:16px;right:16px;z-index:999;width:32px;height:32px}}
.orion-logo img{{border-radius:8px}}
.chat-counter{{position:fixed;top:60px;right:16px;z-index:999;background:{T['chat_bg']};border:1px solid {T['border']};border-radius:20px;padding:6px 14px;font-size:0.8rem;color:{T['badge_text']};font-weight:600}}
.mode-badge{{position:fixed;top:100px;right:16px;z-index:999;background:{T['primary']};color:white;border-radius:20px;padding:6px 14px;font-size:0.8rem;font-weight:600}}
.stButton>button[data-testid="scroll-btn"]{{position:fixed!important;bottom:160px!important;right:20px!important;width:36px!important;height:36px!important;background:{T['chat_bg']}!important;border:1px solid {T['border']}!important;border-radius:50%!important;z-index:998!important;cursor:pointer!important;display:flex!important;align-items:center!important;justify-content:center!important;box-shadow:0 2px 8px rgba(0,0,0,.25)!important;padding:0!important;min-height:36px!important}}
.meta-opening{{margin-top:15vh;margin-bottom:2rem}}
.meta-title{{font-size:2.25rem;font-weight:700;color:{T['text']};margin-bottom:2rem;line-height:1.1;letter-spacing:-0.02em}}
.meta-btn{{display:flex;width:100%;text-align:left;padding:16px 20px;margin-bottom:14px;background-color:{T['chat_bg']};border:1px solid {T['border']};border-radius:28px;color:{T['text']};font-size:1rem;cursor:pointer;transition:all.2s;align-items:center}}
.meta-btn:hover{{border-color:{T['primary']};background-color:{T['user_bg']}}}
.meta-btn-icon{{margin-right:14px;font-size:1.2rem}}
.stChatMessage{{padding:0.5rem 0!important}}
[data-testid="stChatMessageAvatar"]{{background-color:#EF4444!important}}
.stChatMessage[data-testid*="assistant"] [data-testid="stChatMessageAvatar"]{{background-color:#F97316!important}}
[data-testid="stChatMessageContent"]{{background-color:{T['chat_bg']}!important;border-radius:20px!important;padding:16px 20px!important;color:{T['text']}!important;border:1px solid {T['border']};line-height:1.7;font-size:0.95rem;margin-left:8px!important}}
.stChatMessage[data-testid*="user"] [data-testid="stChatMessageContent"]{{background-color:{T['user_bg']}!important}}
.stChatInput{{position:fixed!important;bottom:45px!important;left:50%!important;transform:translateX(-50%)!important;width:calc(100% - 20px)!important;max-width:48rem!important;padding:0 1rem!important;background:{T['bg']}!important;z-index:1001!important;height:52px!important}}
.stChatInput>div{{background-color:{T['bg']}!important;border:1.5px solid {T['primary']}!important;border-radius:28px!important;padding:4px 8px!important;height:52px!important}}
.stChatInput textarea{{font-size:1rem!important;min-height:42px!important}}
.orion-badge{{display:inline-block;font-size:.7rem;padding:4px 10px;border-radius:12px;margin-bottom:10px;margin-right:6px;font-weight:600;background-color:{T['badge_bg']};color:{T['badge_text']};border:1px solid {T['border']}}}
.model-badge{{background:#A78BFA;color:white}}
.danger-badge{{background:{T['danger']};color:white}}
.footer-fnl{{position:fixed;bottom:8px;left:16px;transform:none;font-size:0.7rem;color:{T['badge_text']};z-index:1000}}
.typing-indicator{{display:flex;align-items:center;gap:12px;padding:12px 4px;height:40px}}
.typing-indicator span{{width:12px;height:12px;background-color:#000;border-radius:50%;display:inline-block;animation:wave 1.8s infinite ease-in-out}}
.typing-indicator span:nth-child(1){{animation-delay:0s}}
.typing-indicator span:nth-child(2){{animation-delay:0.2s}}
.typing-indicator span:nth-child(3){{animation-delay:0.4s}}
@keyframes wave{{0%,60%,100%{{transform:translateY(0)}} 30%{{transform:translateY(-16px)}}}}
.burn-btn{{background:{T['danger']}!important;color:white!important;border:none!important;border-radius:20px!important;padding:8px 16px!important;margin-top:10px!important}}
</style>""", unsafe_allow_html=True)

hapus_aib_expired()

try:
    with open("logo.png", "rb") as f: data = base64.b64encode(f.read()).decode()
    st.markdown(f'<div class="orion-logo"><img src="data:image/png;base64,{data}"></div>', unsafe_allow_html=True)
except: pass

st.markdown(f'<div class="chat-counter">waktu ngobrol {ss.chat_count}/{MAX_CHAT}</div>', unsafe_allow_html=True)
mode_text = {"normal": "💬 Normal", "aib": "🔥 Mode Aib", "dokter": "🔧 Dokter Gadget", "dukun": "💸 Dukun Harga"}
st.markdown(f'<div class="mode-badge">{mode_text[ss.mode]}</div>', unsafe_allow_html=True)

genai.configure(api_key=GEMINI_KEY)
gemini_model = genai.GenerativeModel('gemini-2.5-flash')
groq_client = Groq(api_key=GROQ_KEY)

def toast(msg, icon="🎯"): st.toast(msg, icon=icon)

def transcribe_audio(audio_bytes):
    try:
        toast("Lagi ubah suara jadi teks...", "⏳")
        t = groq_client.audio.transcriptions.create(file=("audio.wav", audio_bytes), model="whisper-large-v3", language="id", response_format="text", temperature=0.0).strip()
        if len(t) < 3 or t.lower() in ["dan abroh", "terima kasih", "you", ""]: toast("Suara gak kedeteksi jelas", "⚠️"); return ""
        return t
    except Exception as e: toast(f"STT Error: {str(e)[:30]}", "❌"); return ""

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
    if is_sensitif and ss.mode!= "aib": return [("text", f"Maaf, aku gak bisa bantu soal '{kata}' ya. Itu termasuk konten sensitif/berbahaya.\n\nKalau kamu lagi ada masalah, coba ngobrol sama orang dewasa yang kamu percaya. Aku bisa bantu topik lain yang positif kok!", "ngobrol")]
    
    tingkat = deteksi_tingkat(prompt)
    if tingkat == "image": img, err = generate_gambar(prompt); return [("image", img, tingkat)] if img else [("text", f"Gagal membuat gambar: {err}", "ngobrol")]
    if tingkat == "remix": img, err = remix_gambar_hasil_generate(prompt); return [("image", img, "remix")] if img else [("text", f"Gagal remix: {err}", "ngobrol")]
    
    perlu_link = butuh_link_produk(prompt); keyword = extract_keyword_produk(prompt) if perlu_link else ""
    tgl = datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%d %B %Y')
    
    if ss.mode == "aib":
        sys_p = f"""Anda adalah Falio AI dalam Mode Ngobrolin Aib. Tugasmu jadi temen nongkrong yang gak judge. Tanggal: {tgl}.

ATURAN MODE AIB:
1. Bahasa anak tongkrongan: "bro", "anjir", "gila sih", "sakit tapi real"
2. NO CERAMAH. Validasi perasaan user dulu: "Wajar sih lu ngerasa gitu"
3. Kasih perspektif + solusi konkret tapi santai
4. Jangan sebut "AI" atau "sebagai asisten". Lu adalah Falio, temennya
5. Boleh pake kata kasar ringan kalo konteksnya pas, tapi jangan toxic
6. Tetep TOLAK: bunuh diri, narkoba, kekerasan, porn. Arahkan ke profesional

FORMAT:
Basa basi-
[Validasi + empati pake bahasa gaul]

Gini bro menurut gue
[Analisis + solusi konkret + contoh]

Udah ya jangan overthinking
[Penutup nyemangatin + tawarin bantuan lain]

JANGAN KASIH LINK PRODUK DI MODE INI."""
    elif ss.mode == "dokter":
        sys_p = f"""Anda adalah Falio AI dalam Mode Dokter Gadget Kampung. Lu montir elektronik yang jago tapi bahasanya orang bengkel. Tanggal: {tgl}.

ATURAN DOKTER GADGET:
1. Diagnosis dari foto + deskripsi suara/gejala user
2. Pake istilah bengkel: "dinamo", "kapasitor", "IC", "flexible", "bad sector"
3. Kasih 3 level solusi: Darurat (DIY), Bengkel (bawa ke tuser), Lembiru (ganti baru)
4. WAJIB kasih estimasi harga part + link Shopee/Tokopedia
5. Kasih tutorial YouTube kalo ada
6. Bahasa: "kayanya", "coba cek", "biasanya sih", "bro"

FORMAT:
Diagnosa awal
[Gejala apa + kemungkinan rusak apa]

Solusi Darurat 💉
[Langkah DIY + resiko]

Solusi Bengkel 🔧
[Part apa yang diganti + estimasi harga]
### Link Sparepart
- **Shopee**: [link]
- **Tokopedia**: [link]

Lembiru 🗑️
[Kapan harus ganti baru]"""
    elif ss.mode == "dukun":
        sys_p = f"""Anda adalah Falio AI dalam Mode Dukun Harga. Tugasmu scan struk/menu/foto barang, tebak kemahalan atau gak. Tanggal: {tgl}.

ATURAN DUKUN HARGA:
1. Analisis item di struk/menu, bandingin sama harga pasar Jakarta rata-rata 2026
2. Kasih label: ✅ Wajar, ⚠️ Agak Mahal, 🩸 Getok Harga
3. Kalo mahal, kasih data pembanding: "Es teh di warteg biasa 3-5rb bro"
4. Kasih script protes sopan tapi nusuk
5. Pake bahasa: "anjir", "bro", "kemahalan", "digetok"
6. Kalo dari foto barang, estimasi harga second/barunya

FORMAT:
Hasil Terawangan 🔮
[List item + status harga + harga wajar]

Analisis Dukun
[Kenapa mahal/wajar + konteks lokasi]

Jurus Protes
[Script buat nego/protes ke penjual]

JANGAN KASIH LINK PRODUK KECUALI USER MINTA."""
    else:
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
    models = [ss.selected_model, "groq" if ss.selected_model == "gemini" else "gemini"]; result = None
    for try_model in models:
        try:
            if try_model == "gemini":
                toast("Pake Gemini...", "✨"); content = [full_p]
                if image: content.append(image)
                res = gemini_model.generate_content(content, stream=True)
                full_text = "".join([c.text for c in res if c.text])
            else:
                toast("Pake Groq...", "⚡")
                chat = groq_client.chat.completions.create(messages=[{"role": "user", "content": full_p}], model="llama-3.3-70b-versatile", stream=True)
                full_text = "".join([c.choices[0].delta.content for c in chat if c.choices[0].delta.content])
            if full_text: result = [("text", full_text, tingkat, try_model)]; break
        except Exception as e:
            err = str(e)
            if "401" in err: toast("API Key salah/expired", "❌")
            elif "429" in err: toast("Limit abis, coba model lain...", "⚠️")
            elif "quota" in err.lower(): toast("Quota abis", "⚠️")
            if try_model == models[-1]: result = [("text", f"Error: {err[:80]}. Cek API Key di Secrets.", "ngobrol")]
    loading_placeholder.empty()
    return result if result else [("text", "Error gak dikenal bro.", "ngobrol")]

with st.sidebar:
    st.markdown("### ⚙️ Manage Falio")
    m = st.selectbox("Pilih Model AI", ["Gemini 2.5 Flash", "Llama 3.3 70B Groq"], index=0 if ss.selected_model == "gemini" else 1)
    ss.selected_model = "gemini" if m == "Gemini 2.5 Flash" else "groq"
    st.markdown("---")
    st.markdown("### 🎭 Pilih Mode")
    if st.button("💬 Mode Normal", use_container_width=True): ss.mode = "normal"; st.rerun()
    if st.button("🔥 Mode Ngobrolin Aib", use_container_width=True): ss.mode = "aib"; st.rerun()
    if st.button("🔧 Dokter Gadget", use_container_width=True): ss.mode = "dokter"; st.rerun()
    if st.button("💸 Dukun Harga", use_container_width=True): ss.mode = "dukun"; st.rerun()
    st.markdown("---")
    if st.button("🗑️ Hapus Semua Chat"): ss.messages = []; ss.aib_chats = []; ss.chat_count = 0; st.rerun()
    if ss.mode == "aib" and st.button("🔥 Bakar Chat Aib", use_container_width=True): ss.aib_chats = []; ss.messages = [m for m in ss.messages if m.get("mode")!= "aib"]; st.rerun()
    st.metric("Chat Tersisa", f"{MAX_CHAT - ss.chat_count}/{MAX_CHAT}")

if not ss.messages and ss.mode == "normal":
    st.markdown('<div class="meta-opening"><div class="meta-title">Ada yang bisa<br>Falio bantu?</div><button class="meta-btn"><span class="meta-btn-icon">🖼️</span> Buat gambar</button><button class="meta-btn"><span class="meta-btn-icon">💡</span> Bantu selesaikan masalah</button><button class="meta-btn"><span class="meta-btn-icon">🎓</span> Belajar dan berkembang</button></div>', unsafe_allow_html=True)

if ss.mode == "aib":
    msgs = ss.aib_chats
    st.info("🔥 Mode Aib Aktif - Chat ilang otomatis setelah 24 jam. Aman bro.", icon="🔒")
else:
    msgs = ss.messages

if MAX_CHAT - ss.chat_count == 3: st.toast("Sesi ngobrol hampir habis", icon="⚠️")

for i, msg in enumerate(msgs):
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            bc = msg.get("tingkat", "ngobrol")
            bt = {"image": "🎨 GAMBAR", "remix": "✨ REMIX", "ngobrol": "💬 NGOBROL", "problem_solver": "💡 SOLUSI"}.get(bc, "💬")
            model = "Gemini" if msg.get("model") == "gemini" else "Groq"
            badge_mode = {"aib": '<div class="orion-badge danger-badge">🔥 MODE AIB</div>', "dokter": '<div class="orion-badge">🔧 DOKTER GADGET</div>', "dukun": '<div class="orion-badge">💸 DUKUN HARGA</div>'}.get(msg.get("mode"), "")
            st.markdown(f'{badge_mode}<div class="orion-badge {bc}">{bt}</div><div class="orion-badge model-badge">{model}</div>', unsafe_allow_html=True)
        if msg["type"] == "image":
            st.image(msg["content"], use_container_width=True)
            st.download_button("📥 Unduh", image_to_bytes(msg["content"]), f"falio_{i}.png", "image/png", key=f"dl_{i}", use_container_width=True)
        else:
            st.markdown(msg["content"], unsafe_allow_html=True)

if len(msgs) > 3:
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
            user_msg = {"role": "user", "type": "text", "content": voice_text, "mode": ss.mode}
            if ss.mode 
