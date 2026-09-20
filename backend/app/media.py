from pathlib import Path
class DeterministicRenderer:
 def render(self,output:str,metadata:dict)->str:
  p=Path(output);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(str(metadata),encoding="utf-8");return str(p)
