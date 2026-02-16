import nbformat
import requests
from config import CONFIG

IMPORTANT_KEYWORDS = CONFIG['IMPORTANT_KEYWORDS']

def is_important(cell_text):
    return any(keyword in cell_text.lower() for keyword in IMPORTANT_KEYWORDS)

def is_important(cell_text):
    return any(keyword in cell_text.lower() for keyword in IMPORTANT_KEYWORDS)

def parse_notebook_from_url(url):
    """
    Downloads a notebook from a URL and converts it to a filtered text string.
    Uses smart filtering and token budget strategy.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        nb = nbformat.reads(response.text, as_version=4)
        
        MAX_CHARS = CONFIG['MAX_NOTEBOOK_CHARS']
        current_size = 0
        text = ""
        
        for cell in nb.cells:
            if cell.cell_type == "markdown":
                # Keep markdown short
                if len(cell.source) < 500:
                    cell_text = f"[MARKDOWN]\n{cell.source}\n\n"
                    if current_size + len(cell_text) > MAX_CHARS:
                        break
                    text += cell_text
                    current_size += len(cell_text)
                    
            elif cell.cell_type == "code":
                # Skip very long cells
                if len(cell.source) > 1500:
                    continue
                
                # Keep only important DS cells
                if is_important(cell.source):
                    cell_text = f"[CODE]\n{cell.source}\n\n"
                    if current_size + len(cell_text) > MAX_CHARS:
                        break
                    text += cell_text
                    current_size += len(cell_text)
                
        return text
    except Exception as e:
        raise Exception(f"Error parsing notebook: {e}")
