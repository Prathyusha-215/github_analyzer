import time
from groq import Groq
from src.constants import Config, SYSTEM_PROMPT, COMPRESSION_PROMPT
from src.logger.logging_config import setup_logging

logger = setup_logging()


class LLMEngine:
    def __init__(self):
        self.api_key = Config.GROQ_API_KEY
        self.client = Groq(api_key=self.api_key) if self.api_key else None

    def analyze_repo(self, repo_content, user_context=None):
        """
        Two-step evaluation pipeline:
          1. Compress raw repo content into a focused summary (fast / cheap model)
          2. Evaluate that summary against user context (capable model)
        """
        summary = self.compress_repo_content(repo_content)
        if summary:
            logger.info(f"Compression OK: {len(summary)} chars summary produced.")
            
        raw_response = self.evaluate_summary(summary, user_context)
        logger.info(f"[LLM RAW RESPONSE]: {repr(raw_response)}")
        
        return raw_response

    def compress_repo_content(self, repo_content):
        """
        Compresses repository content into a focused technical summary
        using a fast model. Falls back to truncated raw content on failure.
        """
        if not self.client:
            raise ValueError("GROQ_API_KEY not found in configuration")
        time.sleep(4)  # Throttle

        retries = 3
        for attempt in range(retries):
            try:
                chat_completion = self.client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a technical summarizer. Create concise, factual summaries of GitHub repositories.",
                        },
                        {
                            "role": "user",
                            "content": f"{COMPRESSION_PROMPT}\n\nRepository content:\n\n{repo_content}",
                        }
                    ],
                    model="llama-3.1-8b-instant",
                    temperature=0.3,
                    max_tokens=500,
                )
                return chat_completion.choices[0].message.content
            except Exception as e:
                if "429" in str(e) and attempt < retries - 1:
                    wait_time = (attempt + 1) * 30
                    logger.warning(f"Compression rate limit hit (Attempt {attempt+1}/{retries}). Sleeping {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.warning(f"Compression failed, using raw content: {e}")
                    return repo_content[:3000]

    def evaluate_summary(self, summary, user_context=None):
        """
        Evaluates a compressed repo summary against the user's criteria.
        Returns structured OVERALL SCORE / CATEGORY SCORES / KEY STRENGTHS / CRITICAL ISSUES / SUMMARY feedback.
        """
        if not self.client:
            raise ValueError("GROQ_API_KEY not found in configuration")
        time.sleep(Config.DELAY_BETWEEN_REQUESTS)

        ctx = user_context if user_context and user_context.strip() else \
            "Evaluate this repository on general software engineering quality: code quality, documentation, structure, and best practices."

        system_prompt = SYSTEM_PROMPT.format(user_context=ctx)

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
                            "content": f"Here is the repository summary:\n\n{summary}",
                        }
                    ],
                    model="llama-3.3-70b-versatile",
                    temperature=0.1,
                )
                return chat_completion.choices[0].message.content
            except Exception as e:
                if "429" in str(e) and attempt < retries - 1:
                    wait_time = (attempt + 1) * 30
                    logger.warning(f"Evaluation rate limit hit (Attempt {attempt+1}/{retries}). Sleeping {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"Error calling Groq API: {e}")
