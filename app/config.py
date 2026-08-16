import os

from dotenv import load_dotenv

load_dotenv()

PSEUDOGRAM_API_KEY = os.getenv("PSEUDOGRAM_API_KEY")

PSEUDOGRAM_API_BASE_URL = os.getenv(
    "PSEUDOGRAM_API_BASE_URL",
    "https://pseudogram-api.onrender.com",
)

MONGODB_URL = os.getenv(
    "MONGODB_URL",
    "mongodb://localhost:27017",
)

DATABASE_NAME = os.getenv(
    "DATABASE_NAME",
    "linkplease",
)