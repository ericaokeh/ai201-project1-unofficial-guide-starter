"""
Milestone 4: embed my chunks and store them in ChromaDB.

Takes the chunks from ingest.py, turns each one into a vector with
all-MiniLM-L6-v2, and saves them to a Chroma collection along with the
metadata I'll need later for source attribution.

Run it with:  python embed.py
"""

import math
import re
from collections import Counter
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from ingest import build_chunks

MODEL_NAME = "all-MiniLM-L6-v2"
DB_DIR = Path("chroma_db")
COLLECTION_NAME = "italian_greyhounds"


# Every document in my collection is about Italian Greyhounds, so the breed
# name appears everywhere and tells you nothing about which chunk you want.
# It behaves like a stopword here: leaving it in, a question about crating
# matches whichever chunk says "Italian Greyhound" most often rather than the
# chunk about crates. Taking it out moved my weight question from rank 20 to
# rank 2.
BREED_WORDS = re.compile(
    r"\b(an?\s+)?(italian greyhounds?|iggys?|igs?|sighthounds?)\b", re.I
)


def normalise(text):
    """Drop the breed name, since every chunk is about the same breed."""
    text = BREED_WORDS.sub(" ", text)
    return re.sub(r"\s{2,}", " ", text).strip()


# The same dilution that hurt oversized chunks also hurts long questions: an
# embedding is an average over every token, so framing words drag the query
# vector away from what the question is actually about. "What reason do rescue
# groups give for saying a crate is not cruel?" spends eleven of its seventeen
# words on scaffolding, and retrieved the answer at rank 20; "Is crating
# cruel?" retrieves it at rank 1. These patterns strip the scaffolding and
# leave the content words.
QUERY_SCAFFOLD = [
    re.compile(p, re.I) for p in (
        r"^\s*(so|and|ok(ay)?|hi|hello)\b[,\s]*",
        r"\b(what|which)\s+(reason|reasons|justification)\s+"
        r"(do|does|did)\b.*?\bgive\s+for\s+(saying|claiming)\b",
        r"\b(can|could)\s+you\s+(please\s+)?(tell\s+me|explain|say)\b",
        r"\bi\s+(would\s+like|want|need)\s+to\s+know\b",
        r"\b(what|how)\s+do\s+(rescue\s+groups|rescues|owners|breeders|"
        r"vets|sources|the\s+documents)\s+say\s+(about|for)\b",
        r"\baccording\s+to\s+(the\s+)?(documents|sources|rescue\s+groups)\b",
        r"\bplease\b",
    )
]


def normalise_query(text):
    """Normalise a question: breed name out, framing words out.

    Only used on the query side. The chunks never contain this kind of
    scaffolding, so there is nothing to strip from them.
    """
    for pattern in QUERY_SCAFFOLD:
        text = pattern.sub(" ", text)
    return normalise(text)


def load_model():
    """Load the embedding model.

    This downloads the model the first time it runs (about 90 MB) and then
    keeps a local copy. After that it works with no internet and no API key.
    """
    print(f"Loading {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    print(f"  vector size: {model.get_embedding_dimension()}")
    print(f"  max input: {model.max_seq_length} tokens")
    return model


def build_store(rebuild=True):
    chunks = build_chunks()
    if not chunks:
        return None

    model = load_model()

    # Chroma saves to disk here, so I only have to embed once.
    client = chromadb.PersistentClient(path=str(DB_DIR))

    if rebuild:
        # Start fresh, otherwise re-running this adds everything a second time.
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"\nCleared the old '{COLLECTION_NAME}' collection")
        except Exception:
            pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        # Cosine similarity is the right measure for this model. The default
        # is squared L2 distance, which gives different rankings.
        metadata={"hnsw:space": "cosine"},
    )

    texts = [chunk["text"] for chunk in chunks]

    # Embed the body without the source label on the front -- see the note in
    # ingest.chunk_text. The full text with the label is what gets stored and
    # shown; only the vector is built from the body.
    bodies = [normalise(chunk["body"]) for chunk in chunks]

    print(f"\nEmbedding {len(bodies)} chunks...")
    vectors = model.encode(bodies, show_progress_bar=True, batch_size=32)

    # Metadata. The assignment asks for at least the source document name
    # and the chunk's position in that document. I also keep the length,
    # which is handy when I'm checking retrieval results.
    position_in_doc = {}
    metadatas, ids = [], []

    for chunk in chunks:
        filename = chunk["filename"]
        position = position_in_doc.get(filename, 0)
        position_in_doc[filename] = position + 1

        metadatas.append({
            "source": chunk["source"],        # readable name, for attribution
            "filename": filename,             # which file it came from
            "position": position,             # where it sits in that document
            "length": len(chunk["text"]),
        })
        ids.append(f"{Path(filename).stem}_{position}")

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=[v.tolist() for v in vectors],
        metadatas=metadatas,
    )

    print(f"\nStored {collection.count()} chunks in {DB_DIR}/")
    return collection


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

# Loaded once and reused. Loading the model takes a few seconds, so I don't
# want to do it on every single search.
_model = None
_collection = None


