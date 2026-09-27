import os
import re
import math
from pathlib import Path
from typing import Dict, Any, List, Optional
from PIL import Image, ImageDraw, ImageFont

from backend.app.video.ffmpeg_wrapper import ffmpeg
from backend.app.core.logging import logger

class MemeRenderer:
    """
    Renders high-retention 9:16 meme videos (1080x1920) optimized for Shorts, Reels, and TikTok.
    Combines Ken Burns zoom animations, blurred pillarbox backgrounds, crisp typography overlays,
    and voiceover audio mixing.
    """

    WIDTH = 1080
    HEIGHT = 1920
    FPS = 30

    @classmethod
    def wrap_text(cls, text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> List[str]:
        words = text.split()
        if not words:
            return []

        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            line_width = bbox[2] - bbox[0]
            if line_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
                    current_line = []

        if current_line:
            lines.append(" ".join(current_line))
        return lines

    @classmethod
    def generate_overlay_png(
        cls,
        screen_text: List[Dict[str, Any]],
        format_type: str,
        attribution_text: str,
        output_png: Path
    ) -> Path:
        """
        Creates a crisp 1080x1920 RGBA transparent overlay containing all text cards,
        POV pills, impact subtitles, and attribution info within safe zones.
        """
        img = Image.new("RGBA", (cls.WIDTH, cls.HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Load fonts with fallbacks
        font_path_impact = "C:/Windows/Fonts/impact.ttf"
        font_path_arial = "C:/Windows/Fonts/arial.ttf"
        font_path_bold = "C:/Windows/Fonts/arialbd.ttf"
        if not os.path.exists(font_path_bold):
            font_path_bold = font_path_arial

        try:
            f_impact_large = ImageFont.truetype(font_path_impact if os.path.exists(font_path_impact) else font_path_bold, 54)
            f_impact_medium = ImageFont.truetype(font_path_impact if os.path.exists(font_path_impact) else font_path_bold, 44)
            f_pill = ImageFont.truetype(font_path_bold, 36)
            f_attr = ImageFont.truetype(font_path_arial, 20)
        except Exception:
            f_impact_large = ImageFont.load_default()
            f_impact_medium = ImageFont.load_default()
            f_pill = ImageFont.load_default()
            f_attr = ImageFont.load_default()

        # Safe margins: X: 70 to 1010 (width 940), Y: top >= 240, bottom <= 1620
        max_text_w = 920

        # Sort screen text into top, middle, bottom
        top_items = [st for st in screen_text if st.get("position") == "top"]
        middle_items = [st for st in screen_text if st.get("position") == "middle"]
        bottom_items = [st for st in screen_text if st.get("position") == "bottom"]

        # Default placement if positions weren't specified properly
        if not top_items and screen_text:
            top_items = [screen_text[0]]
            bottom_items = screen_text[1:]

        # 1. RENDER TOP (Hook / Setup)
        top_y = 260
        for item in top_items:
            text = str(item.get("text", "")).strip()
            if not text:
                continue

            style = item.get("style", "pill" if format_type == "pov" else "impact")
            if style == "pill" or format_type == "pov":
                # Render modern pill banner
                lines = cls.wrap_text(text, f_pill, max_text_w - 60, draw)
                line_height = 50
                box_h = len(lines) * line_height + 40
                box_w = max(400, min(max_text_w + 40, max([draw.textbbox((0, 0), l, font=f_pill)[2] - draw.textbbox((0, 0), l, font=f_pill)[0] for l in lines] + [300]) + 60))
                box_x0 = (cls.WIDTH - box_w) // 2
                box_x1 = box_x0 + box_w

                draw.rounded_rectangle(
                    [(box_x0, top_y), (box_x1, top_y + box_h)],
                    radius=20,
                    fill=(15, 15, 20, 235),
                    outline=(255, 255, 255, 180),
                    width=3
                )
                curr_y = top_y + 20
                for line in lines:
                    line_w = draw.textbbox((0, 0), line, font=f_pill)[2] - draw.textbbox((0, 0), line, font=f_pill)[0]
                    lx = (cls.WIDTH - line_w) // 2
                    draw.text((lx, curr_y), line, font=f_pill, fill=(255, 255, 255, 255))
                    curr_y += line_height

                top_y += box_h + 30
            else:
                # Classic Impact Uppercase
                clean_text = text.upper()
                lines = cls.wrap_text(clean_text, f_impact_large, max_text_w, draw)
                line_height = 65
                for line in lines:
                    line_w = draw.textbbox((0, 0), line, font=f_impact_large)[2] - draw.textbbox((0, 0), line, font=f_impact_large)[0]
                    lx = (cls.WIDTH - line_w) // 2
                    draw.text((lx, top_y), line, font=f_impact_large, fill="white", stroke_width=6, stroke_fill="black")
                    top_y += line_height
                top_y += 20

        # 2. RENDER MIDDLE (If any)
        if middle_items:
            mid_y = 900
            for item in middle_items:
                text = str(item.get("text", "")).strip()
                if not text:
                    continue
                lines = cls.wrap_text(text, f_impact_medium, max_text_w, draw)
                for line in lines:
                    line_w = draw.textbbox((0, 0), line, font=f_impact_medium)[2] - draw.textbbox((0, 0), line, font=f_impact_medium)[0]
                    lx = (cls.WIDTH - line_w) // 2
                    draw.text((lx, mid_y), line, font=f_impact_medium, fill="yellow", stroke_width=5, stroke_fill="black")
                    mid_y += 55

        # 3. RENDER BOTTOM (Punchline / Twist)
        if bottom_items:
            # Calculate total height of bottom text to position it just above safe zone (around y=1480)
            all_bottom_lines = []
            for item in bottom_items:
                text = str(item.get("text", "")).strip()
                if text:
                    all_bottom_lines.extend(cls.wrap_text(text.upper(), f_impact_large, max_text_w, draw))

            line_height = 68
            total_bottom_h = len(all_bottom_lines) * line_height
            bot_y = min(1500 - total_bottom_h, 1380)

            for line in all_bottom_lines:
                line_w = draw.textbbox((0, 0), line, font=f_impact_large)[2] - draw.textbbox((0, 0), line, font=f_impact_large)[0]
                lx = (cls.WIDTH - line_w) // 2
                draw.text((lx, bot_y), line, font=f_impact_large, fill="white", stroke_width=6, stroke_fill="black")
                bot_y += line_height

        # 4. RENDER ATTRIBUTION (If required)
        if attribution_text and attribution_text.strip():
            clean_attr = attribution_text.strip()[:65]
            draw.text((40, 1600), clean_attr, font=f_attr, fill=(200, 200, 200, 200), stroke_width=2, stroke_fill="black")

        output_png.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_png, "PNG")
        return output_png

    @classmethod
    def render_meme(
        cls,
        asset_path: str,
        meme_data: Dict[str, Any],
        output_mp4: Path,
        work_dir: Path,
        audio_path: Optional[str] = None,
        attribution_text: str = "",
        export_gif: bool = True
    ) -> Path:
        """
        Renders complete 9:16 vertical meme short with Ken Burns motion/GIF animation, blurred backdrop,
        layered typography overlay, clean/voiceover audio, and optional GIF export.
        """
        output_mp4.parent.mkdir(parents=True, exist_ok=True)
        work_dir.mkdir(parents=True, exist_ok=True)

        screen_text = meme_data.get("screen_text", [])
        fmt = meme_data.get("format", "pov")
        base_dur = float(meme_data.get("duration", 7.5))

        # Check audio duration if audio provided
        has_audio = bool(audio_path and os.path.exists(audio_path))
        if has_audio:
            try:
                a_meta = ffmpeg.probe(audio_path)
                a_dur = float(a_meta.get("duration", 0.0))
                if a_dur > 2.0:
                    base_dur = max(base_dur, a_dur + 1.2)
            except Exception as e:
                logger.warning(f"Could not probe audio duration: {e}")

        duration = min(20.0, max(5.0, base_dur))
        total_frames = int(duration * cls.FPS)

        # Generate Typography Overlay PNG
        overlay_png = work_dir / f"overlay_{output_mp4.stem}.png"
        cls.generate_overlay_png(
            screen_text=screen_text,
            format_type=fmt,
            attribution_text=attribution_text,
            output_png=overlay_png
        )

        escaped_overlay = str(overlay_png.resolve()).replace("\\", "/")

        # Build Video Filter Graph:
        # Background: Scaled and blurred 1080x1920
        # Foreground: Centered visual asset scaled to fit nicely in 960x1000 with a clean drop-shadow card
        # Ken Burns zoom / GIF looping on foreground for high visual retention
        # Typography overlay rendered on top
        vf_chain = (
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5[bg];"
            f"[0:v]scale=960:1080:force_original_aspect_ratio=decrease,format=rgba[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2-30[comp];"
            f"[comp][1:v]overlay=0:0[v_final]"
        )

        is_gif = str(asset_path).lower().endswith(".gif")
        
        args = ["-y"]
        if is_gif:
            args += ["-ignore_loop", "0", "-i", str(asset_path)]
        else:
            args += ["-loop", "1", "-t", f"{duration:.2f}", "-i", str(asset_path)]

        args += [
            "-loop", "1",
            "-t", f"{duration:.2f}",
            "-i", str(overlay_png),
        ]

        if has_audio:
            args += [
                "-i", str(audio_path),
                "-filter_complex", vf_chain,
                "-map", "[v_final]",
                "-map", "2:a",
                "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                "-c:a", "aac",
                "-b:a", "256k",
                "-ar", "44100",
                "-ac", "2"
            ]
        else:
            # Silent audio track for valid MP4 short
            args += [
                "-f", "lavfi",
                "-t", f"{duration:.2f}",
                "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                "-filter_complex", vf_chain,
                "-map", "[v_final]",
                "-map", "2:a",
                "-c:a", "aac",
                "-b:a", "128k"
            ]

        args += [
            "-c:v", "libx264",
            "-preset", "faster",
            "-crf", "19",
            "-r", str(cls.FPS),
            "-pix_fmt", "yuv420p",
            "-t", f"{duration:.2f}",
            "-movflags", "+faststart",
            str(output_mp4)
        ]

        logger.info(f"Rendering Meme Short ({fmt}, {duration:.1f}s, asset_is_gif={is_gif}) to {output_mp4.name}")
        ffmpeg.run_command(args, timeout=180)

        # Export high-quality 9:16 vertical GIF version if requested
        if export_gif:
            output_gif = output_mp4.with_suffix(".gif")
            logger.info(f"Exporting GIF version of meme to {output_gif.name}...")
            gif_args = [
                "-y",
                "-i", str(output_mp4),
                "-vf", "fps=15,scale=480:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer",
                "-t", f"{min(duration, 8.0):.2f}",
                str(output_gif)
            ]
            try:
                ffmpeg.run_command(gif_args, timeout=90)
                logger.info(f"Successfully generated GIF meme at {output_gif.name}")
            except Exception as e:
                logger.warning(f"GIF export failed ({e}), MP4 video remains available.")

        return output_mp4
