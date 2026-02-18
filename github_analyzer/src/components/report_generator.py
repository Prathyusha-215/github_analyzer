import pandas as pd
import re
from src.logger.logging_config import setup_logging

logger = setup_logging()

class ReportGenerator:
    def parse_llm_response(self, response_text):
        """
        Parses the structured LLM response to extract NOTEBOOK TYPE, OVERALL RATING, POSITIVES, NEGATIVES, and IMPROVEMENTS sections.
        """
        sections = {
            "notebook_type": "",
            "overall_rating": "",
            "positives": "",
            "negatives": "",
            "improvements": ""
        }
        
        current_section = None
        
        # Updated regex to handle purely capitalized headers, Markdown headers (### HEADER), and Bold headers (**HEADER**)
        header_pattern = re.compile(r"^[\#\*]*\s*(NOTEBOOK TYPE|OVERALL RATING|POSITIVES|NEGATIVES|IMPROVEMENTS)[\s\:\*]*", re.IGNORECASE)
        
        lines = response_text.split('\n')
        for line in lines:
            stripped_line = line.strip()
            match = header_pattern.match(stripped_line)
            if match:
                # Extract section name and remove any markdown symbols
                raw_section = match.group(1)
                current_section = raw_section.strip().title()
                # Normalizing keys to match dictionary keys
                if current_section.upper() == "POSITIVES":
                    current_section = "positives"
                elif current_section.upper() == "NEGATIVES":
                    current_section = "negatives"
                elif current_section.upper() == "IMPROVEMENTS":
                    current_section = "improvements"
                elif current_section.upper() == "NOTEBOOK TYPE":
                    current_section = "notebook_type"
                elif current_section.upper() == "OVERALL RATING":
                    current_section = "overall_rating"
                continue
                
            if current_section and stripped_line:
                if current_section == "overall_rating":
                    # Parse overall rating if it's on a separate line
                    rating_match = re.match(r"(\d+)/5", stripped_line)
                    if rating_match:
                        sections["overall_rating"] = rating_match.group(1)
                elif current_section == "notebook_type":
                    # Extract the notebook type
                    sections["notebook_type"] = stripped_line
                else:
                    sections[current_section] += stripped_line + "\n"
                
        # Strip trailing newlines from each section
        for key in sections:
            sections[key] = sections[key].strip()
        return sections

    def write_evaluation_file(self, results, output_file="evaluation.xlsx"):
        """
        Writes the list of result dictionaries to an Excel file.
        """
        try:
            # Map internal snake_case keys to Excel display columns
            column_mapping = {
                "student_name": "Student",
                "github_link": "GitHub Link",
                "repo_found": "Repo Found",
                "notebook_found": "Notebook Found",
                "positives": "Positives",
                "negatives": "Negatives",
                "improvements": "Improvements"
            }
            
            # Convert list of dicts to DataFrame
            df = pd.DataFrame(results)
            
            # Check if DataFrame is empty/missing columns
            if df.empty:
                logger.warning("No results to write to Excel.")
                return

            # Rename columns based on mapping (ignoring missing keys)
            rename_map = {k: v for k, v in column_mapping.items() if k in df.columns}
            df = df.rename(columns=rename_map)
            
            # Filter to only the desired display columns
            desired_columns = [v for k, v in column_mapping.items()]
            df = df[[col for col in desired_columns if col in df.columns]]
            
            df.to_excel(output_file, index=False)
            logger.info(f"Successfully wrote results to {output_file}")
        except Exception as e:
            logger.error(f"Error writing to Excel: {e}")
