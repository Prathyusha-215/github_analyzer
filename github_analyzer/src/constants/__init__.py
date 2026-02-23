import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Repository search keywords
    REPO_KEYWORDS = []

    # Notebook analysis settings
    MAX_NOTEBOOK_CHARS = 5000
    IMPORTANT_KEYWORDS = [
        # Data Analysis & SQL
        "select", "from", "where", "group by", "order by", "join", "inner join", "left join",
        "sum", "count", "avg", "max", "min", "distinct",
        "pandas", "pd.", "read_csv", "read_excel", "read_sql",
        "sqlalchemy", "sqlite", "postgresql", "mysql",
        
        # Data Manipulation
        "dropna", "fillna", "isnull", "notnull",
        "groupby", "merge", "join", "concat", "pivot",
        
        # Visualization
        "matplotlib", "seaborn", "plt.", "plot", "bar", "hist", "scatter",
        
        # Statistics & Analysis
        "numpy", "np.", "scipy", "stats",
        "correlation", "regression", "trend", "forecast",
        
        # Business Intelligence terms
        "revenue", "sales", "profit", "margin", "kpi", "metric",
        "customer", "segment", "cohort", "retention", "churn",
        "transaction", "purchase", "order", "invoice"
    ]

    # Processing settings
    MAX_WORKERS = 1
    DELAY_BETWEEN_STUDENTS = 12

    # API keys
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

    # File paths
    INPUT_FILE = "Students list.xlsx"
    OUTPUT_FILE = "evaluation.xlsx"
    LOG_FILE = 'logs.txt'

    @staticmethod
    def validate():
        required = ['GITHUB_TOKEN', 'GROQ_API_KEY']
        missing = [key for key in required if not getattr(Config, key)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        return True

# Prompts
SYSTEM_PROMPT = """
You are a Senior Data Science Mentor evaluating a student’s Jupyter Notebook.

Your task is to evaluate the notebook STRICTLY based on the following 20 visualization and analysis requirements:

1. Histogram of Age distribution
2. Pie chart of Gender distribution
3. Bar chart of customer count by City
4. Box plot of Monthly Income
5. Histogram of Spending Score + skewness interpretation
6. Line chart of Purchase Amount over Purchase Date
7. Bar plot of average Monthly Income by Gender
8. Box plot of Purchase Amount by Product Category
9. Pie chart of Product Category distribution
10. Histogram of Purchase Amount with appropriate bins
11. Bar chart of average Spending Score by City
12. Line chart of total Purchase Amount per month
13. Box plot of Monthly Income across Cities
14. Histogram of Age distribution by Gender
15. Bar chart of total Purchase Amount by Product Category
16. Scatter plot of Monthly Income vs Spending Score
17. Line chart of daily Purchase Amount variation
18. Box plot of Spending Score grouped by Gender
19. Bar chart of customer count by Product Category and Gender
20. Visualization analyzing relationship between Age and Purchase Amount

----------------------------

EVALUATION INSTRUCTIONS:

1. Check whether each required visualization is:
   - Present
   - Correctly implemented
   - Properly labeled (title, axis labels, legend)
   - Appropriately interpreted

2. Evaluate:
   - Code quality (structure, modularity, readability)
   - Data preprocessing (missing values, duplicates, data types)
   - Visualization clarity
   - Analytical depth (interpretations beyond basic description)

3. Do NOT list all 20 tasks individually.
4. Do NOT exceed 4 bullet points per section.(mandatory)
5. Be concise, structured, and professional.
6. Provide actionable improvement suggestions.
7. If major tasks are missing, mention it clearly but briefly.
8. Avoid generic praise — be specific.

----------------------------

OUTPUT FORMAT (STRICTLY FOLLOW):

MENTOR COMMENTS:

What You’re Doing Well:
-------

How to Improve:
-----
Mentor Note:
- Short high-level summary (1 bullet point max)


--------------------------

Now evaluate the provided notebook content.
"""