def get_collection():
    """Open the saved Chroma collection."""
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=str(DB_DIR))
        _collection = client.get_collection(COLLECTION_NAME)
    return _collection


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def _semantic_results(query):
    """Return every chunk in semantic-rank order with its real distance."""
    collection = get_collection()
    query_vector = get_model().encode(normalise_query(query)).tolist()
    raw = collection.query(
        query_embeddings=[query_vector],
        n_results=collection.count(),
        include=["documents", "metadatas", "distances"],
    )

    results = []
    for chunk_id, text, meta, distance in zip(
        raw["ids"][0], raw["documents"][0], raw["metadatas"][0],
        raw["distances"][0],
    ):
        results.append({
            "id": chunk_id,
            "text": text,
            "source": meta["source"],
            "filename": meta["filename"],
            "position": meta["position"],
            "distance": round(distance, 3),
            "similarity": round(1 - distance, 3),
        })
    return results


def semantic_search(query, k=5):
    """Semantic-only retrieval, kept so hybrid results can be compared."""
    return _semantic_results(query)[:k]


def _tokens(text):
    """Lowercase words used by the small in-memory BM25 index."""
    return re.findall(r"[a-z0-9]+", normalise(text).lower())


def _bm25_scores(query, results, k1=1.5, b=0.75):
    """Score the stored chunks with BM25; the corpus is only ~300 chunks."""
    documents = [_tokens(hit["text"].split(": ", 1)[-1]) for hit in results]
    query_terms = set(_tokens(normalise_query(query)))
    if not query_terms or not documents:
        return [0.0] * len(documents)

    average_length = sum(map(len, documents)) / len(documents)
    document_frequency = {
        term: sum(term in document for document in documents)
        for term in query_terms
    }
    scores = []
    for document in documents:
        counts = Counter(document)
        score = 0.0
        for term in query_terms:
            frequency = counts[term]
            if not frequency:
                continue
            inverse_frequency = math.log(
                1 + (len(documents) - document_frequency[term] + 0.5)
                / (document_frequency[term] + 0.5)
            )
            length_adjustment = frequency + k1 * (
                1 - b + b * len(document) / average_length
            )
            score += inverse_frequency * frequency * (k1 + 1) / length_adjustment
        scores.append(score)
    return scores


def search(query, k=5):
    """Combine semantic and BM25 rankings with reciprocal rank fusion.

    Semantic search handles paraphrases; BM25 promotes chunks containing rare
    exact terms. Each result keeps its real cosine distance so the generation
    layer can apply the same relevance cutoff after fusion.

    Returns a list of dicts, most relevant first:
        {"text", "source", "filename", "position", "similarity"}
    """
    semantic = _semantic_results(query)
    semantic_rank = {hit["id"]: rank for rank, hit in enumerate(semantic, 1)}

    keyword_scores = _bm25_scores(query, semantic)
    keyword_order = sorted(
        range(len(semantic)), key=lambda index: keyword_scores[index], reverse=True
    )
    keyword_rank = {
        semantic[index]["id"]: rank
        for rank, index in enumerate(keyword_order, 1)
        if keyword_scores[index] > 0
    }

    # RRF avoids trying to compare cosine distances and BM25 scores directly.
    # 60 is the conventional smoothing constant and keeps either ranker from
    # dominating because of one unusually strong raw score.
    for hit in semantic:
        score = 1 / (60 + semantic_rank[hit["id"]])
        if hit["id"] in keyword_rank:
            score += 1 / (60 + keyword_rank[hit["id"]])
        hit["fusion_score"] = round(score, 6)

    return sorted(semantic, key=lambda hit: hit["fusion_score"], reverse=True)[:k]


def print_results(query, k=5):
    """Run a search and print it in a readable way."""
    print("=" * 62)
    print(f"QUERY: {query}   (top {k})")
    print("=" * 62)

    for n, hit in enumerate(search(query, k), start=1):
        print(f"\n{n}. [{hit['similarity']}] {hit['source']} "
              f"(chunk {hit['position']})")
        # Strip the source label off the front so the preview shows the
        # actual text.
        body = hit["text"].split(": ", 1)[-1].replace("\n\n", " ")
        print(f"   {body[:220]}...")


def show_what_was_stored(collection, how_many=3):
    """Print a few stored records so I can check the metadata is right."""
    sample = collection.get(limit=how_many, include=["documents", "metadatas"])

    print("\n" + "=" * 62)
    print("WHAT GOT STORED")
    print("=" * 62)

    for chunk_id, document, meta in zip(
        sample["ids"], sample["documents"], sample["metadatas"]
    ):
        print(f"\nid:       {chunk_id}")
        print(f"source:   {meta['source']}")
        print(f"filename: {meta['filename']}")
        print(f"position: {meta['position']} in that document")
        print(f"text:     {document[:120]}...")


if __name__ == "__main__":
    import sys

    # "python embed.py <question>" searches the store I already built.
    # "python embed.py" rebuilds it from scratch.
    if len(sys.argv) > 1:
        print_results(" ".join(sys.argv[1:]))
    else:
        collection = build_store()
        if collection:
            show_what_was_stored(collection)
