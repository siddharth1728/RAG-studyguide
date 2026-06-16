import fitz

def extract_text(pdf_path, filename):
    """Extracts text page-by-page and attaches metadata."""
    pages_data = []
    
    doc = fitz.open(pdf_path)
    
    for page_num, page in enumerate(doc, start=1):
        pages_data.append({
            "text": page.get_text(),
            "metadata": {
                "source": filename,
                "page": page_num
            }
        })
        
    return pages_data