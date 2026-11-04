"""Application configuration."""
from pathlib import Path
import os

APP_NAME = "SmartHire AI"
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = Path(os.environ.get("SMARTHIRE_DB_PATH", DATA_DIR / "smarthire.db"))
MAX_UPLOAD_MB = 10
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
MAX_UPLOAD_BATCH_MB = 250
MAX_UPLOAD_BATCH_BYTES = MAX_UPLOAD_BATCH_MB * 1024 * 1024
SAMPLE_JOB_TITLE = "Talent Acquisition Intern – AI & LLM"
SAMPLE_REQUIRED_SKILLS = ["Python", "NLP", "machine learning", "SQL", "prompt engineering", "communication", "problem solving"]
SAMPLE_PREFERRED_SKILLS = ["scikit-learn", "pandas", "generative AI", "Git"]
SKILL_VOCABULARY = [
    "Python", "Java", "SQL", "machine learning", "deep learning", "NLP",
    "natural language processing", "scikit-learn", "pandas", "NumPy",
    "generative AI", "LLMs", "large language models", "prompt engineering",
    "FastAPI", "REST API", "Git", "data analysis", "communication",
    "problem solving", "HTML", "CSS", "JavaScript", "testing", "data visualization",
    "Power BI", "Tableau", "Excel", "recruitment", "talent acquisition",
]
