import os
from dotenv import load_dotenv

load_dotenv()

# Global development mode flag
DEVELOPMENT_MODE = False

# Resend Configuration
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
RECRUITER_EMAIL = os.getenv("RECRUITER_EMAIL", "ndgaming458@gmail.com")

