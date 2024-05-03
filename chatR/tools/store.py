from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings


class FaissEngine:

    def __init__(
            self,
            path: str = "faiss"
    ):
        self.path = path
        self.embedding = HuggingFaceEmbeddings(
            model_name='/home/sentence-transformers/all-MiniLM-L6-v2',
            model_kwargs={'device': 'cuda'}
        )

    # 保存
    def save_vector_store(
            self,
            text_chunks,
            path: str = "faiss"
    ):
        db = FAISS.from_documents(text_chunks, self.embedding)
        db.save_local(path)

    # 加载
    def load_vector_store(
            self,
            directories
    ) -> FAISS:
        vector_store = None
        for directory in directories:
            print(f"Loading faiss engine from {directory}...")
            if vector_store is None:
                vector_store = FAISS.load_local(directory, self.embedding)
            else:
                new_vector_store = FAISS.load_local(directory, self.embedding)
                vector_store.merge_from(new_vector_store)
        return vector_store


faiss_engine = FaissEngine()
