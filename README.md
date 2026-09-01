# The Unofficial Italian Greyhound Guide

A RAG question-answering system grounded in 10 saved rescue, veterinary, and owner-guide pages about living with an Italian Greyhound.

**Repository:** https://github.com/ericaokeh/ai201-project1-unofficial-guide-starter

**Demo video:** https://drive.google.com/file/d/1TmVIU1ycSrH6cPZVJlqd9Xi_Y38MUi8F/view?usp=sharing

## Run It

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # then add GROQ_API_KEY
python embed.py            # build the vector store
python app.py              # open http://localhost:7860
```

## Domain and Documents

The domain is day-to-day Italian Greyhound ownership: health, diet, housetraining, exercise, temperature, barking, appearance, and compatibility with other pets. This practical information is valuable but scattered across rescue and veterinary sites rather than collected in one official guide.

| # | Source | Topic | URL |
|---|---|---|---|
| 1 | Italian Greyhound Rescue Foundation | Diet | https://www.igrescue.com/html/basics/diet_for_italian_greyhounds.shtml |
| 2 | Mid-Atlantic Iggy Rescue | Housetraining | https://www.midatlanticiggyrescue.com/ig-helptraining/housetraining/ |
| 3 | Southern Cross Vet | Health issues | https://southerncrossvet.com.au/10-italian-greyhound-common-health-issues/ |
| 4 | Houndtees | Keeping sighthounds warm | https://houndtees.com.au/en-us/blogs/blog/how-to-tell-if-your-sighthound-is-cold-how-to-keep-them-warm |
| 5 | Dimensions.com | Size | https://www.dimensions.com/element/italian-greyhound |
| 6 | Italian Greyhound Rescue Foundation | Color and patterns | https://www.igrescue.com/html/basics/coloration_&_patterns.shtml |
| 7 | Italian Greyhound Rescue Foundation | General care | https://www.igrescue.com/html/basics/caring_for_iggys.shtml |
| 8 | Italian Greyhound Rescue Charity | Exercise | https://italiangreyhoundrescuecharity.org.uk/about-italian-greyhounds/exercise/ |
| 9 | Iggy Rescue | Other pets | https://www.iggyrescue.com/html/basics/other_pets_&_italian_greyhounds.shtml |
| 10 | Adopt-a-Pet | Barking | https://www.adoptapet.com/answers/do-italian-greyhounds-bark-a-lot |

The pages are saved as plain text in `documents/`. `ingest.py` decodes HTML entities, removes tags, menus, cookie text, ads, footers, repeated banners, duplicates, and fragments, then preserves article text and source metadata.

## Chunking Strategy

The final strategy uses recursive splitting at paragraph and sentence boundaries, with a target of **200 characters** and **30 characters of overlap**. Headings are kept with the text that follows them. This fits the sources because important facts are often one or two sentences; larger section-sized chunks diluted those facts during embedding.

| Target size | Total chunks | Test answers retrieved in top 5 |
|---|---:|---:|
| **200** | **282** | **5/5** |
| 450 | 162 | 5/5 |
| 600 | 118 | 4/5 |
| 1,000 | 76 | 4/5 |

The final corpus contains **282 chunks** from 54,558 cleaned characters. Stored chunks include a source label for display, but only their body text is embedded so repeated source names do not distort similarity.

## Sample Chunks

1. **Adopt-a-Pet — Barking:** “No, Italian Greyhounds are generally not excessive barkers. They tend to be relatively quiet and are not as vocal as some other breeds.”
2. **Southern Cross Vet — Health:** “While there are currently no known treatments for Progressive Retinal Atrophy (PRA), signs that an Italian Greyhound may suffer from Retinal Atrophy include night blindness and dilated pupils.”
3. **IG Rescue Foundation — Diet:** “IGs are not built to carry extra weight. Extra weight puts more workload on their vital organs, thereby decreasing their life expectancy.”
4. **Mid-Atlantic Iggy Rescue — Housetraining:** “Crating is not cruel as dogs are den animals and should have their own ‘room’.”
5. **Houndtees — Warmth:** “If your hound’s ears are cold to the touch, they’ll be feeling cold all over!”

## Embedding and Retrieval

Chunks are embedded locally with `all-MiniLM-L6-v2` and stored in ChromaDB using cosine distance. The model produces 384-dimensional vectors and has a 256-token limit; chunk bodies measure 7–77 tokens, averaging 34.7, so none are truncated.

For production, I would compare embedding accuracy on breed-specific terminology, context length, multilingual support, latency, privacy, and API cost. A larger hosted model could improve accuracy and language coverage, while MiniLM is free, fast, private, and works offline.

### Hybrid Search Stretch Feature

`embed.py` ranks chunks with both Chroma semantic similarity and in-memory BM25 keyword scoring, then combines the rankings with reciprocal rank fusion. Semantic search handles paraphrases; BM25 helps rare exact terms. Keyword-promoted results retain their real cosine distance, so the generation layer’s 0.85 cutoff still applies.

### Retrieval Tests

Distances below are cosine distance; lower is more similar. Results are listed in hybrid rank order.

**Query 1: “Do Italian Greyhounds bark a lot?”**

| Rank | Distance | Returned chunk |
|---:|---:|---|
| 1 | 0.346 | Adopt-a-Pet chunk 0: generally not excessive barkers |
| 2 | 0.299 | Adopt-a-Pet chunk 1: may bark when excited, nervous, or seeking attention |
| 3 | 0.481 | Housetraining chunk 54: barking as a signal |

The first two chunks directly provide the answer and qualification. The third mentions barking but does not directly answer how often the breed barks.

**Query 2: “What are the early signs of Progressive Retinal Atrophy?”**

| Rank | Distance | Returned chunk |
|---:|---:|---|
| 1 | 0.246 | Southern Cross Vet chunk 14: night blindness and dilated pupils |
| 2 | 0.251 | Southern Cross Vet chunk 11: identifies PRA |
| 3 | 0.696 | Southern Cross Vet chunk 27: signs of hypothyroidism |

The first two chunks directly support the answer. The third is a weak keyword match about another condition, showing that hybrid retrieval can also promote irrelevant passages.

**Query 3: “How can I tell if my Italian Greyhound is cold?”**

| Rank | Distance | Returned chunk |
|---:|---:|---|
| 1 | 0.408 | Houndtees chunk 8: check the dog’s ears |
| 2 | 0.563 | Houndtees chunk 2: introduction to signs and warming |
| 3 | 0.557 | Houndtees chunk 5: cold ears indicate the dog feels cold |

All three come from the relevant temperature guide; two contain direct evidence and one introduces the section.

## Grounded Generation

`generate.py` sends up to eight retrieved chunks to Groq. Grounding is enforced by:

- A system prompt requiring answers only from retrieved text.
- A citation after each factual claim.
- An explicit refusal when the context does not answer the question.
- A 0.85 cosine-distance cutoff before generation.
- A programmatic source list and citation checker.

### Example Responses

**Covered question:** “How can I tell if my Italian Greyhound is cold?”

> Cold ears and cold paw pads indicate that the dog needs warming, and a body that feels cool rather than warm suggests the dog is chilly [2][3][5].

The displayed sources identify the numbered Houndtees chunks, positions, and distances.

**Covered question:** “Do Italian Greyhounds get along with cats?”

> It depends on the individual animals. Some Italian Greyhounds chase cats, some are afraid after bad experiences, and some live harmoniously with them [1][4][6]. A cat’s personality and history with other animals also matter [5].

The displayed sources point to the Iggy Rescue other-pets page.

**Out-of-scope question:** “What is the capital of France?”

> The documents I have don’t cover that. They’re about Italian Greyhound care: diet, health problems, housetraining, exercise, keeping them warm, and how they get on with other pets.

All eight candidates exceed the distance cutoff, so the model is not called.

## Query Interface

`app.py` provides a Gradio question textbox and Ask button, an answer box containing inline citations, and a source box containing source names, filenames, chunk positions, distances, and citation-use markers.

```text
Question: Do Italian Greyhounds bark a lot?
Answer: They are generally quiet, although they may bark when excited,
nervous, or seeking attention [1][2].
Retrieved from: Adopt-a-Pet chunks 0 and 1, with distances shown.
```

## Evaluation Report

These responses were recorded after the required semantic-retrieval and prompt fixes, before adding the later hybrid-search stretch feature.

| # | Question | Expected answer | Recorded response summary | Judgment |
|---:|---|---|---|---|
| 1 | Do Italian Greyhounds bark a lot? | Generally quiet; may bark from excitement, nervousness, or attention-seeking | Returned both the general answer and exceptions with citations | Accurate |
| 2 | What are the early signs of PRA? | Night blindness and dilated pupils; gradual genetic blindness | Returned the signs and gradual decline with citations | Accurate |
| 3 | Why is being overweight bad? | Organ strain, shorter life, and greater fracture and orthopedic risk | Returned organ, bone, joint, and fracture risks with citations | Accurate |
| 4 | Why do rescues say a crate is not cruel? | Dogs are den animals and should have their own room | Returned the den-animal explanation with a citation | Accurate |
| 5 | How tall and heavy is a typical IG? | 13–15 in at the withers and 7–14 lb | Returned both measurements and distinguished standing height | Accurate |

**Recorded score:** 5 accurate, 0 partially accurate, 0 inaccurate. The first run scored 3 accurate and 2 partially accurate; those failures produced the fixes below.

## Failure Case

The crating question originally failed at retrieval. The chunk containing “dogs are den animals” ranked 20th, outside the six chunks sent to the model, so the answer discussed positive crate training without giving the requested reason.

Removing query scaffolding moved the chunk to semantic rank 7. Hybrid retrieval then combined semantic and BM25 rankings and moved it to rank 4. Semantic retrieval captures meaning, while BM25 gives weight to the rare exact word “cruel.”

Hybrid search still has a limitation: keyword matches can promote a passage that shares a word but discusses another subject, as shown by the hypothyroidism passage in the PRA test. The retained cosine distance makes weak matches visible, and the grounding prompt tells the model to use only passages that answer the question.

## Spec Reflection

The spec helped by defining five expected answers before implementation, giving me a fixed set for comparing chunk sizes and retrieval changes. Implementation diverged from the original 1,000-character, 150-overlap plan because testing showed that 200-character chunks with 30 overlap retrieved specific facts more reliably.

## AI Usage

1. I gave an AI tool my document formats and chunking plan and asked for ingestion and recursive chunking functions. I revised its cleaning rules, fixed paragraph handling, added repeated-banner detection, and changed the chunk size after measuring retrieval.
2. I gave an AI tool the grounding and attribution requirements and asked for generation and interface code. I strengthened the prompt, generated the source list programmatically, and added citation validation rather than trusting the model’s formatting.
3. For the failed crating query, I supplied the measured semantic ranks and requested retrieval alternatives. I kept a semantic-only baseline, implemented BM25 plus reciprocal rank fusion, preserved the semantic cutoff, and documented the rank-7 versus rank-4 comparison.
