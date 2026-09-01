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

**Chunk size:** 1,000 characters (about 250 tokens), using recursive splitting — paragraphs first, then sentences, and only cutting mid-sentence as a last resort.

**Overlap:** 150 characters (15%), starting at a sentence boundary.

**Why these choices fit your documents:**

Most of my sources are guides broken into sections, and those sections are consistently sized — each of the 10 health issues on the Southern Cross Vet page runs 150–200 words, and the housetraining sections are about the same. That's roughly 1,000 characters, so one chunk ends up holding about one section, and one section usually answers one question.

At 500 characters a health issue would split in half, putting the disease name in one chunk and its symptoms in another. At 2,000 three unrelated conditions would be squashed together and the chunk would stop being about any one thing.

**Preprocessing before chunking** (`clean_text()` in `ingest.py`):

- Fixed HTML entities (`&amp;`, `&nbsp;`) and curly quotes, and stripped any leftover tags
- Dropped lines containing junk phrases — cookie notices, privacy policy, copyright, subscribe, share buttons, comment counts
- Dropped runs of 3 or more short unpunctuated lines, which is how navigation menus appear; a single short line is kept because that's a real heading
- Dropped lines repeated across 3 or more documents, which removed the site banner shared by four pages on the same rescue site
- Dropped sentence fragments (lines starting with a lowercase letter or punctuation) and exact duplicate lines
- Kept each surviving block as its own paragraph, separated by a blank line, so the chunker can find paragraph boundaries

**Final chunk count:** **64 chunks** across 10 documents, from 49,433 characters of cleaned text. Sizes run 153 to 998 characters, averaging 772. That's inside the expected 50–2,000 range, and just under the 70–100 I estimated in planning.md — a bit lower because cleaning removed more boilerplate than I expected.

The per-document breakdown shows the chunker following the documents rather than cutting mechanically: the housetraining page (7,946 characters) produced 12 chunks and the vet page (7,245) produced 12, while the two very short sources produced 1 each. The 64 chunks have 62 distinct lengths, so nothing is being sliced at a fixed size.

---

## Sample Chunks

These are five **random** chunks printed by `python ingest.py`, copied exactly as they came out. Each one starts with its source name, because my chunker puts that at the front of every chunk.

I picked them randomly on purpose. My first version of the sampling took evenly spaced chunks, and it kept handing me the same good-looking ones. The first random draw turned up three bad chunks straight away.

**Chunk 1** — from `ig_rescue_foundation__caring_for_iggys.txt` (683 characters)

> IG Rescue Foundation - Caring for Iggys: stinky things found in their yard, it may be a good idea to give them a quick cleansing before they are ready to snuggle under the blankets at night.
>
> Cleaning the Ears
>
> At a minimum keep monitor if your Italian Greyhound's ears are building up wax and dirt that may be irritating them, and causing them to itch or get infected. Heavy or dark buildup can be indicative of other problems such as an infection or ear mites even. Cleaning the ears isn't difficult but should be done with care. You should only clean the widest part of the ear, without entering the ear canal. If wax buildup is especially heavy, a veterinary visit may be needed.

*Stands on its own:* yes. Someone could answer "how do I clean my Italian Greyhound's ears?" from this chunk alone. It opens mid-sentence because that's the 150-character overlap carrying the tail of the previous chunk, so the sentence isn't lost from either one.

---

**Chunk 2** — from `houndtees__keeping_your_sighthound_warm.txt` (930 characters)

> Houndtees - Keeping Your Sighthound Warm: Please do what you can to warm them up, so they're happy to stretch back out or roach the day away – suggestions on that to come.
>
> Their ears are cold
>
> If your hound's ears are cold to the touch, they'll be feeling cold all over!
>
> Their paw pads are cold
>
> Doggos regulate heat through their paw pads, and if your hound's feetsies are cold, they need some warming up.
>
> Are you cold?
>
> If you're cold, your doggo won't be too far behind. Sighthound's bods do run at a higher base temp than hoomans, so they should typically feel warm to your touch. If you're cold, check your doggo's ears.
>
> Shivering
>
> Like hoomans, doggos will shiver to warm up. Not to be confused with chattering – sometimes, when greyhounds are excited, they'll chatter their teeth together, kinda like the dog equivalent of purring.
>
> Shaking it off
>
> Some greyhounds will attempt to shake off the cold like it were water.

*Stands on its own:* yes. This fully answers "how can I tell if my sighthound is cold?" — it's a list of five signs, each with its heading attached to its explanation. This is the chunk I'd most want retrieved for that question, and it holds the whole answer.

---

**Chunk 3** — from `iggy_rescue__other_pets_and_italian_greyhounds.txt` (722 characters)

> Iggy Rescue - Other Pets and Italian Greyhounds: there will be exceptions, so it is always best to fill our an adoption application completely and accurately to help ensure a successful placement.
>
> Iggys and Cats
>
> More often than not, the cats are usually more particular about a dog coming in to their house than vice versa. People with cats know their cat's personality or personalities, if they have been accepting of other animals in the past, and how they may react. We do get some Italian Greyhounds in to rescue who have had bad experiences with cats in the past and are scared of them due to being attacked or scratched. And, on the opposite end of the spectrum, we also get IGs who are obsessed with chasing cats.

