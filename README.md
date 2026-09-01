# The Unofficial Italian Greyhound Guide

A RAG question-answering system grounded in 10 saved rescue, veterinary, and owner-guide pages about living with an Italian Greyhound.

**Repository:** https://github.com/ericaokeh/ai201-project1-unofficial-guide-starter

**Demo video:** https://drive.google.com/file/d/1TmVIU1ycSrH6cPZVJlqd9Xi_Y38MUi8F/view?usp=sharing

The video demonstrates these three queries with citations and retrieved sources visible:

1. **“What are the early signs of Progressive Retinal Atrophy in an Italian Greyhound?”** — the strong retrieval example.
2. **“Do Italian Greyhounds get along with cats?”** — a grounded answer that preserves the source’s qualifications.
3. **“What reason do rescue groups give for saying a crate is not cruel for an Italian Greyhound?”** — the documented retrieval failure and hybrid-search improvement.

The metadata-filtering and conversational-memory stretch features are demonstrated in the source and documented under Query Interface; they are not shown in this video.

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

I compared semantic-only and hybrid retrieval on four queries:

| Query | Semantic-only result | Hybrid result | Better method |
|---|---|---|---|
| Barking | Top 3: direct qualification, direct answer, housetraining signal | Same three chunks, with the direct answer moved to rank 1 | Tie; hybrid ordering is slightly clearer |
| PRA signs | Top 3: symptoms, PRA heading, gradual blindness | Top 3: symptoms, PRA heading, unrelated hypothyroidism signs | Semantic; its third result remains relevant |
| Crating reason | Correct “den animals” chunk at rank 7 | Correct chunk at rank 4 | Hybrid; the needed evidence enters the top results |
| Overweight risk | Correct “vital organs” and “not built to carry weight” chunks at ranks 1 and 2 | Correct chunks fall to ranks 10 and 15 | Semantic; hybrid keyword matches displace the answer |

Hybrid search therefore fixes the crating failure but is not universally better. The comparison also exposed the current overweight failure documented below.

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

**Covered question:** “Do Italian Greyhounds bark a lot?”

> Italian Greyhounds are generally not excessive barkers and are relatively quiet compared with many other breeds [1]. However, like all dogs they may bark when they are excited, nervous, or seeking attention [2].

- [1] Adopt-a-Pet — Do Italian Greyhounds Bark a Lot?, chunk 0, distance 0.346
- [2] Adopt-a-Pet — Do Italian Greyhounds Bark a Lot?, chunk 1, distance 0.299

**Covered question:** “Why do rescue groups say a crate is not cruel?”

> Rescue groups say crating isn’t cruel because dogs are den-type animals and naturally benefit from having their own “room” to retreat to [4].

- [4] Mid-Atlantic Iggy Rescue — Housetraining, chunk 37, distance 0.480

**Out-of-scope question:** “What is the capital of France?”

> The documents I have don’t cover that. They’re about Italian Greyhound care: diet, health problems, housetraining, exercise, keeping them warm, and how they get on with other pets.

All eight candidates exceed the distance cutoff, so the model is not called.

## Query Interface

`app.py` provides a Gradio question textbox and Ask button, an optional source filter, an answer box containing inline citations, and a source box containing source names, filenames, chunk positions, distances, and citation-use markers.

```text
Question: Do Italian Greyhounds bark a lot?
Answer: Italian Greyhounds are generally not excessive barkers and are
relatively quiet compared with many other breeds [1]. However, like all dogs
they may bark when excited, nervous, or seeking attention [2].

Retrieved from:
*[1] Adopt-a-Pet — Do Italian Greyhounds Bark a Lot?
     file: adopt_a_pet__do_italian_greyhounds_bark_a_lot.txt
     chunk 0, distance 0.346
*[2] Adopt-a-Pet — Do Italian Greyhounds Bark a Lot?
     file: adopt_a_pet__do_italian_greyhounds_bark_a_lot.txt
     chunk 1, distance 0.299
```

### Metadata Filtering Stretch Feature

The source dropdown filters retrieval using each chunk’s `source` metadata. For example, “How can I tell if my Italian Greyhound is cold?” normally returns Houndtees temperature passages. Selecting **Southern Cross Vet — 10 Common Health Issues** before asking the same question restricts every returned result to that veterinary source, visibly changing the source list. The filter is implemented by the `source` argument in `search()`, `retrieve_for()`, and `answer()`.

### Conversational Memory Stretch Feature

