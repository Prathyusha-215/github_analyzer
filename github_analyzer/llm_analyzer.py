import os
import time
from groq import Groq
from dotenv import load_dotenv
from prompts import SYSTEM_PROMPT
from config import CONFIG  # <-- Add this line

load_dotenv()

# Create client once globally
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not found in environment variables")

client = Groq(api_key=api_key)

def analyze_code_with_llm(code_content, questions_content=None):
    """
    Two-step evaluation pipeline: compress notebook first, then evaluate summary.
    Uses dynamic questions if provided.
    """
    # Step 1: Compress the notebook
    summary = compress_notebook(code_content)

    # Step 2: Evaluate the compressed summary
    return evaluate_summary(summary, questions_content)

def compress_notebook(code_content):
    """
    Compresses notebook content into a focused summary.
    """
    time.sleep(4)  # Throttle
    
    compression_prompt = """
    Summarize this notebook in 300 words focusing on:
    - Pandas usage and data manipulation
    - Data cleaning techniques
    - Visualization approaches
    - Overall code quality and structure
    
    Be concise and objective.
    """
    
    retries = 3
    for attempt in range(retries):
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a technical summarizer. Create concise, factual summaries.",
                    },
                    {
                        "role": "user",
                        "content": f"{compression_prompt}\n\nNotebook content:\n\n{code_content}",
                    }
                ],
                model="llama-3.1-8b-instant",
                temperature=0.3,
                max_tokens=400  # Limit output tokens
            )
            
            return chat_completion.choices[0].message.content
        except Exception as e:
            if "429" in str(e) and attempt < retries - 1:
                wait_time = (attempt + 1) * 30
                import logging
                logging.warning(f"Compression rate limit hit (Attempt {attempt+1}/{retries}). Sleeping for {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                # Fallback: return original content if compression fails
                return code_content[:2000]

def evaluate_summary(summary, questions_content=None):
    """
    Evaluates the compressed notebook summary.
    Uses dynamic questions if provided.
    """
    time.sleep(CONFIG['DELAY_BETWEEN_STUDENTS'])  # Throttle

    # Create dynamic prompt based on questions
    if questions_content:
        system_prompt = f"""
    You are a senior business analyst evaluating a data analysis Jupyter notebook.

    Evaluate the notebook against the provided analysis questions. Use the questions silently for assessment — DO NOT list, restate, summarize, or reference them in your response.

    Only evaluate work that is explicitly visible in the notebook. Do not assume missing analysis was performed.

    Be strict, objective, and evidence-based. Avoid generosity in feedback.

    Criteria:
    - Data Analysis & Querying
    - Business Logic Implementation
    - Code Quality & Structure
    - Results Interpretation
    - Documentation & Presentation
    - Problem-Solving Approach

    Rules:
    - Each bullet under 10 words
    - No repeated ideas across sections
    - Merge similar points into one bullet
    - No filler language or generic praise
    - No meta commentary
    - No contradictions
    - Prefer high-signal feedback only

    Penalize if you observe:
    - Missing data cleaning
    - Lack of visualizations
    - No interpretation of results
    - Over-reliance on print outputs
    - Weak structure or repeated calculations

    Reward only clearly demonstrated analysis aligned with the questions.

    Return EXACTLY:

    POSITIVES:
    - ...

    NEGATIVES:
    - ...

    IMPROVEMENTS:
    - ...
"""
    else:
        from prompts import SYSTEM_PROMPT
        system_prompt = SYSTEM_PROMPT

    retries = 3
    for attempt in range(retries):
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": f"Here is the student's notebook summary:\n\n{summary}",
                    }
                ],
                model="llama-3.1-8b-instant",
                temperature=0.1,
            )

            return chat_completion.choices[0].message.content
        except Exception as e:
            if "429" in str(e) and attempt < retries - 1:
                wait_time = (attempt + 1) * 30
                import logging
                logging.warning(f"Evaluation rate limit hit (Attempt {attempt+1}/{retries}). Sleeping for {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise Exception(f"Error calling Groq API: {e}")
