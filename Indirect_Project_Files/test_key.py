import os
from dotenv import load_dotenv

load_dotenv()
print("Your saved key starts with:", os.environ.get("OPENAI_API_KEY")[:7])