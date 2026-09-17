from pathlib import Path
from typing import Dict, Any, List

CAPTION_PRESETS = {
    "dynamic": {
        "font_name": "Arial Black",
        "font_size": 48,
        "primary_color": "&H00FFFFFF",  # Crisp White
        "secondary_color": "&H0000FFFF", # Electric Yellow
        "outline_color": "&H00000000",   # Bold Black outline
        "outline": 4,
        "shadow": 2,
        "alignment": 2,  # Bottom-center
        "margin_v": 360,  # Optimal Shorts safe zone
    },
    "minimal": {
        "font_name": "Arial",
        "font_size": 42,
        "primary_color": "&H00FFFFFF",
        "secondary_color": "&H00E0E0E0",
        "outline_color": "&H00000000",
        "outline": 3,
        "shadow": 1,
        "alignment": 2,
        "margin_v": 340,
    },
    "podcast": {
        "font_name": "Trebuchet MS",
        "font_size": 46,
        "primary_color": "&H00F0F0F0",
        "secondary_color": "&H0000E676", # Green highlight
        "outline_color": "&H00101010",
        "outline": 4,
        "shadow": 2,
        "alignment": 2,
        "margin_v": 360,
    },
    "gaming": {
        "font_name": "Impact",
        "font_size": 52,
        "primary_color": "&H0000FFFF",  # Bright Yellow
        "secondary_color": "&H000000FF", # Red highlight
        "outline_color": "&H00000000",
        "outline": 5,
        "shadow": 3,
        "alignment": 2,
        "margin_v": 380,
    },
    "cinematic": {
        "font_name": "Georgia",
        "font_size": 42,
        "primary_color": "&H00EEEEEE",
        "secondary_color": "&H00D4AF37", # Gold
        "outline_color": "&H00000000",
        "outline": 3,
        "shadow": 2,
        "alignment": 2,
        "margin_v": 340,
    },
    "clean": {
        "font_name": "Verdana",
        "font_size": 44,
        "primary_color": "&H00FFFFFF",
        "secondary_color": "&H00FF9800", # Orange
        "outline_color": "&H00202020",
        "outline": 4,
        "shadow": 1,
        "alignment": 2,
        "margin_v": 270,
    }
}

def format_ass_time(seconds: float) -> str:
    """Format seconds into ASS time format: H:MM:SS.cs"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1.0) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

class CaptionEngine:
    @staticmethod
    def generate_ass_subtitle_file(
        segments: List[Dict[str, Any]],
        clip_start: float,
        clip_end: float,
        output_file: Path,
        preset_name: str = "dynamic"
    ) -> Path:
        """
        Generates an Advanced SubStation Alpha (.ass) subtitle file.
        Times are shifted relative to clip_start.
        Applies preset styles and safe zones.
        """
        preset = CAPTION_PRESETS.get(preset_name, CAPTION_PRESETS["dynamic"])
        output_file.parent.mkdir(parents=True, exist_ok=True)

        header = f"""[Script Info]
Title: AI Repurposing Studio Captions
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{preset['font_name']},{preset['font_size']},{preset['primary_color']},{preset['secondary_color']},{preset['outline_color']},{preset['outline_color']},1,0,0,0,100,100,0,0,1,{preset['outline']},{preset['shadow']},{preset['alignment']},50,50,{preset['margin_v']},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        events = []
        for seg in segments:
            # Check overlap with clip
            if seg["end"] < clip_start or seg["start"] > clip_end:
                continue

            rel_start = max(0.0, seg["start"] - clip_start)
            rel_end = min(clip_end - clip_start, seg["end"] - clip_start)

            if rel_end <= rel_start:
                continue

            start_str = format_ass_time(rel_start)
            end_str = format_ass_time(rel_end)

            words = seg.get("words", [])
            if words and preset_name == "dynamic":
                # Build karaoke / word highlight tags
                text_parts = []
                for w in words:
                    w_rel_start = max(0.0, w["start"] - clip_start)
                    w_rel_end = min(clip_end - clip_start, w["end"] - clip_start)
                    dur_cs = max(int((w_rel_end - w_rel_start) * 100), 10)
                    text_parts.append(f"{{\\k{dur_cs}}}{w['word']}")
                caption_text = " ".join(text_parts)
            else:
                caption_text = seg["text"].strip().upper()

            events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{caption_text}")

        content = header + "\n".join(events) + "\n"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)

        return output_file
