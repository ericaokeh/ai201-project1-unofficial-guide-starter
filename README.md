# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |
| 6 | | | |
| 7 | | | |
| 8 | | | |
| 9 | | | |
| 10 | | | |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:** 200 characters, using recursive splitting — paragraphs first, then sentences, with a new chunk started at every section heading. A sentence longer than 200 characters is kept whole rather than sliced.

**Overlap:** 30 characters (15%), starting at a sentence boundary.

**Why these choices fit your documents:**

I started at 1,000 characters, because that's about the size of one section in my sources — each of the 10 health issues on the Southern Cross Vet page runs 150–200 words, and the housetraining sections are similar. The idea was that one chunk would hold one section, and one section usually answers one question.

Testing retrieval showed that was wrong, and taught me something I hadn't understood: **an embedding is an average over everything in the chunk.** A section-sized chunk holds one sentence that answers the question plus a lot of other material, and the other material pulls the vector away from the answer.

I measured this on my crating question. The sentence "Crating is not cruel as dogs are den animals" scores **0.694** similarity against "Is crating cruel?" on its own. Inside its 898-character section chunk, it scored **0.072**. Adding just one neutral sentence about crates being a useful training tool dropped it from 0.598 to 0.340.

So I tested all 5 of my evaluation questions at several sizes and counted how many retrieved their answer in the top 5:

| Chunk size | Chunks | Answers found in top 5 |
|---|---|---|
| **200** | **293** | **5/5** |
| 450 | 162 | 5/5 |
| 600 | 118 | 4/5 |
| 1,000 | 76 | 4/5 |

200 wins, and gives the lowest distance scores. The cost is real: a chunk is now one or two sentences rather than a whole section, so each carries less context, and Chunk 2 in my samples below shows what that looks like at its weakest.

Two related changes came out of the same testing:

- **I stopped embedding the source name.** I was putting `Mid-Atlantic Iggy Rescue - Housetraining: ` on the front of every chunk *before* embedding it, so every vector contained a rescue group's name and the words "Italian Greyhound". That shared wording drowned out the words that distinguish chunks — searching `crate training` found the right chunk at rank 1, but `Is crating an Italian Greyhound cruel?` couldn't find it in the top 5 at all. The name is still stored in metadata and still shown with answers.
- **I treat the breed name as a stopword.** Every document is about Italian Greyhounds, so the phrase carries no information about which chunk you want. Removing it from both chunks and queries moved my weight question from rank 20 to rank 2.

**Preprocessing before chunking** (`clean_text()` in `ingest.py`):

- Fixed HTML entities (`&amp;`, `&nbsp;`) and curly quotes, and stripped any leftover tags
- Dropped lines containing junk phrases — cookie notices, privacy policy, copyright, subscribe, share buttons, comment counts
- Dropped runs of 3 or more short unpunctuated lines, which is how navigation menus appear; a single short line is kept because that's a real heading
- Dropped lines repeated across 3 or more documents, which removed the site banner shared by four pages on the same rescue site
- Dropped sentence fragments (lines starting with a lowercase letter or punctuation) and exact duplicate lines
- Kept each surviving block as its own paragraph, separated by a blank line, so the chunker can find paragraph boundaries

**Final chunk count:** **293 chunks** across 10 documents, from 56,270 characters of cleaned text. Sizes run 64 to 363 characters, averaging 192. That's inside the expected 50–2,000 range. My planning.md estimate of 70–100 was made at the 1,000-character size and no longer applies.

The per-document breakdown follows the documents rather than cutting mechanically: the housetraining page produced 36 chunks and the vet page 28, while the Adopt-a-Pet Q&A — the whole page is 386 characters — produced 1. Only 7 of the 293 chunks don't end on sentence punctuation, and those are section headings.

---
## Sample Chunks

Five **random** chunks printed by `python ingest.py`, copied exactly as they came out. Each starts with its source name, which my chunker adds for display and attribution.

I take them at random rather than evenly spaced. My first version picked evenly spaced chunks and kept showing me the same good-looking ones; the first random draw turned up three bad chunks immediately.

**Chunk 1** — from `ig_rescue_foundation__caring_for_iggys.txt` (166 characters)

> IG Rescue Foundation - Caring for Iggys: Caring for Italian Greyhounds
>
> Compared to many dog breeds, Italian Greyhounds are a relatively low maintenance breed of dog.

*Stands on its own:* yes. It answers "are Italian Greyhounds high maintenance?" The section heading sits directly above the sentence it introduces, which is a rule I had to add — chunks used to end on a dangling heading with nothing under it.

---

**Chunk 2** — from `houndtees__keeping_your_sighthound_warm.txt` (98 characters)

> Houndtees - Keeping Your Sighthound Warm: It don't take much for your sighthound to feel the cold!

*Stands on its own:* barely. It's a complete sentence and it's on-topic, but it's the weakest of these five — it tells you sighthounds get cold without saying why or what to do about it. This is the honest cost of my 200-character chunk size: a short paragraph in the source becomes a thin chunk. The 30-character overlap means the following sentence appears at the start of the next chunk, so the fuller explanation is still retrievable, just not from this chunk alone.

---

**Chunk 3** — from `ig_rescue_foundation__diet.txt` (146 characters)

