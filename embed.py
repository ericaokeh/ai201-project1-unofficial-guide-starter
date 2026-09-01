"""
Milestone 4: embed my chunks and store them in ChromaDB.

Takes the chunks from ingest.py, turns each one into a vector with
all-MiniLM-L6-v2, and saves them to a Chroma collection along with the
metadata I'll need later for source attribution.

Run it with:  python embed.py
"""

import re
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


def search(query, k=5):
    """Find the k chunks closest in meaning to the query.

    The query gets turned into a vector by the same model that embedded the
    chunks, which is what lets this match on meaning instead of on shared
    words -- "is my dog too skinny" can find a chunk about weight without
    either one using the other's wording.

    Returns a list of dicts, most relevant first:
        {"text", "source", "filename", "position", "similarity"}
    """
    collection = get_collection()

    # The query goes through the same treatment as the chunks did, otherwise
    # I'd be comparing text that still says "Italian Greyhound" against
    # chunks where I removed it.
    query_vector = get_model().encode(normalise(query)).tolist()

    raw = collection.query(
        query_embeddings=[query_vector],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    results = []
    for text, meta, distance in zip(
        raw["documents"][0], raw["metadatas"][0], raw["distances"][0]
    ):
        results.append({
            "text": text,
            "source": meta["source"],
            "filename": meta["filename"],
            "position": meta["position"],
            # Chroma gives me cosine distance, where 0 means identical and
            # bigger numbers mean less alike. I keep that, and also flip it
            # round into a similarity score that goes up as the match gets
            # better, because that reads more naturally.
            "distance": round(distance, 3),
            "similarity": round(1 - distance, 3),
        })

    return results


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