*Stands on its own:* yes. It answers "do Italian Greyhounds get along with cats?" The "Iggys and Cats" heading sits directly above the text it introduces, which is what tells you what the chunk is about.

---

**Chunk 4** — from `iggy_rescue__other_pets_and_italian_greyhounds.txt` (875 characters)

> Iggy Rescue - Other Pets and Italian Greyhounds: Rescues get many questions about if Italian Greyhounds "get along" with other dogs, tolerate cats or birds, or are safe around other animals even. And, the answer to most of those questions is the same and simple... it really depends on the particular dog. The best way to know if a particular dogs gets along with other animals is to ask the rescue representative who is fostering the animal. They may or may not be able to tell you an answer based on if they have other pets in the house, or if the previous owners have supplied such information upon surrendering the IG. Although our approval process sometimes seems lengthy, we include a home visit so we can help introduce a dog in to a new environment, existing pets, and to feel comfortable that the dogs we love are going to a home where we also feel they will thrive.

*Stands on its own:* yes. It's one complete argument — that compatibility depends on the individual dog, and how to find out about a specific one. Note this is a second chunk from the same document as Chunk 3, covering a different part of it, which is what I want.

---

**Chunk 5** — from `ig_rescue_foundation__diet.txt` (915 characters)

> IG Rescue Foundation - Diet: Avoid "flavors", digests, and color dyes.
>
> Grain-free kibble or canned food
>
> Some Italian Greyhounds are sensitive to grains (corn, wheat, rice, oats, barley, rye, soybeans, millet, etc.), and enjoy better health when fed a grain-free food. It is important to remember that any grain-free kibble will have an alternative carbohydrate source such as sweet potato, peas, or potato, and some dogs also have difficulty with these alternative carbohydrates. A grain-free diet is especially worth considering if your dog has an existing health condition such as allergies, skin issues, chronic ear infections, immune issues, and digestive issues.
>
> IGs are not built to carry excess weight. Excess weight creates an increased workload for vital organs, reduces life expectancy, and increases the risk of leg break and other orthopedic issues through added strain on muscles, bones, and joints.

*Stands on its own:* yes. It answers "should I feed my Italian Greyhound grain-free food?" It holds two topics — grain-free diets and weight — which is the cost of filling a chunk up to 1,000 characters, but both are about feeding so the chunk still has a clear subject.

---

### What I had to debug before these were usable

Random sampling found problems that my evenly spaced sampling had hidden. Three rounds of fixes:

**Round 1 — repeated site banners.** Two chunks opened with the same text: "Wren is a fighter…" and an all-caps scam warning. Four of my sources are pages on the same rescue website, so every one of them carried that banner. They're real sentences about Italian Greyhounds, so no line-by-line rule could catch them. The fix was to compare documents against each other — any line appearing in 3 or more of my 10 documents is site furniture. That removed 9 lines.

**Round 2 — interface text and dead links.** The Adopt-a-Pet chunk contained "Loading…", "Enter e-mail", "Send", and three "Related Questions" the page links to but never answers. I added a list of whole lines that are always buttons, and a rule treating a short standalone question as a link rather than as writing.

**Round 3 — the real bug.** A chunk started with the single word "Do". Chasing it down, I found my cleaning function joined lines with a single newline while my chunker splits paragraphs on blank lines. So every document arrived at the chunker as **one enormous paragraph**, and the paragraph step never ran — it fell through to sentence splitting every single time. My planning.md says "paragraphs first, then sentences," and that had not been true of my code at all.

Changing the join to a blank line fixed it, and the difference is visible in these samples: headings like "Cleaning the Ears" and "Grain-free kibble or canned food" now sit directly above the text they introduce, instead of being scattered. It also changed my chunk count from 58 to 64, because real paragraph boundaries produce different splits than sentence-packing does.

Two smaller fixes came out of the same round: a chunk may no longer *end* on a heading (headings move down to the next chunk, where their content is), and an overlap that lands on a fragment shorter than 40 characters is dropped instead of being carried over — that's what produced the stray "Do".

**Known remaining issues**, which I chose not to fix:

- Three of the 64 chunks are short leftovers from the end of a document — a vet's author bio, a rescue group's tagline. They're complete sentences rather than fragments, and on-topic enough to be harmless. A rule aggressive enough to remove them would take real content with it.
- The Dimensions.com chunk includes that site's self-description ("a comprehensive reference database of dimensioned drawings…"), which isn't about dogs. It only appears in one document, so my repeated-line check can't see it.
- My sentence splitter breaks on `!` and `?` even inside quotation marks, so a quote like `"whew! glad you are out of that awful place"` gets split in two. Both halves stayed in the same chunk here, but on a chunk boundary it would strand half a quote.

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