> IG Rescue Foundation - Diet: Dog Food Advisor offers a rating system so you can research foods and choose a well-rated food that fits your budget.

*Stands on its own:* yes. A complete, specific recommendation that answers "how do I choose a dog food?"

---

**Chunk 4** — from `ig_rescue_foundation__diet.txt` (163 characters)

> IG Rescue Foundation - Diet: Avoid non-specific ingredients such as meat, meat meal, meat and bone meal, blood meal, poultry meal, liver meal, glandular meal, etc.

*Stands on its own:* yes. It answers "what ingredients should I avoid in my IG's food?" and the list is complete rather than cut off partway.

---

**Chunk 5** — from `ig_rescue_foundation__diet.txt` (354 characters)

> IG Rescue Foundation - Diet: Some owners who feed a raw diet choose from a variety of pre-made brands that are available at better pet food stores; these options range from patties or nuggets of frozen raw food which can be defrosted and fed as needed, to freeze-dried or dehydrated raw food which are shelf-stable and can be mixed with water and served.

*Stands on its own:* yes. This one is 354 characters, well over my 200-character target, because it's a single sentence and I keep long sentences whole rather than slicing them. An oversized chunk is a much smaller problem than one that trails off mid-word.

**One thing this draw shows about my collection:** three of these five came from the diet document. That's not a bug — it's my longest-per-topic source and produced 18 chunks — but it's a reminder that my chunks aren't spread evenly across sources, so a query has more ways to land in the diet document than in the barking one.

---

### What I had to debug

Each round of problems was found by reading output, not by guessing.

**Round 1 — repeated site banners.** Two chunks opened with "Wren is a fighter…" and an all-caps scam warning. Four of my sources are pages on the same rescue website and all carried that banner. They're real sentences about Italian Greyhounds, so no line-by-line rule could catch them. Fix: compare documents against each other and drop any line appearing in 3 or more of the 10.

**Round 2 — interface text.** The Adopt-a-Pet chunk contained "Loading…", "Enter e-mail", "Send", and three "Related Questions" that page links to but never answers. Fix: a list of whole lines that are always buttons, plus treating a short standalone question as a link rather than as writing. Later I found the Houndtees shop pages carried promo banners too ("$12 SHIPPING OVER $175", "TARIFFS & DUTIES INCLUDED") and added those.

**Round 3 — paragraphs weren't being split.** A chunk started with the single word "Do". Tracing it, my cleaning function joined lines with a single newline while the chunker splits paragraphs on blank lines, so every document arrived as **one enormous paragraph** and the paragraph step never ran. It fell through to sentence splitting every time — the opposite of the recursive strategy in planning.md. Changing the join to a blank line fixed it and put headings above the text they introduce.

**Round 4 — cleaning was deleting answers.** This was the worst one, and I only found it because retrieval failed. The housetraining page says *"Crating is **not** cruel as dogs are den animals."* The bold `not` splits that into three separate pieces in the HTML, and my fragment rule deleted the lowercase piece — destroying the answer to one of my own test questions. Fragments are now rejoined onto the unfinished line above them, which recovered about 4,000 characters across the whole collection. Getting this fix backwards would have stored "Crating is cruel", so I checked the `not` survived.

**Known remaining issues:**

- The Dimensions.com document includes that site's self-description ("a comprehensive reference database of dimensioned drawings…"), which isn't about dogs. It only appears in one document, so my repeated-line check can't see it.
- A bare short menu item like "Find a pet" would still survive, because it's shaped exactly like a real heading such as "Crates".
- My sentence splitter breaks on `!` and `?` even inside quotation marks, so `"whew! glad you are out of that awful place"` splits in two.

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:**

**Production tradeoff reflection:**

---

## Retrieval Test Results

<!-- Run these 3 queries through your retrieval system and record the top returned chunks.
     For at least 2 of the 3, explain why the returned chunks are relevant to the query.
     Results must be text — not screenshots. -->

**Query 1:**

Top returned chunks:
-
-
-

Relevance explanation:

---

**Query 2:**

Top returned chunks:
-
-
-

Relevance explanation:

---

**Query 3:**

Top returned chunks:
-
-
-

Relevance explanation:

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**

**How source attribution is surfaced in the response:**

---

## Example Responses

<!-- Provide at least 2 grounded responses (query + response + source attribution)
     and 1 out-of-scope query showing your system's refusal.
     All entries must be text — not screenshots. -->

**Grounded response 1**

Query:

Response:

Source attribution:

---

**Grounded response 2**

Query:

Response:

Source attribution:

---

**Out-of-scope query**

Query:

System response (refusal):

---

## Query Interface

<!-- Describe your query interface: what are the input fields, what does the output look like?
     Then provide a complete sample interaction transcript showing a real exchange. -->

**Input fields:**

**Output format:**

---

**Sample Interaction Transcript**

<!-- Show a complete query → response exchange as it actually appears in your interface.
     Must be text — not a screenshot. -->

> **User:** 

> **System:** 

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**

**What the system returned:**

**Root cause (tied to a specific pipeline stage):**

**What you would change to fix it:**

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**

**One way your implementation diverged from the spec, and why:**

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*

**Instance 2**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*
