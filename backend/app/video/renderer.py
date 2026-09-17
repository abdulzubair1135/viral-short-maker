import os
from pathlib import Path
from typing import Dict, Any, Optional
from backend.app.video.ffmpeg_wrapper import ffmpeg
from backend.app.video.reframing import SmartReframer
from backend.app.video.captions import CaptionEngine
from backend.app.video.audio import AudioEngine
from backend.app.video.effects import EffectsEngine
from backend.app.core.logging import logger

def escape_ffmpeg_path(path: Path) -> str:
    """Escapes Windows path for FFmpeg filter arguments."""
    p_str = str(path.resolve()).replace("\\", "/")
    # Escape colon for ffmpeg filter parsing (C: -> C\:)
    if len(p_str) > 1 and p_str[1] == ":":
        p_str = p_str[0] + "\\:" + p_str[2:]
    return p_str

class VideoRenderer:
    def __init__(self):
        self.reframer = SmartReframer(target_width=1080, target_height=1920)

    def render_clip(
        self,
        source_video_path: str,
        clip_data: Dict[str, Any],
        transcript_data: Dict[str, Any],
        output_mp4: Path,
        work_dir: Path,
        commentary_audio_path: Optional[str] = None
    ) -> Path:
        """
        Transformative Review short pipeline render:
        1. Boundary trimming
        2. 9:16 smart reframing (speaker tracking or background blur)
        3. ASS caption burn-in
        4. Commentary voiceover narration mixing & ducking
        5. Visual transformative review badges & verdict/rating card
        6. Universal audio normalization (-ar 44100 -ac 2)
        7. Export to 1080x1920 H.264/AAC MP4
        """
        output_mp4.parent.mkdir(parents=True, exist_ok=True)
        work_dir.mkdir(parents=True, exist_ok=True)

        start = clip_data["start_time"]
        end = clip_data["end_time"]
        duration = end - start
        crop_mode = clip_data.get("crop_mode", "speaker_tracking")
        caption_preset = clip_data.get("caption_preset", "dynamic")

        # Step 1: Generate ASS Subtitle file
        ass_path = work_dir / f"captions_{start}_{end}.ass"
        CaptionEngine.generate_ass_subtitle_file(
            segments=transcript_data.get("segments", []),
            clip_start=start,
            clip_end=end,
            output_file=ass_path,
            preset_name=caption_preset
        )

        # Step 2: Detect faces for smart reframing
        source_meta = ffmpeg.probe(source_video_path)
        subject_centers = []
        if crop_mode == "speaker_tracking":
            subject_centers = self.reframer.detect_subject_centers(
                source_video_path,
                start_time=start,
                end_time=end,
                sample_fps=1.5
            )

        # Step 3: Build video filter complex
        v_crop = self.reframer.build_crop_filter(
            source_width=source_meta.get("width", 1920),
            source_height=source_meta.get("height", 1080),
            subject_centers=subject_centers,
            crop_mode=crop_mode
        )

        escaped_ass = escape_ffmpeg_path(ass_path)
        progress_bar = EffectsEngine.build_progress_bar_filter(duration)

        # Build transformative review overlays
        font_path = "C\\:/Windows/Fonts/arial.ttf"
        rating_val = float(clip_data.get("rating", 8.5) or 8.5)
        verdict_text = str(clip_data.get("verdict", "MUST WATCH") or "MUST WATCH").replace("'", "").replace(":", " ")[:26].upper()
        card_start = max(0.5, duration - 3.5)

        overlay_chain = (
            f"drawtext=fontfile='{font_path}':text='CRITIQUE & ANALYSIS':fontcolor=white:fontsize=32:box=1:boxcolor=black@0.7:boxborderw=10:x=(w-text_w)/2:y=120,"
            f"drawtext=fontfile='{font_path}':text='Fair Use Review | Commentary':fontcolor=white@0.8:fontsize=20:x=(w-text_w)/2:y=175,"
            f"drawbox=x=80:y=ih-460:w=iw-160:h=210:color=black@0.88:t=fill:enable='gte(t,{card_start:.1f})',"
            f"drawtext=fontfile='{font_path}':text='VERDICT\\: {verdict_text}':fontcolor=yellow:fontsize=34:x=(w-text_w)/2:y=h-420:enable='gte(t,{card_start:.1f})',"
            f"drawtext=fontfile='{font_path}':text='RATING\\: {rating_val:.1f}/10':fontcolor=white:fontsize=44:x=(w-text_w)/2:y=h-350:enable='gte(t,{card_start:.1f})'"
        )

        has_commentary = bool(commentary_audio_path and Path(commentary_audio_path).exists())

        # Combine video filter chain
        if crop_mode == "blur_background":
            video_filter = f"{v_crop}[v_over];[v_over]ass='{escaped_ass}',{progress_bar},{overlay_chain}[v_final]"
        else:
            video_filter = f"{v_crop},ass='{escaped_ass}',{progress_bar},{overlay_chain}[v_final]"

        # Step 4: Audio filter with ducking if narration exists
        if has_commentary:
            audio_filter = "[0:a]volume=0.35,loudnorm=I=-16:TP=-1.5:LRA=11[bg];[1:a]volume=1.25[comm];[bg][comm]amix=inputs=2:duration=first:dropout_transition=2[a_final]"
        else:
            audio_filter = AudioEngine.build_audio_filter(normalize_loudness=True, voice_gain_db=2.0)

        # Step 5: Execute FFmpeg render
        args = [
            "-y",
            "-ss", str(start),
            "-to", str(end),
            "-i", str(source_video_path),
        ]

        if has_commentary:
            args += ["-i", str(commentary_audio_path)]
            args += ["-filter_complex", f"{video_filter};{audio_filter}", "-map", "[v_final]", "-map", "[a_final]"]
        elif crop_mode == "blur_background":
            args += ["-filter_complex", video_filter, "-map", "[v_final]", "-map", "0:a", "-af", audio_filter]
        else:
            args += ["-filter_complex", video_filter, "-map", "[v_final]", "-map", "0:a", "-af", audio_filter]

        args += [
            "-c:v", "libx264",
            "-preset", "faster",
            "-crf", "18",
            "-c:a", "aac",
            "-b:a", "320k",
            "-ar", "44100",
            "-ac", "2",
            "-r", "30",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(output_mp4)
        ]

        logger.info(f"Rendering transformative review Short [{start:.1f}s - {end:.1f}s] to {output_mp4} (Narration: {has_commentary})")
        try:
            ffmpeg.run_command(args, timeout=300)
        except Exception as e:
            # Fallback without ASS or complex overlays if filter chain encounters edge-case codec error
            logger.warning(f"Render with full filters failed ({e}), attempting resilient fallback render...")
            fallback_vf = v_crop.split(";")[0] if crop_mode == "blur_background" else v_crop
            fallback_args = [
                "-y",
                "-ss", str(start),
                "-to", str(end),
                "-i", str(source_video_path),
                "-vf", fallback_vf,
                "-af", AudioEngine.build_audio_filter(normalize_loudness=True),
                "-c:v", "libx264",
                "-preset", "faster",
                "-crf", "18",
                "-c:a", "aac",
                "-b:a", "320k",
                "-ar", "44100",
                "-ac", "2",
                "-r", "30",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                str(output_mp4)
            ]
            ffmpeg.run_command(fallback_args, timeout=300)

        return output_mp4

