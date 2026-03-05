import pandas as pd
import re
from src.logger.logging_config import setup_logging

logger = setup_logging()

class ReportGenerator:
    def parse_llm_response(self, response_text):
        """
        Parses the structured LLM response to extract OVERALL RATING and MENTOR COMMENTS.
        Handles both inline values ("OVERALL RATING: 7/10") and values on subsequent lines.
        """
        sections = {
            "overall_rating": "",
            "mentor_comments": ""
        }

        current_section = None

        # Matches headers like: "OVERALL RATING", "### OVERALL RATING", "**OVERALL RATING**"
        # Also captures any inline value after the colon (e.g. "OVERALL RATING: 7/10")
        header_pattern = re.compile(
            r"^[#\*\s]*\s*(OVERALL RATING|MENTOR COMMENTS)\s*[:\*#]*\s*(.*)?$",
            re.IGNORECASE
        )

        lines = response_text.split('\n')
        for line in lines:
            stripped_line = line.strip()
            match = header_pattern.match(stripped_line)
            if match:
                raw_section = match.group(1).strip().upper().replace(" ", "_")
                inline_value = (match.group(2) or "").strip()

                if raw_section == "OVERALL_RATING":
                    current_section = "overall_rating"
                    # Try to grab value inline (e.g. "OVERALL RATING: 7/10")
                    if inline_value:
                        rating_match = re.search(r"(\d{1,2})\s*/\s*10", inline_value)
                        if not rating_match:
                            rating_match = re.match(r"(\d{1,2})$", inline_value)
                        if rating_match:
                            sections["overall_rating"] = rating_match.group(1) + "/10"
                elif raw_section == "MENTOR_COMMENTS":
                    current_section = "mentor_comments"
                    if inline_value:
                        sections["mentor_comments"] += inline_value + "\n"
                continue

            if current_section and stripped_line:
                if current_section == "overall_rating" and not sections["overall_rating"]:
                    # Value on the next line
                    rating_match = re.search(r"(\d{1,2})\s*/\s*10", stripped_line)
                    if not rating_match:
                        rating_match = re.match(r"(\d{1,2})$", stripped_line)
                    if rating_match:
                        sections["overall_rating"] = rating_match.group(1) + "/10"
                elif current_section == "mentor_comments":
                    sections["mentor_comments"] += stripped_line + "\n"

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
                "overall_rating": "Overall Rating /10",
                "mentor_comments": "Mentor Comments"
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
