# Project 1 Planning: The Unofficial Guide

## Domain

My domain is day-to-day care and ownership of Italian Greyhounds. Practical information about housetraining, health, temperature, diet, and living with other pets is valuable but scattered across rescue and veterinary sites rather than collected in one official guide.

## Documents

| # | Source | Topic |
|---:|---|---|
| 1 | Italian Greyhound Rescue Foundation | Diet |
| 2 | Mid-Atlantic Iggy Rescue | Housetraining |
| 3 | Southern Cross Vet | Health issues |
| 4 | Houndtees | Keeping sighthounds warm |
| 5 | Dimensions.com | Size |
| 6 | Italian Greyhound Rescue Foundation | Color and patterns |
| 7 | Italian Greyhound Rescue Foundation | General care |
| 8 | Italian Greyhound Rescue Charity | Exercise |
| 9 | Iggy Rescue | Compatibility with other pets |
| 10 | Adopt-a-Pet | Barking |

The exact URLs are listed in README.md. Each page is saved as a plain-text file in `documents/`.

## Chunking Strategy

**Initial plan:** recursive splitting at paragraph and sentence boundaries, using 1,000 characters with 150 characters of overlap. I expected one section-sized chunk to retain complete ideas without cutting sentences.

**Implementation update:** retrieval testing showed that large chunks diluted individual facts. I changed the target to **200 characters with 30 characters of overlap**, kept headings with their following text, and embedded only the body rather than the repeated source label. The final pipeline produces **282 chunks**. The README contains the comparison and sample chunks.

## Retrieval Approach

The embedding model is `all-MiniLM-L6-v2` through sentence-transformers. It runs locally, has no API cost, and stores 384-dimensional vectors in ChromaDB using cosine distance. Generation receives up to **8** chunks; this fits the short final chunks, while a 0.85 semantic-distance cutoff removes very weak matches.

For production I would compare domain accuracy, context length, multilingual support, latency, privacy, and API cost before choosing a larger hosted model.

**Stretch update — Hybrid Search:** After semantic-only search missed the exact crating explanation, I added BM25 keyword ranking and reciprocal rank fusion. A separate semantic-only function preserves the baseline for comparison. Keyword-promoted chunks retain their cosine distances and must pass the same generation cutoff.

## Evaluation Plan

| # | Question | Expected answer |
|---:|---|---|
| 1 | Do Italian Greyhounds bark a lot? | Generally quiet, though they may bark when excited, nervous, or seeking attention |
| 2 | What are the early signs of Progressive Retinal Atrophy? | Night blindness and dilated pupils; gradual genetic blindness with no known treatment |
| 3 | Why is it bad for an Italian Greyhound to be overweight? | Organ strain, shorter life expectancy, and greater fracture and orthopedic risk |
| 4 | Why do rescue groups say a crate is not cruel? | Dogs are den animals and should have their own “room” |
| 5 | How tall and heavy is a typical Italian Greyhound? | 13–15 inches at the withers and 7–14 pounds |

## Anticipated Challenges

1. Site menus, ads, banners, and footers may become irrelevant chunks unless cleaning removes them.
2. Important facts may cross chunk boundaries or become diluted inside chunks that are too large.
3. Similar sources may disagree, so the model must report real conflicts rather than merge them.
4. Chroma always returns nearest neighbors, even for unsupported questions, so the generator needs grounding and refusal rules.
5. Keyword retrieval may promote exact-word matches that are not semantically relevant.

## Architecture

```text
documents/*.txt
      |
      v
Ingestion and cleaning (Python: pathlib, regex, html)
      |
      v
Recursive chunking (200 characters, 30 overlap)
      |
      v
Embedding (all-MiniLM-L6-v2) -> ChromaDB
      |
      v
Hybrid retrieval (cosine + BM25 -> reciprocal rank fusion, top 8)
      |
      v
Grounded generation (Groq, citations and refusal rules)
      |
      v
Gradio interface (question, answer, retrieved sources)
```

## AI Tool Plan

1. **Ingestion and chunking:** Give the AI the Documents and Chunking Strategy sections and request functions that load text files, remove site furniture, retain source metadata, and split recursively. I will inspect sample chunks and revise cleaning or chunk size based on retrieval tests.
2. **Embedding and retrieval:** Give the AI the Retrieval Approach and chunk output format and request Chroma storage and a function returning ranked chunks with source metadata and distances. I will test at least three evaluation questions before generation.
3. **Generation and interface:** Give the AI the grounding, refusal, citation, and output requirements and request a Groq generation function plus a Gradio page. I will verify that sources are constructed from retrieved metadata rather than invented by the model.
4. **Stretch feature:** Give the AI the failed-query ranks and ask for ways to combine semantic and keyword retrieval. I will preserve the semantic baseline, measure the comparison, and ensure keyword results cannot bypass the distance cutoff.
