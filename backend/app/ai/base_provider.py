from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class AIProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier (gemini, chatgpt, deepseek, mock)."""
        pass

    @abstractmethod
    async def analyze(self, transcript_text: str, duration: float, prompt_override: Optional[str] = None, title: str = "Viral Video", video_url: str = "") -> str:
        """Submit transcript and prompt to the browser-based AI and return the raw output text."""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check browser readiness, session status, or human intervention requirement."""
        pass

    @abstractmethod
    def validate_response(self, response_text: str) -> Dict[str, Any]:
        """Validate and parse AI output into structured candidate list."""
        pass
