from functools import lru_cache
from pydantic_settings import BaseSettings,SettingsConfigDict
class Settings(BaseSettings):
 app_env:str="development";database_url:str="sqlite+pysqlite:///./ytautomation.db";human_approval_required:bool=True
 publish_enabled:bool=False;youtube_publish_enabled:bool=False;youtube_client_id:str="";youtube_client_secret:str="";youtube_refresh_token:str=""
 ollama_base_url:str="http://localhost:11434";ollama_model:str="llama3.2:3b";max_daily_spend_usd:float=5;max_daily_uploads:int=2
 youtube_daily_quota:int=10000;global_kill_switch:bool=False
 model_config=SettingsConfigDict(env_file=".env",extra="ignore",case_sensitive=False)
@lru_cache
def get_settings():return Settings()
