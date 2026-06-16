from langchain_text_splitters import RecursiveCharacterTextSplitter

def create_chunks(pages_data):
    """Splits text while maintaining source and page metadata."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )
    
    chunks = []
    
    for page in pages_data:
        splits = splitter.split_text(page["text"])
        
        for split in splits:
            chunks.append({
                "text": split,
                "metadata": page["metadata"]
            })
            
    return chunks