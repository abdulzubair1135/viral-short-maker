from pathlib import Path
from typing import Optional
from backend.app.core.logging import logger

class AudioEngine:
    @staticmethod
    def build_audio_filter(
        normalize_loudness: bool = True,
        voice_gain_db: float = 2.0,
        background_music_path: Optional[str] = None,
        music_volume: float = 0.15,
        ducking: bool = True
    ) -> str:
        """
        Builds FFmpeg audio filter string for voice normalization and background music mixing.
        """
        filters = []
        if voice_gain_db != 0.0:
            filters.append(f"volume={voice_gain_db}dB")

        if normalize_loudness:
            # EBU R128 loudness normalization
            filters.append("loudnorm=I=-16:TP=-1.5:LRA=11")

        voice_chain = ",".join(filters) if filters else "anull"

        if background_music_path and Path(background_music_path).exists():
            # Ducking: sidechain compress music when voice speaks
            if ducking:
                return (
                    f"[0:a]{voice_chain}[v_norm];"
                    f"[1:a]volume={music_volume}[m_vol];"
                    f"[m_vol][v_norm]sidechaincompress=threshold=0.1:ratio=5:attack=50:release=300[ducked_bg];"
                    f"[v_norm][ducked_bg]amix=inputs=2:duration=first:dropout_transition=2[a_out]"
                )
            else:
                return (
                    f"[0:a]{voice_chain}[v_norm];"
                    f"[1:a]volume={music_volume}[m_vol];"
                    f"[v_norm][m_vol]amix=inputs=2:duration=first[a_out]"
                )

        return voice_chain
