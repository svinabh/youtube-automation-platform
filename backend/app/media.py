from pathlib import Path
import subprocess

class FFmpegRenderer:
    """Real deterministic MP4 renderer; final TTS/scene assembly remains a later phase."""
    def render(self,output:str,duration_seconds:float=1.0)->str:
        path=Path(output);path.parent.mkdir(parents=True,exist_ok=True)
        command=["ffmpeg","-y","-loglevel","error","-f","lavfi","-i","color=c=black:s=640x360:r=30",
                 "-f","lavfi","-i","anullsrc=r=48000:cl=stereo","-t",str(duration_seconds),
                 "-shortest","-c:v","libx264","-pix_fmt","yuv420p","-c:a","aac",str(path)]
        subprocess.run(command,check=True,timeout=30)
        if not path.exists() or path.stat().st_size==0: raise RuntimeError("FFmpeg produced no MP4")
        return str(path)