The Gradio state retains the last five question-answer pairs. When a follow-up contains a reference such as “they,” “it,” or “that,” `contextualise_question()` includes the preceding user question in retrieval and generation. The Clear conversation button resets the state.

Demo exchange:

```text
User: How tall and heavy is a typical Italian Greyhound?
System: They stand 13–15 inches at the withers and weigh about 7–14 lb [1].

User: How much do they weigh?
System: A typical Italian Greyhound stands about 13–15 in at the withers [2].
Its usual weight is 7–14 lb (3–6 kg) [2].
Interface status: Used the previous question for context.
```

## Evaluation Report

These are verbatim responses from the current hybrid system, recorded on September 1, 2026.

| # | Question | Expected answer | Actual system response | Judgment |
|---:|---|---|---|---|
| 1 | Do Italian Greyhounds bark a lot? | Generally quiet; may bark from excitement, nervousness, or attention-seeking | “Italian Greyhounds are generally not excessive barkers and are relatively quiet compared with many other breeds [1]. However, like all dogs they may bark when they are excited, nervous, or seeking attention [2].” | Accurate |
| 2 | What are the early signs of PRA? | Night blindness and dilated pupils | “The early signs of Progressive Retinal Atrophy in an Italian Greyhound include night blindness and dilated pupils [1].” | Accurate |
| 3 | Why is being overweight bad? | Organ strain, shorter life, and greater fracture and orthopedic risk | “The documents note that extra calories from people-food must be accounted for when keeping an Italian Greyhound at a healthy weight [1]. They also say that an overweight IG will hide the faint outline of ribs, vertebrae, hip points and a lean tuck, indicating excess body condition [2]. The sources do not explain why being overweight is harmful to an Italian Greyhound.” | **Inaccurate** |
| 4 | Why do rescues say a crate is not cruel? | Dogs are den animals and should have their own room | “Rescue groups say crating isn’t cruel because dogs are den-type animals and naturally benefit from having their own ‘room’ to retreat to [4].” | Accurate |
| 5 | How tall and heavy is a typical IG? | 13–15 in at the withers and 7–14 lb | “Italian Greyhounds are small dogs. One passage from Dimensions.com says they stand 13–15 inches (33–38 cm) at the withers and weigh about 7–14 lb (3–6 kg) [1]. Another passage from the same source gives a standing height of roughly 17–20 inches (43–51 cm) [3].” | Accurate |

**Score:** 4 accurate, 0 partially accurate, 1 inaccurate.

## Failure Case

The current failure is the overweight question. Semantic-only retrieval ranks the two passages containing the expected answer first and second: one says extra weight strains vital organs and shortens life expectancy, and the other says the breed is not built to carry extra weight. Reciprocal rank fusion moves those passages to hybrid ranks 10 and 15, outside the top-eight generation window. The model therefore sees only calorie-management and body-shape passages and incorrectly concludes that the sources do not explain the harm. This is a retrieval-stage failure caused by keyword ranking displacing stronger semantic matches.

The crating question shows the opposite outcome. It originally failed because the “dogs are den animals” chunk ranked 20th, outside the six chunks sent to the model.

Removing query scaffolding moved the chunk to semantic rank 7. Hybrid retrieval then combined semantic and BM25 rankings and moved it to rank 4. Semantic retrieval captures meaning, while BM25 gives weight to the rare exact word “cruel.”

Together, the cases show the tradeoff honestly: hybrid search improves an exact-word query but can hurt a query already handled well by semantic similarity. A production version should tune the fusion weights or retrieve a union of high-confidence semantic and keyword results so strong semantic matches cannot be pushed out.

## Spec Reflection

The spec helped by defining five expected answers before implementation, giving me a fixed set for comparing chunk sizes and retrieval changes. Implementation diverged from the original 1,000-character, 150-overlap plan because testing showed that 200-character chunks with 30 overlap retrieved specific facts more reliably.

## AI Usage

1. I gave an AI tool my document formats and chunking plan and asked for ingestion and recursive chunking functions. I revised its cleaning rules, fixed paragraph handling, added repeated-banner detection, and changed the chunk size after measuring retrieval.
2. I gave an AI tool the grounding and attribution requirements and asked for generation and interface code. I strengthened the prompt, generated the source list programmatically, and added citation validation rather than trusting the model’s formatting.
3. For the failed crating query, I supplied the measured semantic ranks and requested retrieval alternatives. I kept a semantic-only baseline, implemented BM25 plus reciprocal rank fusion, preserved the semantic cutoff, and documented the rank-7 versus rank-4 comparison.
