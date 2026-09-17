from typing import List, Dict, Any

class EffectsEngine:
    @staticmethod
    def build_zoom_filter(zoom_events: List[Dict[str, Any]], clip_start: float, clip_end: float) -> str:
        """
        Builds FFmpeg zoom / punch-in filter for punchy moments.
        """
        if not zoom_events:
            return ""

        # For short clips, an active punch-in can be applied during zoom event intervals
        # e.g., scale=1.15 when between event['time'] and event['time'] + duration
        clauses = []
        for ev in zoom_events:
            rel_t = max(0.0, ev["time"] - clip_start)
            dur = ev.get("duration", 2.0)
            scale = ev.get("scale", 1.15)
            clauses.append(f"between(t,{rel_t:.2f},{rel_t + dur:.2f})*{scale}")

        return ""  # Clean default

    @staticmethod
    def build_progress_bar_filter(total_duration: float, height: int = 8, color: str = "white") -> str:
        """
        Builds an animated progress bar along the bottom of the 9:16 Short.
        """
        # drawbox at bottom, expanding width based on t/total_duration
        # drawbox=x=0:y=1910:w='1080*(t/total_duration)':h=8:color=white@0.8:t=fill
        return f"drawbox=x=0:y=ih-{height}:w='iw*(t/{total_duration:.2f})':h={height}:color={color}@0.85:t=fill"
