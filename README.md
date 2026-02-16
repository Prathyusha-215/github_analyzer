# GitHub Repository Analysis Evaluator

A comprehensive tool for analyzing student GitHub repositories and evaluating them based on data analysis, coding quality, and problem-solving capabilities. Supports analysis of any repository type with customizable evaluation criteria.

## 🚀 Quick Start

### Web Interface (Recommended)
```bash
cd github_analyzer
pip install flask werkzeug
python app.py
```
Then open http://localhost:5000 in your browser!

### Command Line
```bash
cd github_analyzer
python main.py
```

## Features

- 🔍 **Flexible Repository Detection**: Analyze any repository or filter by custom keywords
- 📊 **Comprehensive Code Analysis**: Evaluates data manipulation, algorithms, and coding quality
- 🤖 **AI-Powered Evaluation**: Uses Groq LLM for intelligent code assessment with custom criteria
- 🌐 **Web Interface**: User-friendly web UI for easy file uploads and configuration
- 📈 **Progress Tracking**: Real-time progress bars and detailed logging
- ⚡ **Optimized Performance**: Token-efficient processing with rate limit management
- 🔧 **Configurable**: Easy-to-modify settings for different analysis scenarios
- 📝 **Dynamic Evaluation**: Upload custom question files for tailored assessments
- � **Smart Excel Processing**: Auto-detects columns, removes duplicates, handles various formats

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   Create a `.env` file with:
   ```
   GITHUB_TOKEN=your_github_token_here
   GROQ_API_KEY=your_groq_api_key_here
   ```

3. **Prepare student data:**
   Create an Excel file with student information. The tool automatically detects columns containing names and GitHub links:

   **Flexible Column Names** (case-insensitive):
   - **Student Names**: `name`, `student name`, `full name`, `user`, etc.
   - **GitHub Links**: `github`, `repo`, `link`, `url`, `profile`, etc.

   **Supported GitHub URL Formats**:
   - `https://github.com/username`
   - `https://github.com/username/repo`
   - `github.com/username`
   - `username/repo`
   - `username`

   **Example Excel Structure**:
   ```
   | Student Name | GitHub Profile | Class |
   |-------------|---------------|-------|
   | John Doe    | john123       | A     |
   | Jane Smith  | jane-dev      | B     |
   ```

   The tool will automatically:
   - ✅ Detect the correct columns
   - ✅ Remove duplicate entries
   - ✅ Clean and validate GitHub URLs
   - ✅ Show processing summary

## Configuration

Edit `config.py` to customize:

- **Repository Keywords**: What types of repos to analyze
- **Analysis Keywords**: What code patterns to look for
- **Performance Settings**: Workers, delays, token limits

### Repository Search Configuration:

**Default (Analyze Any Repository):**
```python
REPO_KEYWORDS = []  # Empty list = analyze most recent repository
```

**Specific Analysis Focus Examples:**

**Transaction Analysis:**
```python
REPO_KEYWORDS = ['transaction', 'transactions', 'sales', 'revenue', 'customer', 'purchase']
```

**Data Science Projects:**
```python
REPO_KEYWORDS = ['machine learning', 'ml', 'ai', 'data science', 'analytics', 'pandas', 'numpy']
```

**Web Development:**
```python
REPO_KEYWORDS = ['web', 'app', 'website', 'frontend', 'backend', 'api', 'react', 'django']
```

**Financial Analysis:**
```python
REPO_KEYWORDS = ['financial', 'banking', 'payment', 'invoice', 'accounting']
```

**Business Intelligence:**
```python
REPO_KEYWORDS = ['bi', 'business intelligence', 'analytics', 'reporting', 'dashboard']
```

## Usage

```bash
python main.py
```

The tool will:
1. Read student list from Excel
2. Find relevant repositories for each student
3. Analyze Jupyter notebooks
4. Generate AI-powered feedback
5. Save results to `evaluation.xlsx`

## 🌐 Web Interface Features

The web interface provides an intuitive way to:

- **📤 Upload Files**: Drag & drop Excel files and question text files
- **⚙️ Configure Settings**: Set repository keywords, API keys, and analysis parameters
- **📊 View Results**: See analysis summary with metrics and detailed results table
- **📥 Download Reports**: Export comprehensive evaluation reports in Excel format
- **🔍 Real-time Feedback**: Monitor analysis progress and status updates

### Web Interface Screenshots
- Clean, modern Bootstrap-based UI
- Responsive design for desktop and mobile
- Progress indicators and status badges
- Interactive results table with filtering

## Evaluation Criteria

The tool evaluates repositories based on **specific transaction analysis questions** from the provided requirements:

**Sales & Revenue Analysis:**
- Total sales amount across all transactions
- Monthly transaction amounts and trends
- Highest single transaction amounts
- Service category revenue contributions

**Customer Analysis:**
- Unique customers and spending patterns
- Average transaction amount per customer
- Customer segmentation and repeat buyer analysis
- Cross-category purchase behavior

**Product & Service Performance:**
- Product revenue performance
- Service popularity by transaction count
- Product category analysis
- Average spending by product type

**Geographic Analysis:**
- State and city sales performance
- Regional spending patterns
- Geographic service popularity
- State-specific product preferences

**Temporal Analysis:**
- Monthly and quarterly sales trends
- Seasonal patterns and spikes
- Transaction volume over time

**Transaction Analysis:**
- Payment method analysis (credit vs debit)
- Transaction count patterns
- Average spending comparisons

## Advanced Features

- **Two-step LLM pipeline**: Compresses notebooks before analysis for better token efficiency
- **Smart filtering**: Only analyzes relevant data science code
- **Rate limit management**: Automatically handles API limits
- **Error resilience**: Continues processing even if individual students fail

## Customization

The tool is highly modular. You can:
- Modify analysis criteria in `prompts.py`
- Change repository search logic in `github_fetcher.py`
- Adjust notebook parsing in `notebook_parser.py`
- Customize output format in `excel_writer.py`

## Requirements

- Python 3.8+
- GitHub Personal Access Token
- Groq API Key
- Student data in Excel format

## License

MIT License - feel free to modify and distribute!
