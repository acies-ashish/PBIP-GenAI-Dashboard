import os
from groq import Groq
from dotenv import load_dotenv
load_dotenv()


def planner_client():
    return Groq(api_key=os.getenv("GROQ_PLANNER_KEY"))

def dashboard_client():
    return Groq(api_key=os.getenv("GROQ_DASHBOARD_KEY"))
