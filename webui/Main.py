import io
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
import imageio_ffmpeg

st.set_page_config(page_title="Gerador de Vídeos", page_icon="🎬", layout="wide")

st.title("🎬 Gerador de vídeos curtos")
st.write("Crie vídeos verticais em lote com narração, texto na tela e fundos personalizados.")

st.info("Dica: envie imagens ou vídeos de fundo que você tenha direito de usar. A narração por texto usa conexão com a internet.")

def load_font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = (current + " " + word).strip()
        if draw.textbbox((0, 0), trial, font=font)[2] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

def make_card(text, template, title, duration_hint=30):
    W, H = 1080, 1920
    card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    title_font = load_font(76, True)
    body_font = load_font(54, True)
    if template == "Notícia":
        box = (70, 570, 1010, 1390)
        fill = (0, 0, 0, 190)
        accent = (255, 205, 45, 255)
    elif template == "Minimalista":
        box = (65, 650, 1015, 1320)
        fill = (10, 10, 10, 165)
        accent = (255, 255, 255, 255)
    elif template == "Destaque":
        box = (55, 520, 1025, 1420)
        fill = (95, 20, 130, 205)
        accent = (255, 225, 70, 255)
    else:
        box = (65, 590, 1015, 1370)
        fill = (0, 0, 0, 180)
        accent = (80, 220, 180, 255)
    d.rounded_rectangle(box, radius=42, fill=fill, outline=accent, width=5)
    x, y = box[0] + 55, box[1] + 45
    if title.strip():
        for line in wrap_text(d, title.strip(), title_font, box[2]-box[0]-110)[:2]:
            d.text((x, y), line, font=title_font, fill=accent, stroke_width=1, stroke_fill=(0,0,0,255))
            y += 95
        y += 22
    available = box[3] - y - 35
    lines = wrap_text(d, text, body_font, box[2]-box[0]-110)
    line_h = 68
    max_lines = max(1, int(available / line_h))
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        if lines:
            lines[-1] = lines[-1].rstrip(".,!?") + "…"
    for line in lines:
        d.text((x, y), line, font=body_font, fill=(255,255,255,255), stroke_width=2, stroke_fill=(0,0,0,255))
        y += line_h
    footer = "VÍDEO CURTO"
    d.text((75, 1790), footer, font=load_font(30, True), fill=(255,255,255,220))
    return card

def create_video(script, title, bg_file, template, voice, language, output_path):
    work = tempfile.mkdtemp(prefix="video_")
    try:
        bg_path = os.path.join(work, "background")
        with open(bg_path, "wb") as f:
            f.write(bg_file)
        # Imagens são convertidas para o formato vertical; vídeos enviados também são aceitos.
        ext = Path(getattr(bg_file, "name", "background.jpg")).suffix.lower()
        if ext not in [".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mov", ".m4v"]:
            ext = ".jpg"
        bg_path = bg_path + ext
        os.replace(os.path.join(work, "background"), bg_path)

        audio_path = os.path.join(work, "voice.mp3")
        if voice is not None:
            with open(audio_path, "wb") as f:
                f.write(voice)
        else:
            gTTS(text=script, lang=language, slow=False).save(audio_path)

        # Duração real do áudio
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        probe = subprocess.run([ffmpeg, "-i", audio_path], capture_output=True, text=True)
        m = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", probe.stderr)
        duration = 20.0
        if m:
            duration = int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3))
        duration = max(5, duration + 1.0)

        overlay = make_card(script, template, title)
        overlay_path = os.path.join(work, "overlay.png")
        overlay.save(overlay_path)

        is_video = ext in [".mp4", ".mov", ".m4v"]
        if is_video:
            bg_input = ["-stream_loop", "-1", "-i", bg_path]
            video_filter = "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[bg];[bg][2:v]overlay=0:0[v]"
        else:
            bg_input = ["-loop", "1", "-framerate", "30", "-i", bg_path]
            video_filter = "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[bg];[bg][2:v]overlay=0:0[v]"
        cmd = [ffmpeg, "-y"] + bg_input + ["-i", audio_path, "-i", overlay_path,
              "-filter_complex", video_filter, "-map", "[v]", "-map", "1:a",
              "-t", str(duration), "-r", "30", "-c:v", "libx264", "-preset", "veryfast",
              "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", output_path]
        run = subprocess.run(cmd, capture_output=True, text=True)
        if run.returncode != 0:
            raise RuntimeError(run.stderr[-1800:])
    finally:
        shutil.rmtree(work, ignore_errors=True)

with st.sidebar:
    st.header("Configurações")
    template = st.selectbox("Modelo visual", ["Moderno", "Notícia", "Minimalista", "Destaque"])
    language = st.selectbox("Idioma da narração", ["Português", "English", "Español"])
    lang_code = {"Português":"pt", "English":"en", "Español":"es"}[language]
    st.caption("A voz é gerada online pelo Google Text-to-Speech (gTTS).")

scripts_text = st.text_area(
    "Roteiros (separe cada vídeo com uma linha contendo apenas ---)",
    height=220,
    placeholder="Título do primeiro vídeo\nEscreva aqui o texto da narração...\n---\nTítulo do segundo vídeo\nEscreva outro roteiro..."
)
backgrounds = st.file_uploader("Fundos (imagens)", type=["jpg","jpeg","png","webp"], accept_multiple_files=True)
voice_upload = st.file_uploader("Áudio de narração opcional (um áudio para todos os vídeos)", type=["mp3","wav","m4a"])
st.caption("Se não enviar áudio, o programa cria uma narração a partir do texto.")

if st.button("🚀 Gerar vídeos", type="primary", use_container_width=True):
    chunks = [x.strip() for x in scripts_text.split("\n---\n") if x.strip()]
    if not chunks:
        st.error("Digite pelo menos um roteiro.")
    elif not backgrounds:
        st.error("Envie pelo menos uma imagem ou vídeo de fundo.")
    else:
        results = []
        progress = st.progress(0)
        status = st.empty()
        for i, chunk in enumerate(chunks):
            lines = chunk.splitlines()
            title = lines[0][:90] if len(lines) > 1 else f"Vídeo {i+1}"
            script = " ".join(lines[1:] if len(lines) > 1 else lines).strip()
            if not script:
                script = title
                title = f"Vídeo {i+1}"
            bg = backgrounds[i % len(backgrounds)]
            out = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{i+1}.mp4")
            out.close()
            try:
                status.write(f"Gerando vídeo {i+1} de {len(chunks)}…")
                create_video(script, title, bg.getvalue(), template,
                             voice_upload.getvalue() if voice_upload else None,
                             lang_code, out.name)
                results.append((f"video_{i+1:02d}.mp4", out.name))
            except Exception as e:
                st.error(f"Falha no vídeo {i+1}: {e}")
                try: os.unlink(out.name)
                except OSError: pass
            progress.progress((i+1)/len(chunks))
        if results:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as z:
                for name, path in results:
                    z.write(path, name)
            st.success(f"{len(results)} vídeo(s) gerado(s)!")
            st.download_button("⬇️ Baixar todos os vídeos (.ZIP)", zip_buffer.getvalue(),
                               file_name="meus_videos.zip", mime="application/zip",
                               use_container_width=True)
            for name, path in results:
                with open(path, "rb") as f:
                    st.download_button(f"Baixar {name}", f.read(), file_name=name, mime="video/mp4")
                os.unlink(path)
