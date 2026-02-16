import os
from dotenv import load_dotenv

load_dotenv()

# Configuration settings
CONFIG = {
    # Repository search keywords (searches both name and description)
    # Set to empty list to analyze the most recent repository
    'REPO_KEYWORDS': [],  # Empty means analyze any repository

    # Notebook analysis settings
    'MAX_NOTEBOOK_CHARS': 5000,
    'IMPORTANT_KEYWORDS': [
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
    ],

    # Processing settings
    'MAX_WORKERS': 1,  # Keep low to respect API limits
    'DELAY_BETWEEN_STUDENTS': 2,

    # API settings
    'GITHUB_TOKEN': os.getenv("GITHUB_TOKEN"),
    'GROQ_API_KEY': os.getenv("GROQ_API_KEY"),

    # File paths
    'INPUT_FILE': "Students list.xlsx",
    'OUTPUT_FILE': "evaluation.xlsx",
    'LOG_FILE': 'logs.txt'
}

# Validate configuration
def validate_config():
    """Validate that all required configuration is present"""
    required = ['GITHUB_TOKEN', 'GROQ_API_KEY']
    missing = [key for key in required if not CONFIG.get(key)]

    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    return True