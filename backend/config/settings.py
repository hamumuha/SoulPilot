import os

from dotenv import load_dotenv

# 必须在读取环境变量之前加载 .env（config.settings 是最早需要配置的模块）
load_dotenv()

# MySQL
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "hamu_pet")

# Server
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
CORS_ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if o.strip()
]
CONTEXT_ADMIN_USERNAMES = {
    username.strip().lower()
    for username in os.getenv("CONTEXT_ADMIN_USERNAMES", "").split(",")
    if username.strip()
}
DATA_ENCRYPTION_KEY = os.getenv("DATA_ENCRYPTION_KEY", "")
