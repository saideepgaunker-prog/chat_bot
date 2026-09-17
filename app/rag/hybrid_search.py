import re
import math
from typing import List, Dict, Any, Tuple
from collections import Counter
from app.rag.embedding import embedding_service

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "he", "in", "is", "it", "its", "of", "on", "that", "the",
    "to", "was", "were", "will", "with", "where", "can", "i", "how", "do",
    "what", "does", "this", "my"
}

class BM25Index:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus: List[Dict[str, Any]] = []
        self.doc_lengths: List[int] = []
        self.avg_dl: float = 0.0
        self.doc_freqs: Dict[str, int] = Counter()
        self.term_freqs_list: List[Counter] = []

    def _tokenize(self, text: str) -> List[str]:
        tokens = re.findall(r'\b[a-zA-Z0-9_-]+\b', text.lower())
        filtered = [t for t in tokens if t not in STOP_WORDS]
        return filtered if filtered else tokens

    def index(self, documents: List[Dict[str, Any]], text_field: str = "text"):
        self.corpus = documents
        self.doc_lengths = []
        self.doc_freqs = Counter()
        self.term_freqs_list = []

        total_length = 0
        for doc in documents:
            text = doc.get(text_field, "")
            tokens = self._tokenize(text)
            self.doc_lengths.append(len(tokens))
            total_length += len(tokens)
            
            tf = Counter(tokens)
            self.term_freqs_list.append(tf)
            for term in tf.keys():
                self.doc_freqs[term] += 1

        self.avg_dl = (total_length / len(documents)) if documents else 0.0

    def score(self, query: str) -> List[Tuple[int, float]]:
        query_tokens = self._tokenize(query)
        if not query_tokens or not self.corpus:
            return []

        n_docs = len(self.corpus)
        scores = []

        for idx, doc in enumerate(self.corpus):
            score = 0.0
            doc_len = self.doc_lengths[idx]
            tf_map = self.term_freqs_list[idx]

            for term in query_tokens:
                if term not in tf_map:
                    continue
                df = self.doc_freqs.get(term, 0)
                # BM25 IDF
                idf = math.log(1.0 + (n_docs - df + 0.5) / (df + 0.5))
                tf = tf_map[term]
                term_score = idf * ((tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * (doc_len / (self.avg_dl or 1.0)))))
                score += term_score

            scores.append((idx, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

class HybridSearchEngine:
    def __init__(self, rrf_k: int = 60):
        self.rrf_k = rrf_k
        self.bm25 = BM25Index()
        self.documents: List[Dict[str, Any]] = []
        self.embeddings: List[List[float]] = []

    def index(self, documents: List[Dict[str, Any]], text_field: str = "text"):
        self.documents = documents
        self.bm25.index(documents, text_field=text_field)
        self.embeddings = [
            embedding_service.embed_text(doc.get(text_field, ""))
            for doc in documents
        ]

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not self.documents:
            return []

        # 1. BM25 scoring & ranking
        bm25_ranked = self.bm25.score(query)
        bm25_ranks = {doc_idx: rank for rank, (doc_idx, score) in enumerate(bm25_ranked) if score > 0}

        # 2. Dense vector similarity scoring & ranking
        query_vec = embedding_service.embed_text(query)
        vec_scores = []
        for idx, doc_vec in enumerate(self.embeddings):
            sim = embedding_service.cosine_similarity(query_vec, doc_vec)
            vec_scores.append((idx, sim))
        
        vec_scores.sort(key=lambda x: x[1], reverse=True)
        vec_ranks = {doc_idx: rank for rank, (doc_idx, sim) in enumerate(vec_scores) if sim > 0.05}

        # 3. Reciprocal Rank Fusion (RRF)
        combined_scores: Dict[int, float] = {}
        all_candidates = set(bm25_ranks.keys()).union(set(vec_ranks.keys()))
        
        if not all_candidates:
            return [self.documents[idx] for idx, _ in vec_scores[:top_k]]

        for doc_idx in all_candidates:
            rrf_score = 0.0
            if doc_idx in bm25_ranks:
                rrf_score += 1.0 / (self.rrf_k + bm25_ranks[doc_idx] + 1)
            if doc_idx in vec_ranks:
                rrf_score += 1.0 / (self.rrf_k + vec_ranks[doc_idx] + 1)
            combined_scores[doc_idx] = rrf_score

        sorted_indices = sorted(combined_scores.keys(), key=lambda idx: combined_scores[idx], reverse=True)
        
        results = []
        for idx in sorted_indices[:top_k]:
            doc_copy = dict(self.documents[idx])
            doc_copy["_score"] = combined_scores[idx]
            results.append(doc_copy)
        return results
