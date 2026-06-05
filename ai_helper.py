import os
from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found. Please check your .env file.")

client = genai.Client(api_key=api_key)


def get_ai_response(user_message, mode="general"):
    try:
        if mode == "resume":
            prompt = f"""
You are CareerMate AI Resume Analyzer.

Analyze this resume for internship/job selection.

Give output in this format:

1. Resume Score out of 100
2. First Impression
3. Strengths
4. Weaknesses
5. Missing Technical Skills
6. ATS Keyword Improvements
7. Projects Improvement
8. Better Resume Summary
9. Final Selection Chance
10. Exact Changes to Make

Use simple English.
Be practical.
Focus on internship selection, ATS, skills, projects, and resume improvement.

Resume:
{user_message}
"""
            max_tokens = 1400

        elif mode == "roadmap":
            prompt = f"""
You are CareerMate AI Roadmap Generator.

Create a practical career roadmap based on this information:

{user_message}

Give output in this format:

1. Main Goal
2. Current Level Analysis
3. Skills to Learn
4. Weekly Roadmap
5. Projects to Build
6. Tools to Learn
7. Resume Tasks
8. Interview Preparation
9. Mistakes to Avoid
10. Final Target

Use simple English.
Make it practical for a student.
"""
            max_tokens = 1400

        elif mode == "interview":
            prompt = f"""
You are CareerMate AI Interview Coach.

Prepare interview practice based on this information:

{user_message}

Give output in this format:

1. Role Understanding
2. 10 Interview Questions
3. Expected Answers
4. Common Mistakes
5. Scoring Tips
6. Final Preparation Advice

Use simple English.
Make answers suitable for beginner/intermediate students.
"""
            max_tokens = 1400

        else:
            prompt = f"""
You are CareerMate AI, a smart career guidance assistant.

Help users with:
- Career guidance
- Internship preparation
- Resume improvement
- Skill roadmap
- Project ideas
- Interview practice
- Programming doubts
- Study planning

Rules:
- Use simple English
- Give direct and practical answers
- Avoid unnecessary introduction
- Focus on useful steps
- For programming doubts, give clean code and explanation
- For career questions, give roadmap, skills, projects, and next steps

User question:
{user_message}
"""
            max_tokens = 900

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.4,
                max_output_tokens=max_tokens
            )
        )

        return response.text

    except Exception as e:
        error_message = str(e)

        if "429" in error_message or "RESOURCE_EXHAUSTED" in error_message:
            return "AI quota limit reached. Wait and try again later, change model, use a new API key from a new Google AI Studio project, or enable billing."

        if "404" in error_message or "NOT_FOUND" in error_message:
            return "AI model not found. Try model='gemini-2.5-flash' or model='gemini-2.5-flash-lite'."

        if "API_KEY" in error_message or "api key" in error_message.lower():
            return "Gemini API key error. Check your .env file and GEMINI_API_KEY."

        return f"AI Error: {error_message}"