import pandas as pd
import re
from src.logger.logging_config import setup_logging

logger = setup_logging()


class ReportGenerator:
    def parse_llm_response(self, response_text):
        """
        Parses the structured LLM response to extract just the score.
        Expected format: OVERALL SCORE: X/100 (or similar variant).
        The checklist above it serves only as a math scratchpad and is ignored.
        """
        sections = {
            "overall_score": "",
            "category_scores": "",
            "key_strengths": "",
            "critical_issues": "",
            "task_completion": "",
            "summary": ""
        }

        # Grab the X/100 format directly, which bypasses the addition sequence
        match = re.search(r"(\d+(?:\.\d+)?)/100", response_text)
        if match:
            sections["overall_score"] = match.group(1) + "/100"
        else:
            # Fallback if they just put SCORE: X
            match = re.search(r"(?:SCORE|Score).*?(\d{1,3}(?:\.\d+)?)", response_text)
            if match:
                # To avoid picking up the first number of the sum, let's grab all numbers and take the last
                numbers = re.findall(r"\d+(?:\.\d+)?", response_text)
                if numbers:
                    sections["overall_score"] = numbers[-1] + "/100"

        return sections

    def write_evaluation_file(self, results, output_file="evaluation.xlsx"):
        """
        Writes the list of result dictionaries to an Excel file.
        """
        try:
            column_mapping = {
                "student_name": "Name / Repo",
                "github_link": "GitHub Link",
                "repo_found": "Repo Found",
                "files_analyzed": "Files Analyzed",
                "overall_score": "Overall Score (/100)"
            }

            df = pd.DataFrame(results)

            if df.empty:
                logger.warning("No results to write to Excel.")
                return

            # Normalise: if 'label' exists but not 'student_name', use it
            if "student_name" not in df.columns and "label" in df.columns:
                df["student_name"] = df["label"]

            rename_map = {k: v for k, v in column_mapping.items() if k in df.columns}
            df = df.rename(columns=rename_map)

            desired_columns = [v for v in column_mapping.values()]
            df = df[[col for col in desired_columns if col in df.columns]]

            df.to_excel(output_file, index=False)
            logger.info(f"Successfully wrote results to {output_file}")
        except Exception as e:
            logger.error(f"Error writing to Excel: {e}")
