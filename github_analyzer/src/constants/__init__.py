import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Repository search keywords
    REPO_KEYWORDS = []

    # Notebook analysis settings
    MAX_NOTEBOOK_CHARS = 5000
    IMPORTANT_KEYWORDS = [
        # Web Scraping
        "requests", "beautifulsoup", "bs4", "selenium", "scrape", "scrapy",
        "get_text", "find_all", "soup.find", "driver.get", "amazon",

        # Data fields
        "product_title", "brand", "ram", "storage", "ssd", "windows", "color",
        "price", "rating", "processor", "screen_size", "laptop",

        # Data Cleaning / Pandas
        "pandas", "pd.", "read_csv", "read_excel", "dropna", "fillna",
        "isnull", "notnull", "drop_duplicates", "astype", "to_numeric",
        "groupby", "merge", "concat",

        # CSV output
        "to_csv", "amazon_laptop_raw", "amazon_laptop_cleaned",

        # Analysis & Visualization
        "matplotlib", "seaborn", "plt.", "plot", "bar", "hist", "scatter", "pie",
        "correlation", "corr", "value_counts", "mean", "describe",
        "numpy", "np.",

        # Regex patterns used
        "re.search", "re.match", "re.sub",
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
You are a Senior Data Science Mentor evaluating a student's GitHub repository for the Amazon Laptop Market Analysis project.

You will be provided with the contents of ALL files in the student's repository — including Python scripts (.py), Jupyter notebooks (.ipynb), CSV file headers, and any README/documentation. Evaluate the ENTIRE repository, not just a single file.

----------------------------

WHAT TO EVALUATE (based on the project requirements):

PART 1 — WEB SCRAPING (from Amazon):
- Did they scrape at least 100 laptop products?
- Did they extract all required fields: product_title, Brand, RAM, Storage (SSD), Windows version, Color, Price, Rating, Processor?
- Did they use BeautifulSoup, Requests, or Selenium correctly?

PART 2 — DATAFRAME & DATA CLEANING:
- Created a Pandas DataFrame from scraped data
- Checked shape, info, and missing values
- Removed duplicates
- Converted Price to numeric
- Extracted Brand from title if not directly available

PART 3 — FILE SAVING:
- Generated amazon_laptop_raw.csv
- Generated amazon_laptop_cleaned.csv

PART 4 — ANALYSIS QUESTIONS (all 8 expected):
1. Brand with highest average price
2. Brand with highest average rating
3. Top 5 most reviewed laptops
4. Average discount percentage
5. Price vs Rating correlation
6. Distribution of laptops by RAM
7. Most common screen size
8. Count of laptops under ₹50,000

----------------------------

EVALUATION INSTRUCTIONS:

1. Check each part above — note what is present, missing, or incorrect.
2. Evaluate:
   - Scraping correctness and completeness
   - Data cleaning thoroughness
   - Accuracy-and depth of analysis
   - Code quality and readability
3. Do NOT list every requirement one by one.
4. Do NOT exceed 4 bullet points per section. (mandatory)
5. Be concise, specific, and professional.
6. If major sections (scraping, cleaning, analysis) are missing, state it briefly but clearly.
7. Avoid generic praise — reference actual code or file evidence.


----------------------------

OUTPUT FORMAT (STRICTLY FOLLOW):

MENTOR COMMENTS:

What You're Doing Well:
-------

How to Improve:
-----
Mentor Note:
- Short high-level summary (1 bullet point max)


--------------------------

Now evaluate the provided repository content.
"""
