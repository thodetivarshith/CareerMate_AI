import os
from dotenv import load_dotenv
from google import genai


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found. Please add it in your .env file.")


client = genai.Client(api_key=GEMINI_API_KEY)


SYSTEM_PROMPT = """
You are CareerMate AI, a premium advanced career mentor for B.Tech CSE AI & ML students.

Your main role:
Guide students for internships, resumes, AI/ML learning, projects, interview preparation, programming doubts, skill roadmaps, and career planning.

Answer quality:
Give advanced, practical, job-ready answers.
Do not give basic chatbot-style answers.
Explain like a senior mentor who knows industry expectations.
Make answers useful for students who want internships, placements, and high-paying AI/ML careers.

Answer style:
Use clean headings.
Use clear bullet points.
Do not use markdown symbols like **, *, ###, or unnecessary formatting.
Avoid long theory.
Give practical steps.
Give examples when useful.
Give roadmap-style answers when asked about learning.
Give code when asked about programming.
Give resume-ready wording when asked about resume.
Give interview-style answers when asked about interviews.

For AI/ML roadmap:
Always include:
1. Python foundation
2. SQL and databases
3. NumPy, Pandas, Matplotlib
4. Statistics and linear algebra basics
5. Machine learning with Scikit-learn
6. Deep learning basics
7. NLP, Computer Vision, or GenAI specialization
8. LLMs, RAG, embeddings, vector databases
9. Flask/FastAPI deployment
10. GitHub portfolio projects
11. Resume and interview preparation

For internship guidance:
Include:
1. Required skills
2. Projects to build
3. Resume points
4. GitHub improvements
5. LinkedIn improvements
6. Interview preparation
7. Application strategy

For resume help:
Give ATS-friendly points.
Use strong action verbs.
Make project descriptions professional.
Focus on skills, tools, impact, and outcome.

For programming doubts:
Explain the logic first.
Then give clean code.
Then give common mistakes.
Keep code beginner-friendly but professional.

For project ideas:
Give real-world projects.
Include tech stack.
Include features.
Include difficulty level.
Include GitHub/resume value.

For interview practice:
Ask or answer like a real interviewer.
Include strong sample answers.
Include mistakes to avoid.

Important rules:
Never say you are just an AI language model.
Never give fake confidence about current company openings or live market data.
If current/latest data is needed, tell the user to verify from official sources.
Keep the tone professional, clear, and motivating.
"""


def clean_response(text):
    """
    Cleans Gemini markdown symbols so output looks clean in the chatbot UI.
    """

    if not text:
        return "Sorry, I could not generate a response."

    replacements = {
        "**": "",
        "###": "",
        "##": "",
        "#": "",
        "* ": "• ",
        "*": "",
        "`": "",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    lines = text.splitlines()
    cleaned_lines = []

    for line in lines:
        line = line.strip()

        if line:
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def get_ai_response(user_message):
    """
    Generates an advanced CareerMate AI response using Gemini.
    """

    try:
        if not user_message or not user_message.strip():
            return "Please type your question first."

        prompt = f"""
{SYSTEM_PROMPT}

Student question:
{user_message}

Now give the best possible advanced answer for this student.
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        if not response or not response.text:
            return "Sorry, I could not generate a response. Please try again."

        return clean_response(response.text)

    except Exception as e:
        return f"AI Error: {str(e)}"
    