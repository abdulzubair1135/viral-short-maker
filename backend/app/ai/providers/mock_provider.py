import json
import asyncio
from typing import Dict, Any, Optional
from backend.app.ai.base_provider import AIProvider
from backend.app.ai.validators import validate_structured_ai_response

class MockBrowserProvider(AIProvider):
    @property
    def name(self) -> str:
        return "mock"

    async def health_check(self) -> Dict[str, Any]:
        return {
            "provider": "mock",
            "ready": True,
            "status": "Ready (Deterministic offline mode)",
            "requires_human_intervention": False
        }

    async def analyze(self, transcript_text: str, duration: float, prompt_override: Optional[str] = None, title: str = "Viral Video", video_url: str = "") -> str:
        """Simulates browser-based AI moment selection with structured source analysis and quality shorts."""
        await asyncio.sleep(0.3)

        dur = max(duration, 25.0)

        # AI dynamically evaluates how many strong moments exist
        # E.g. for a short video, 2 strong moments; for longer video, 3-4 strong moments
        c1_start = round(min(2.0, dur * 0.08), 1)
        c1_end = round(min(c1_start + 22.0, dur - 0.5), 1)

        c2_start = round(min(c1_end + 1.0, dur * 0.5), 1)
        c2_end = round(min(c2_start + 20.0, dur), 1)

        shorts = [
            {
                "id": "review_01",
                "start_time": c1_start,
                "end_time": c1_end,
                "duration": round(c1_end - c1_start, 1),
                "score": 95,
                "hook_score": 97,
                "interest_score": 94,
                "commentary_potential": 96,
                "standalone_score": 95,
                "clarity_score": 96,
                "context_score": 91,
                "originality_potential": 95,
                "overall_score": 95,
                "reason": "Intriguing open loop in the first 3 seconds followed by a concrete, actionable takeaway.",
                "hook": "Here is an incredible secret you probably never knew before.",
                "title": "The Incredible Secret Nobody Talks About",
                "description": "Discover the counterintuitive method that completely changes how you approach this challenge.",
                "hashtags": ["#shorts", "#review", "#breakdown", "#strategy"],
                "keywords": ["secret", "analysis", "review"],
                "analysis": {
                    "claim_or_event": "Host reveals a unique counterintuitive technique.",
                    "fact_or_opinion": "fact",
                    "commentary": "Analyzing why this approach bypasses the usual friction points.",
                    "context": "Historically, conventional methods took twice as long.",
                    "counterpoint": "Requires strict discipline or it backfires completely.",
                    "verdict": "Brilliant strategy with masterclass execution.",
                    "rating": 9.2,
                    "rating_label": "GENIUS"
                },
                "narration_script": [
                    {"segment": "hook", "text": "Is this genuinely the smartest approach out there?"},
                    {"segment": "commentary", "text": "Notice how they completely skip the standard bottleneck."},
                    {"segment": "verdict", "text": "Final verdict: Exceptional efficiency. Rating: 9.2 out of 10."}
                ],
                "source_attribution": "Original footage analyzed for educational critique",
                "caption_style": "dynamic",
                "priority": 1
            }
        ]

        if dur >= 20.0 and c2_end > c2_start + 5.0:
            shorts.append({
                "id": "review_02",
                "start_time": c2_start,
                "end_time": c2_end,
                "duration": round(c2_end - c2_start, 1),
                "score": 91,
                "hook_score": 93,
                "interest_score": 91,
                "commentary_potential": 92,
                "standalone_score": 92,
                "clarity_score": 94,
                "context_score": 88,
                "originality_potential": 90,
                "overall_score": 91,
                "reason": "High retention explanation with seamless visual and speech coherence.",
                "hook": "This single change can literally 10x your output overnight.",
                "title": "How to 10x Your Productivity Overnight",
                "description": "A step-by-step breakdown of the single habit that yields 10x output with zero extra effort.",
                "hashtags": ["#shorts", "#review", "#lifehacks", "#productivity"],
                "keywords": ["habits", "success", "work"],
                "analysis": {
                    "claim_or_event": "Presenter outlines the foundational leverage point.",
                    "fact_or_opinion": "opinion",
                    "commentary": "Evaluating whether this holds up under real-world pressure.",
                    "context": "Supported by cognitive behavioral habit formation studies.",
                    "counterpoint": "Diminishing returns kick in without proper baseline fundamentals.",
                    "verdict": "Highly practical advice, but requires sustained consistency.",
                    "rating": 8.7,
                    "rating_label": "HIGH VALUE"
                },
                "narration_script": [
                    {"segment": "hook", "text": "Does this productivity hack actually work in real life?"},
                    {"segment": "commentary", "text": "The psychological trigger here is where the real leverage is."},
                    {"segment": "verdict", "text": "Final verdict: Highly effective. Rating: 8.7 out of 10."}
                ],
                "source_attribution": "Original footage analyzed for educational commentary",
                "caption_style": "dynamic",
                "priority": 2
            })

        c3_start = round(min(c2_end + 1.0, dur * 0.75), 1)
        c3_end = round(min(c3_start + 18.0, dur), 1)
        if c3_end > c3_start + 5.0:
            shorts.append({
                "id": "review_03",
                "start_time": c3_start,
                "end_time": c3_end,
                "duration": round(c3_end - c3_start, 1),
                "score": 89,
                "hook_score": 91,
                "interest_score": 89,
                "commentary_potential": 90,
                "standalone_score": 89,
                "clarity_score": 92,
                "context_score": 85,
                "originality_potential": 88,
                "overall_score": 89,
                "reason": "Dramatic climactic moment with an intense challenge payoff.",
                "hook": "Watch what happens when the stakes are raised to the maximum.",
                "title": "When The Stakes Get Raised To The Maximum",
                "description": "Watch the intense climax and see if they can survive the final obstacle.",
                "hashtags": ["#shorts", "#review", "#challenge", "#analysis"],
                "keywords": ["challenge", "intense", "win"],
                "analysis": {
                    "claim_or_event": "Final obstacle sprint under ticking clock pressure.",
                    "fact_or_opinion": "fact",
                    "commentary": "Breaking down the exact risk calculus taken in the final seconds.",
                    "context": "Only a 2-second margin of error was allowed.",
                    "counterpoint": "Any minor misstep would have resulted in immediate elimination.",
                    "verdict": "Peak suspense with flawless dramatic pacing.",
                    "rating": 8.4,
                    "rating_label": "INTENSE"
                },
                "narration_script": [
                    {"segment": "hook", "text": "Could you survive this final obstacle with zero margin for error?"},
                    {"segment": "commentary", "text": "Look at the timing precision required right here."},
                    {"segment": "verdict", "text": "Final verdict: Masterful clutch moment. Rating: 8.4 out of 10."}
                ],
                "source_attribution": "Original footage analyzed for educational commentary",
                "caption_style": "dynamic",
                "priority": 3
            })

        rejected = [
            {
                "title": "Intro Greeting & Channel Intro",
                "start_time": 0.0,
                "end_time": 8.0,
                "duration": 8.0,
                "claim": "Creator introduces the premise and thanks sponsors",
                "scores": {
                    "hook_score": 52,
                    "interest_score": 48,
                    "commentary_potential": 35,
                    "standalone_score": 40,
                    "clarity_score": 88,
                    "context_score": 45,
                    "originality_potential": 30,
                    "overall_score": 48
                },
                "score_total": 48,
                "rejection_reason": "Low commentary potential; generic channel greeting without standalone payoff."
            }
        ]

        response_payload = {
            "source_analysis": {
                "overall_quality": 93,
                "summary": "Engaging content with high density of actionable insights and strong review moments.",
                "recommended_short_count": len(shorts)
            },
            "shorts": shorts,
            "rejected_candidates": rejected
        }

        return json.dumps(response_payload, indent=2)

    def validate_response(self, response_text: str) -> Dict[str, Any]:
        return validate_structured_ai_response(response_text, source_duration=3600.0)
