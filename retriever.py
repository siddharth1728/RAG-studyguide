import chromadb
from sentence_transformers import SentenceTransformer
import uuid

model = SentenceTransformer("all-MiniLM-L6-v2")

class VectorStore:
    def __init__(self, persist_directory="./vectordb"):
        # This creates a folder called 'vectordb' to save documents forever
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(name="study_materials")

    def build(self, chunks):
        """Adds new chunks to the database."""
        if not chunks:
            return

        texts = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        # Generate unique IDs for each chunk
        ids = [str(uuid.uuid4()) for _ in chunks]

        # Generate embeddings
        embeddings = model.encode(texts).tolist()

        # Add to database
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )

    def search(self, query, k=5):
        """Searches the database and returns text + metadata."""
        query_embedding = model.encode([query]).tolist()

        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=k
        )
        
        # Format results nicely
        retrieved = []
        if results['documents']:
            for i in range(len(results['documents'][0])):
                retrieved.append({
                    "text": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i]
                })
                
        return retrieved
        
    def get_document_count(self):
        """Helper to show how many chunks are stored."""
        return self.collection.count()