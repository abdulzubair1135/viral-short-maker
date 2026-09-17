import asyncio
import os
from pathlib import Path
from typing import Dict, Any, List, Union
from backend.app.core.logging import logger
from backend.app.video.ffmpeg_wrapper import ffmpeg

class NarrationEngine:
    DEFAULT_VOICE = "en-US-ChristopherNeural"
    FALLBACK_VOICE = "en-US-GuyNeural"

    @classmethod
    async def generate_commentary_audio(
        cls,
        script_data: Union[str, List[Dict[str, Any]]],
        output_path: Union[str, Path],
        voice: str = DEFAULT_VOICE,
        rate: str = "+0%",
        pitch: str = "+0Hz"
    ) -> Dict[str, Any]:
        """
        Synthesizes high-fidelity AI commentary voiceover using local Edge TTS
        with automated offline fallback to pyttsx3.
        Returns generated audio metadata including duration.
        """
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # 1. Compile full text from script
        if isinstance(script_data, list):
            parts = []
            for item in script_data:
                if isinstance(item, dict):
                    txt = str(item.get("text", "")).strip()
                    if txt:
                        parts.append(txt)
                elif isinstance(item, str) and item.strip():
                    parts.append(item.strip())
            full_text = " ".join(parts).strip()
        else:
            full_text = str(script_data).strip()

        if not full_text:
            raise ValueError("No narration text provided for audio synthesis.")

        # 2. Try Edge TTS
        tts_success = False
        provider_used = "edge-tts"
        try:
            import edge_tts
            communicate = edge_tts.Communicate(full_text, voice=voice, rate=rate, pitch=pitch)
            await communicate.save(str(out_path))
            if out_path.exists() and out_path.stat().st_size > 1000:
                tts_success = True
                logger.info(f"Synthesized narration via Edge TTS ({voice}) to {out_path.name}")
        except Exception as e:
            logger.warning(f"Edge TTS synthesis failed ({e}), attempting pyttsx3 offline fallback...")

        # 3. Offline fallback using pyttsx3 if edge-tts failed
        if not tts_success:
            provider_used = "pyttsx3"
            try:
                import pyttsx3
                wav_path = out_path.with_suffix(".wav")
                engine = pyttsx3.init()
                engine.setProperty("rate", 175)
                engine.save_to_file(full_text, str(wav_path))
                engine.runAndWait()

                if wav_path.exists() and wav_path.stat().st_size > 1000:
                    ffmpeg.run_command([
                        "-y", "-i", str(wav_path),
                        "-c:a", "libmp3lame", "-b:a", "192k",
                        str(out_path)
                    ])
                    wav_path.unlink(missing_ok=True)
                    tts_success = True
                    logger.info(f"Synthesized narration via offline pyttsx3 to {out_path.name}")
            except Exception as e2:
                logger.error(f"pyttsx3 offline synthesis also failed: {e2}")

        if not tts_success or not out_path.exists():
            raise RuntimeError(f"Could not synthesize audio commentary for text: '{full_text[:60]}...'")

        # 4. Probe audio file to obtain exact duration
        meta = ffmpeg.probe(str(out_path))
        duration = float(meta.get("duration", 0.0))

        return {
            "audio_path": str(out_path),
            "duration": duration,
            "provider": provider_used,
            "voice": voice,
            "text": full_text,
            "is_ai_narrated": True
        }
