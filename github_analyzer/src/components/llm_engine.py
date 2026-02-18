import time
from groq import Groq
from src.constants import Config, SYSTEM_PROMPT
from src.logger.logging_config import setup_logging

logger = setup_logging()

class LLMEngine:
    def __init__(self):
        self.api_key = Config.GROQ_API_KEY
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in configuration")
        self.client = Groq(api_key=self.api_key)

    def analyze_code(self, code_content, questions_content=None):
        """
        Two-step evaluation pipeline: compress notebook first, then evaluate summary.
        Uses dynamic questions if provided.
        """
        # Step 1: Compress the notebook
        summary = self.compress_notebook(code_content)

        # Step 2: Evaluate the compressed summary
        return self.evaluate_summary(summary, questions_content)

    def compress_notebook(self, code_content):
        """
        Compresses notebook content into a focused summary.
        """
        time.sleep(4)  # Throttle
        
        compression_prompt = """
        You are a senior data science code reviewer.

Your task is to analyze and summarize a Jupyter notebook that will later be evaluated by another AI system.

IMPORTANT RULES:
- Be concise but information-dense.
- Do NOT explain step-by-step code.
- Do NOT repeat notebook content.
- Compress aggressively while preserving meaning.
- Limit the summary to HIGH-VALUE technical signals only.

Focus on extracting WHAT matters for evaluation.

----------------------------------

Return the summary strictly in the following structure:

### 1. Project Objective
Explain in 2–3 lines what problem the notebook is solving.

### 2. Dataset Understanding
- Data source (if mentioned)
- Key features used
- Target variable (if any)

### 3. Data Preprocessing
Mention only important techniques such as:
- missing value handling
- encoding
- scaling
- outlier treatment
- feature engineering

Skip if not present.

### 4. Analysis / Methods Used
Identify major techniques:

Examples:
- EDA
- visualization
- statistical analysis
- machine learning models
- NLP
- deep learning

Avoid listing basic pandas operations.

### 5. Model Information (If Present)
Include ONLY:
- algorithm names
- train/test split
- evaluation metrics

DO NOT describe algorithm theory.

### 6. Code Quality Signals
Briefly comment on:
- structure
- modularity
- readability
- comments
- repetition

Keep this under 5 bullet points.

### 7. Key Strengths
Max 5 bullets.

Only high-impact strengths.

### 8. Key Weaknesses / Gaps
Max 5 bullets.

Focus on evaluation-critical issues like:
- missing preprocessing
- lack of validation
- no visualization
- poor structure
- hardcoding

### 9. Overall Technical Complexity
Classify as ONE:

Beginner / Intermediate / Advanced

Base this on techniques used — not notebook length.

----------------------------------

OUTPUT RULES:
- Maximum 300-400 words.
- No fluff.
- No motivational language.
- No teaching tone.
- No emojis.
- No markdown outside the requested format.
- Be objective and professional.

The summary will be used for automated grading, so accuracy is critical.

        """
        
        retries = 3
        for attempt in range(retries):
            try:
                chat_completion = self.client.chat.completions.create(
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
                    logger.warning(f"Compression rate limit hit (Attempt {attempt+1}/{retries}). Sleeping for {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    # Fallback: return original content if compression fails
                    return code_content[:2000]

    def evaluate_summary(self, summary, questions_content=None):
        """
        Evaluates the compressed notebook summary.
        Uses dynamic questions if provided.
        """
        time.sleep(Config.DELAY_BETWEEN_STUDENTS)  # Throttle

        # Create dynamic prompt based on questions
        if questions_content:
            # Inject questions into the system prompt template if needed, 
            # but current prompts.py logic suggests replacing it or appending.
            # The previous logic was:
            system_prompt = SYSTEM_PROMPT.format(questions_content=questions_content)
        else:
             system_prompt = SYSTEM_PROMPT.format(questions_content="No specific questions provided.")

        retries = 3
        for attempt in range(retries):
            try:
                chat_completion = self.client.chat.completions.create(
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
                    model="llama-3.3-70b-versatile",
                    temperature=0.1,
                )

                return chat_completion.choices[0].message.content
            except Exception as e:
                if "429" in str(e) and attempt < retries - 1:
                    wait_time = (attempt + 1) * 30
                    logger.warning(f"Evaluation rate limit hit (Attempt {attempt+1}/{retries}). Sleeping for {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"Error calling Groq API: {e}")
