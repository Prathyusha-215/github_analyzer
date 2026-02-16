import pandas as pd
import re

def parse_llm_response(response_text):
    """
    Parses the structured LLM response to extract NOTEBOOK TYPE, OVERALL RATING, POSITIVES, NEGATIVES, and IMPROVEMENTS sections.
    """
    sections = {
        "Notebook Type": "",
        "Overall Rating": "",
        "Positives": "",
        "Negatives": "",
        "Improvements": ""
    }
    
    current_section = None
    
    # regex to identify headers
    header_pattern = re.compile(r"^(NOTEBOOK TYPE|OVERALL RATING|POSITIVES|NEGATIVES|IMPROVEMENTS):", re.IGNORECASE)
    
    lines = response_text.split('\n')
    for line in lines:
        stripped_line = line.strip()
        match = header_pattern.match(stripped_line)
        if match:
            current_section = match.group(1).title()
            # Normalizing keys to match dictionary keys
            # Removed normalization for NOTEBOOK TYPE and OVERALL RATING as requested
            if current_section.upper() == "POSITIVES":
                current_section = "Positives"
            elif current_section.upper() == "NEGATIVES":
                current_section = "Negatives"
            elif current_section.upper() == "IMPROVEMENTS":
                current_section = "Improvements"
            continue
            
        if current_section and stripped_line:
            if current_section == "Overall Rating":
                # Parse overall rating if it's on a separate line
                rating_match = re.match(r"(\d+)/5", stripped_line)
                if rating_match:
                    sections["Overall Rating"] = rating_match.group(1)
            elif current_section == "Notebook Type":
                # Extract the notebook type
                sections["Notebook Type"] = stripped_line
            else:
                sections[current_section] += stripped_line + "\n"
            
    # Strip trailing newlines from each section to avoid empty list items
    for key in sections:
        sections[key] = sections[key].strip()
    return sections

def write_evaluation_file(results, output_file="evaluation.xlsx"):
    """
    Writes the list of result dictionaries to an Excel file.
    """
    try:
        # Only keep the specified columns
        columns = [
            "Student",
            "GitHub Link",
            "Repo Found",
            "Notebook Found",
            "Positives",
            "Negatives",
            "Improvements"
        ]
        df = pd.DataFrame(results)
        # Filter to only the specified columns (ignore missing)
        df = df[[col for col in columns if col in df.columns]]
        df.to_excel(output_file, index=False)
        print(f"Successfully wrote results to {output_file}")
    except Exception as e:
        print(f"Error writing to Excel: {e}")
