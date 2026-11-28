import math
from typing import Any

from pymongo import MongoClient
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS


def preprocess(text: str) -> list[str]:
    """Lowercase and split text into tokens, removing English stop words."""
    return [t for t in text.lower().split() if t not in ENGLISH_STOP_WORDS]


def compute_k(k1: float, b: float, dl: float, avdl: float) -> float:
    """Compute BM25 document length normalization: K = k1 * ((1 - b) + b * (dl / avdl))"""
    if avdl <= 0: return k1
    return k1 * ((1.0 - b) + b * (dl / avdl))


def compute_bm25_unlabeled_idf(numDocs: int, docFreq: int) -> float:
    """Compute BM25 IDF-like weight when no relevance labels are available (r_i = 0, R = 0): 
        log( ((0 + 0.5) / (0 - 0 + 0.5)) / ((n_i - 0 + 0.5) / (N - n_i - 0 + 0 + 0.5)) )"""
    if numDocs <= 0 or docFreq <= 0 or docFreq >= numDocs: return 0.0    
    numerator = 0.5 / 0.5
    noRelProp = (docFreq + 0.5) / (numDocs - docFreq + 0.5)
    if noRelProp <= 0: return 0.0
    return math.log(numerator / noRelProp)


def compute_doc_tf_component(tf: float, k1: float, kNorm: float) -> float:
    """Document term-frequency component: ((k1 + 1) * f_i) / (K + f_i)."""
    denom = kNorm + tf
    if denom <= 0: return 0.0
    return ((k1 + 1.0) * tf) / denom


def compute_query_tf_component(qf: float, k2: float) -> float:
    """Query term-frequency component: ((k2 + 1) * qf_i) / (k2 + qf_i)."""
    denom = k2 + qf
    if denom <= 0: return 0.0
    return ((k2 + 1.0) * qf) / denom


def extract_tf_from_posting(posting: dict[str, Any]) -> float:
    """Extract term frequency f_i from a posting dictionary."""
    if "tf" in posting and posting["tf"] is not None: return float(posting["tf"])
    positions = posting.get("positions")
    if isinstance(positions, list) and len(positions) > 0: return float(len(positions))
    return 1.0


class SlideBM25Ranker:
    """BM25 ranker using `documents` and `inverted_index` collections in MongoDB."""

    def __init__(self, documents_collection: Any, index_collection: Any, k1: float = 1.2, k2: float = 100.0, b: float = 0.75, content_field: str = "content") -> None:
        self.documents_col = documents_collection
        self.index_col = index_collection
        self.k1 = k1
        self.k2 = k2
        self.b = b
        self.content_field = content_field

    def corpus_stats(self) -> tuple[int, float, dict[Any, float], dict[Any, dict[str, Any]]]:
        """Load documents to get N, avdl, per-document length dl, and docs by _id."""
        docs = list(self.documents_col.find({}))
        numDocs = len(docs)
        if numDocs == 0: return 0, 0.0, {}, {}

        docLengths: dict[Any, float] = {}
        docsBy_id: dict[Any, dict[str, Any]] = {}
        totalLen = 0.0

        for doc in docs:
            docId = doc.get("_id")
            docsBy_id[docId] = doc
            rawText = doc.get(self.content_field, "")
            dl = float(len(preprocess(rawText))) if isinstance(rawText, str) else 0.0
            docLengths[docId] = dl
            totalLen += dl

        avdl = totalLen / numDocs if numDocs > 0 else 0.0
        return numDocs, avdl, docLengths, docsBy_id

    def rank(self, query: str, top_k: int | None = None) -> list[dict[str, Any]]:
        """Compute BM25 scores for `query` against `inverted_index`, fetch matching documents from `documents` by `docId`, and return results ordered by descending score."""
        queryTokens = preprocess(query)
        if not queryTokens: return []

        queryTFmap: dict[str, float] = {}
        for token in queryTokens: queryTFmap[token] = queryTFmap.get(token, 0.0) + 1.0

        numDocs, avdl, docLengths, docsBy_id = self.corpus_stats()
        if numDocs == 0: return []

        scores: dict[Any, float] = {}

        for term, qf in queryTFmap.items():
            indexDoc = self.index_col.find_one({"term": term})
            if not indexDoc: continue

            postings = indexDoc.get("postings", [])
            idf = compute_bm25_unlabeled_idf(numDocs, len(postings))
            qComp = compute_query_tf_component(qf, self.k2)

            for posting in postings:
                docId = posting.get("docId")
                if docId not in docsBy_id: continue

                tf = extract_tf_from_posting(posting)
                dl = docLengths.get(docId, avdl)
                kNorm = compute_k(self.k1, self.b, dl, avdl)
                dComp = compute_doc_tf_component(tf, self.k1, kNorm)
                scores[docId] = scores.get(docId, 0.0) + (idf * dComp * qComp)

        rankedIds = sorted(scores.keys(), key=lambda did: scores[did], reverse=True)
        if top_k is not None: rankedIds = rankedIds[:top_k]

        results: list[dict[str, Any]] = []
        for docId in rankedIds: results.append({"docId": docId, "score": scores[docId], "document": docsBy_id[docId]})
        return results


if __name__ == "__main__":
    client = MongoClient("mongodb://localhost:27017/")
    db = client["CS4250WebScraper"]
    ranker = SlideBM25Ranker(documents_collection=db["documents"], index_collection=db["inverted_index"])
    for rankPos, item in enumerate(ranker.rank("ecology"), start=1): print(f"{rankPos}. docId={item['docId']} score={item['score']:.4f}")