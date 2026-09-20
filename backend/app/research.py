from dataclasses import dataclass
from datetime import datetime,timezone
@dataclass(frozen=True)
class ResearchEvidence:
 source:str;claim:str;retrieved_at:datetime
class ResearchService:
 def normalize(self,source,claim):return ResearchEvidence(source,claim,datetime.now(timezone.utc))
