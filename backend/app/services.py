from dataclasses import dataclass
from typing import ClassVar
import hashlib
import json
import re
import httpx
from .config import get_settings

@dataclass
class Result:
    passed: bool
    reasons: list[str]
    score: float
    risk_level: str = "LOW"

class VariationGuard:
    def __init__(self, limit: float = 0.82): self.limit = limit
    def fp(self, text: str) -> set[str]:
        words = re.findall(r"[a-z0-9]+", text.lower())
        return {" ".join(words[i:i+5]) for i in range(max(0, len(words)-4))}
    def similarity(self, a: str, b: str) -> float:
        x, y = self.fp(a), self.fp(b)
        return len(x & y) / max(1, len(x | y))
    def allowed(self, candidate: str, previous: list[str]) -> bool:
        return all(self.similarity(candidate, old) < self.limit for old in previous)

class RightsRegistry:
    def cleared(self, assets: list[dict]) -> bool:
        return bool(assets) and all(a.get("cleared") is True and a.get("license") for a in assets)

class VideoBriefGenerator:
    async def generate(self, script:str, title:str, topic:str)->str:
        prompt=(
            "Create a production-ready video brief from this YouTube script. "
            "Return valid JSON only with keys: scenes (array of objects with scene_number, "
            "duration_seconds, visual, tone, narration_focus), target_duration_seconds, "
            "aspect_ratio (9:16 or 16:9), voice_and_pacing_notes. "
            "Do not write a new script or invent factual claims. "
            f"Title: {title}\nTopic: {topic}\nScript:\n{script}"
        )
        output=(await AIProvider.get().generate(prompt)).strip()
        if not output: raise RuntimeError("AI returned an empty video brief")
        try:
            parsed=json.loads(output)
        except json.JSONDecodeError as exc:
            raise RuntimeError("AI returned a non-JSON video brief") from exc
        required={"scenes","target_duration_seconds","aspect_ratio","voice_and_pacing_notes"}
        if not required.issubset(parsed) or not isinstance(parsed["scenes"],list):
            raise RuntimeError("AI video brief missing required structured fields")
        return json.dumps(parsed,ensure_ascii=False,indent=2)

class ReviewSuggestionEngine:
    SIGNALS: ClassVar[tuple[tuple[str, str], ...]] = (
        ("AI-generated visuals", "brief/script mentions AI-generated visuals"),
        ("synthetic", "brief/script mentions synthetic content"),
        ("realistic recreation", "brief/script mentions a realistic recreation"),
        ("deepfake-style", "brief/script mentions deepfake-style content"),
        ("voice clone", "brief/script mentions a voice clone"),
    )

    def suggest(self, text: str) -> tuple[bool, str]:
        lower = text.lower()
        reasons = [reason for signal, reason in self.SIGNALS if signal.lower() in lower]
        if not reasons:
            return False, "No known synthetic-content signal found in the script/brief text."
        return True, "; ".join(reasons)


class DisclosureTagger:
    def evaluate(self, realistic_synthetic=False, altered_real_person=False, altered_real_event=False,
                 generated_realistic_scene=False, production_assistance_only=False) -> dict:
        reasons=[]
        if realistic_synthetic: reasons.append("realistic synthetic content")
        if altered_real_person: reasons.append("real person altered/generated")
        if altered_real_event: reasons.append("real event/place materially altered")
        if generated_realistic_scene: reasons.append("realistic scene that did not occur")
        return {"required": bool(reasons), "reasons": reasons or
                (["production assistance only"] if production_assistance_only else ["no trigger evidence"])}

class AdvertiserPrecheck:
    HIGH_RISK: ClassVar[frozenset[str]] = frozenset({"graphic violence","sexual content","slur","hate","drugs","firearms"})
    MEDIUM_RISK: ClassVar[frozenset[str]] = frozenset({"shocking","controversial issue","sensitive event","self-harm","suicide","domestic abuse","terrorism","war","conflict"})
    def evaluate(self, text: str) -> Result:
        lower=text.lower()
        high=sorted(t for t in self.HIGH_RISK if t in lower)
        medium=sorted(t for t in self.MEDIUM_RISK if t in lower)
        reasons=[f"HIGH: {t}" for t in high]+[f"MEDIUM: {t}" for t in medium]
        if high: return Result(False,reasons,0.0,"HIGH")
        if medium: return Result(True,reasons,0.5,"MEDIUM")
        return Result(True,[],1.0,"LOW")

class PolicyEngine:
    def evaluate(self,title,description,script,rights,disclosure) -> Result:
        reasons=[]
        if not rights: reasons.append("rights not cleared")
        if len(title.strip())<3: reasons.append("title too short")
        if not script.strip(): reasons.append("empty script")
        ad=AdvertiserPrecheck().evaluate(f"{title} {description} {script}")
        reasons.extend(ad.reasons)
        return Result(not reasons and ad.risk_level!="HIGH",reasons,ad.score,ad.risk_level)

class BudgetGuard:
    def __init__(self,max_daily): self.max_daily=max_daily
    def allowed(self,spent,estimate): return spent+estimate<=self.max_daily

class QuotaManager:
    def __init__(self,daily): self.daily=daily
    def allowed(self,used,cost): return used+cost<=self.daily
    def remaining(self,used): return max(0,self.daily-used)

class OllamaProvider:
    def __init__(self,url,model): self.url,self.model=url.rstrip("/"),model
    async def generate(self,prompt):
        async with httpx.AsyncClient(timeout=90) as c:
            r=await c.post(self.url+"/api/generate",json={"model":self.model,"prompt":prompt,"stream":False})
            r.raise_for_status()
            return r.json().get("response","")

class MockProvider:
    async def generate(self,prompt): return "Safe simulation draft: "+prompt[:120]

class AIProvider:
    @staticmethod
    def get():
        s=get_settings()
        return OllamaProvider(s.ollama_base_url,s.ollama_model) if s.ai_provider=="ollama" else MockProvider()

class YouTubePublisher:
    async def upload(self,path,title,description,disclosure):
        s=get_settings()
        if not(s.youtube_publish_enabled and s.publish_enabled):
            return {"status":"SIMULATED","video_id":hashlib.sha1(path.encode()).hexdigest()[:11]}
        if not(s.youtube_client_id and s.youtube_client_secret and s.youtube_refresh_token):
            raise RuntimeError("YouTube OAuth is not configured")
        raise RuntimeError("Production OAuth/resumable upload adapter requires staging credentials and integration tests")
