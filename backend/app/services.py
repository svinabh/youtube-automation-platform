from dataclasses import dataclass
import re,hashlib
import httpx
from .config import get_settings
@dataclass
class Result:passed:bool;reasons:list[str];score:float
class VariationGuard:
 def __init__(self,limit=.82):self.limit=limit
 def fp(self,s):
  w=re.findall(r"[a-z0-9]+",s.lower());return {" ".join(w[i:i+5]) for i in range(max(0,len(w)-4))}
 def similarity(self,a,b):x,y=self.fp(a),self.fp(b);return len(x&y)/max(1,len(x|y))
 def allowed(self,candidate,previous):return all(self.similarity(candidate,p)<self.limit for p in previous)
class RightsRegistry:
 def cleared(self,assets):return bool(assets) and all(a.get("cleared") is True and a.get("license") for a in assets)
class DisclosureTagger:
 def evaluate(self,realistic_synthetic=False,altered_real_person=False,altered_real_event=False,generated_realistic_scene=False,production_assistance_only=False):
  r=[]
  if realistic_synthetic:r.append("realistic synthetic content")
  if altered_real_person:r.append("real person altered/generated")
  if altered_real_event:r.append("real event/place materially altered")
  if generated_realistic_scene:r.append("realistic scene that did not occur")
  return {"required":bool(r),"reasons":r or (["production assistance only"] if production_assistance_only else ["no trigger evidence"])}
class AdvertiserPrecheck:
 risks={"graphic violence","sexual content","hate","slur","drugs","firearms","shocking"}
 def evaluate(self,text):h=[x for x in self.risks if x in text.lower()];return Result(not h,h,1 if not h else 0)
class PolicyEngine:
 def evaluate(self,title,description,script,rights,disclosure):
  r=[] 
  if not rights:r.append("rights not cleared")
  if len(title.strip())<3:r.append("title too short")
  if not script.strip():r.append("empty script")
  r+=AdvertiserPrecheck().evaluate(" ".join([title,description,script])).reasons
  return Result(not r,r,1 if not r else 0)
class BudgetGuard:
 def __init__(self,max_daily):self.max_daily=max_daily
 def allowed(self,spent,estimate):return spent+estimate<=self.max_daily
class QuotaManager:
 def __init__(self,daily):self.daily=daily
 def allowed(self,used,cost):return used+cost<=self.daily
 def remaining(self,used):return max(0,self.daily-used)
class OllamaProvider:
 def __init__(self,url,model):self.url=url.rstrip("/");self.model=model
 async def generate(self,prompt):
  async with httpx.AsyncClient(timeout=90) as c:
   r=await c.post(self.url+"/api/generate",json={"model":self.model,"prompt":prompt,"stream":False});r.raise_for_status();return r.json().get("response","")
class MockProvider:
 async def generate(self,prompt):return "Safe simulation draft: "+prompt[:120]
class AIProvider:
 @staticmethod
 def get():
  s=get_settings();return OllamaProvider(s.ollama_base_url,s.ollama_model) if getattr(s,"ai_provider","ollama")=="ollama" else MockProvider()
class YouTubePublisher:
 async def upload(self,path,title,description,disclosure):
  s=get_settings()
  if not(s.youtube_publish_enabled and s.publish_enabled):return {"status":"SIMULATED","video_id":hashlib.sha1(path.encode()).hexdigest()[:11]}
  if not(s.youtube_client_id and s.youtube_client_secret and s.youtube_refresh_token):raise RuntimeError("YouTube OAuth is not configured")
  raise RuntimeError("Production OAuth/resumable upload adapter requires staging credentials and integration tests")
