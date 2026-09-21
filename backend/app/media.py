from pathlib import Path
import subprocess

class FFmpegRenderer:
    """Media utility: external video is ingested; FFmpeg is retained only for thumbnail extraction."""
    def extract_thumbnail(self,video_path:str,thumbnail_path:str)->str:
        source=Path(video_path); target=Path(thumbnail_path)
        target.parent.mkdir(parents=True,exist_ok=True)
        command=["ffmpeg","-y","-loglevel","error","-ss","0","-i",str(source),"-frames:v","1","-q:v","2",str(target)]
        subprocess.run(command,check=True,timeout=30)
        if not target.exists() or target.stat().st_size==0: raise RuntimeError("FFmpeg produced no thumbnail")
        return str(target)
