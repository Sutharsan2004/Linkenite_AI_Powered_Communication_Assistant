import os
import glob
from typing import List, Tuple
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

class SimpleRAG:
    def __init__(self, kb_path: str = "kb", model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.kb_path = kb_path
        self.model = SentenceTransformer(model_name)
        self.docs = []
        self.chunks = []
        self.index = None
        self.build_index()

    def chunk_text(self, text: str, chunk_size: int = 400):
        words = text.split()
        chunk, size = [], 0
        for w in words:
            chunk.append(w)
            size += len(w) + 1
            if size >= chunk_size:
                yield " ".join(chunk)
                chunk, size = [], 0
        if chunk:
            yield " ".join(chunk)

    def build_index(self):
        paths = glob.glob(os.path.join(self.kb_path, "*.md"))
        for p in paths:
            with open(p, "r", encoding="utf-8") as f:
                txt = f.read()
                for ch in self.chunk_text(txt, chunk_size=400):
                    self.chunks.append(ch)
        if not self.chunks:
            self.index = None
            return
        emb = self.model.encode(self.chunks, convert_to_numpy=True, normalize_embeddings=True)
        dim = emb.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(emb)

    def retrieve(self, query: str, k: int = 4) -> List[Tuple[str, float]]:
        if not self.index:
            return []
        q = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
        D, I = self.index.search(q, k)
        out = []
        for d, i in zip(D[0], I[0]):
            out.append((self.chunks[int(i)], float(d)))
        return out
