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
        You are a technical signal extractor preparing a repository summary for an automated hackathon evaluator.

The repository is a submission for the Smart Railway Resource Planning System hackathon.
Your summary MUST surface repo-specific details that allow a downstream evaluator to write NON-GENERIC feedback.

CRITICAL RULES:
- Extract EXACT names: column names, function names, file names, variable names, model class names, threshold values.
- Do NOT write generic observations like "uses pandas" or "has visualizations" — name WHAT specifically.
- If a detail is not present in the repo, say "Not found" for that field. Do NOT invent.
- The summary must be UNIQUE to this repo — nothing you write should be applicable to any other project.

----------------------------------

Return ONLY this structure (fill every field precisely):

### 1. Project Objective
One sentence describing what THIS solution does for railway planning.

### 2. Dataset
- Source: [real CSV/Excel / synthetic generated / API / not found]
- Exact column names found (list all relevant ones): e.g. train_id, route, passenger_count, occupancy_rate, num_coaches, platform_no, is_holiday, delay_minutes
- Missing key fields (from the hackathon requirement): [list what's absent]
- Row count or data size (if visible): [e.g. 5000 rows, 12 months]

### 3. Visualizations
List EACH chart by its exact type and what railway variable it shows:
- e.g. "Seaborn heatmap of hourly passenger_count by route"
- e.g. "Plotly bar chart of top 10 high-demand routes by avg occupancy"
- e.g. "Matplotlib time-series of daily passenger volume for Route A-B"
If none found: "No visualizations found."

### 4. Prediction / Forecasting
- Model used: [exact class name, e.g. RandomForestRegressor, LinearRegression, Prophet, ARIMA]
- Target variable predicted: [e.g. passenger_count, occupancy_rate]
- Features used: [list the actual input columns]
- Evaluation metrics with VALUES (if shown): [e.g. RMSE=142.3, R²=0.87]
- Train/test split approach: [e.g. 80/20 random, time-based split, cross-validation]
- Overfitting/validation concerns: [note if test set is missing, leakage risk, etc.]
If none found: "No prediction model found."

### 5. Resource Allocation Logic
- Describe the EXACT logic (copy or paraphrase the decision rule):
  e.g. "if predicted_occupancy > 0.85 and route in peak_routes: recommend += 1 coach"
- Output format of recommendation: [e.g. printed table, saved CSV, shown in dashboard]
- Is logic rule-based or model-driven?
If none found: "No allocation logic found."

### 6. Dashboard / Web App
- Framework: [Streamlit / Dash / Flask / FastAPI / Jupyter widgets / none]
- Interactive features: [filters, dropdowns, date pickers, route selectors — list what exists]
- What can a user do in the UI? [be specific, e.g. "select a route and see demand forecast"]
If none found: "No dashboard/UI found."

### 7. Code Structure
- Main files and their roles: [e.g. app.py (Streamlit UI), model.py (RandomForest training), data_loader.py (CSV ingestion)]
- Is logic modular (multiple files/functions) or monolithic (single script)?
- README present? Does it explain setup + how to run? [yes/no/partial]

### 8. Hackathon Goal Coverage
For each goal, state PRESENT or MISSING and one-line evidence:
- Overcrowding Reduction: [PRESENT — identifies routes with occupancy > 90% | MISSING]
- Coach/Train Allocation: [PRESENT — recommends extra coaches via threshold logic | MISSING]
- Platform Usage: [PRESENT — platform_no field used in analysis | MISSING]
- Proactive Scheduling: [PRESENT — 7-day demand forecast generated | MISSING]

----------------------------------

OUTPUT RULES:
- Maximum 500 words.
- No motivational language, no emojis, no teaching tone.
- Use exact names from the code, not paraphrases.
- The downstream evaluator will use this summary to write specific feedback — accuracy is critical.

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

        # Use the system prompt directly (no dynamic questions for hackathon evaluation)
        system_prompt = SYSTEM_PROMPT

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
                            "content": f"Here is the participant's repository summary:\n\n{summary}",
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
