import os
from groq import Groq
from dotenv import load_dotenv
load_dotenv()


def planner_client():
    return Groq(api_key=os.getenv("GROQ_PLANNER_KEY"))

def dashboard_client():
    return Groq(api_key=os.getenv("GROQ_DASHBOARD_KEY"))

def synonym_client():
    """Client for synonym generator agent - uses dedicated key to avoid rate limit conflicts"""
    return Groq(api_key=os.getenv("GROQ_SYNONYM_KEY"))
