from groq import Groq
from dotenv import load_dotenv
import os
import json

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def format_context(context_items):
    """Helper to format text + metadata into a readable string."""
    formatted = []
    for item in context_items:
        source = item['metadata']['source']
        page = item['metadata']['page']
        text = item['text']
        formatted.append(f"[Source: {source}, Page: {page}]\n{text}")
    return "\n\n".join(formatted)

def generate_answer(question, context_items):
    
    context_text = format_context(context_items)

    prompt = f"""
You are an academic study assistant.

Answer the question ONLY using the provided context. 
If the answer is not in the context, say "I cannot find the answer in the provided documents."
When you answer, explicitly cite the [Source] and [Page] provided in the context.

Context:
{context_text}

Question:
{question}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content

def generate_flashcards(context_items):

    context_text = format_context(context_items)

    prompt = f"""
Create 10 study flashcards from the text.
Return ONLY valid JSON.

Example:
[
  {{
    "question":"What is Machine Learning?",
    "answer":"A field of AI that enables systems to learn from data."
  }}
]

Content:
{context_text}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )

    result = response.choices[0].message.content.strip()

    if result.startswith("```json"):
        result = result.replace("```json", "")
        result = result.replace("```", "")
        result = result.strip()

    try:
        return json.loads(result)
    except Exception:
        return [{"question": "Error", "answer": "Failed to parse JSON"}]

def generate_study_guide(context_items):

    context_text = format_context(context_items)

    prompt = f"""
Create a detailed study guide.
Include:
1. Key Topics
2. Important Concepts
3. Revision Notes
4. Exam Tips

Content:
{context_text}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content