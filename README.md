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

**Final chunk count:** **58 chunks** across 10 documents, from 49,084 characters of cleaned text. Sizes run 179 to 998 characters, averaging 846. That's inside the expected 50–2,000 range, and close to the 70–100 I estimated in planning.md — a bit lower because cleaning removed more boilerplate than I expected.

---

## Sample Chunks

<!-- Paste 5 representative chunks from your document collection after running your ingestion pipeline.
     For each chunk, note which source document it came from.
     These must be actual text — not screenshots. -->

These are real chunks printed by `python ingest.py`, copied exactly as they came out.
Each one starts with its source name, which my chunker puts at the front of every chunk.

**Chunk 1** — from `adopt_a_pet__do_italian_greyhounds_bark_a_lot.txt` (394 characters)

> Adopt-a-Pet - Do Italian Greyhounds Bark a Lot?: Do Italian Greyhounds bark a lot? - Adopt a Pet
>
> No, Italian Greyhounds are generally not excessive barkers. They tend to be relatively quiet and are not as vocal as some other breeds. However, like all dogs, Italian Greyhounds might bark in response to certain stimuli or situations, such as when they are excited, nervous, or seeking attention.

*Stands on its own:* yes. This whole source page is one short Q&A, so it became a single chunk. It's well under 1,000 characters and I let it stay that way instead of padding it out with something unrelated.

---

**Chunk 2** — from `ig_rescue_foundation__caring_for_iggys.txt` (980 characters)

> IG Rescue Foundation - Caring for Iggys: Caring for Italian Greyhounds
>
> Compared to many dog breeds, Italian Greyhounds are a relatively low maintenance breed of dog.
>
> They don't usually have the "dog smell" of other breeds, nor do they shed a lot.
>
> Since Italian Greyhounds are a short-haired breed, grooming in a traditional sense, by brushing their hair on a regular basis, isn't needed.
>
> However, like any dog they do need bathing, their nails need kept short, and glands sometimes expressed, squeezed, or drained.
>
> Brushing an Iggy's Teeth
>
> Keeping an Italian Greyhound's teeth clean is essential to maintaining good health.
>
> Many owners will brush their dog's teeth daily to keep plaque build-up to a minimum.
>
> Most pet retailers sell doggie tooth brushes and paste for cleaning a dog's teeth for a very reasonable cost.
>
> A dog who does not have dental care at home will need more regular dental cleanings by a veterinarian, generally costing a few hundred dollars every year.

*Stands on its own:* yes. You could answer "do Italian Greyhounds shed?" or "how often should I brush my IG's teeth?" from this chunk alone. It covers two related grooming topics rather than one, which is the cost of filling a chunk up to 1,000 characters.

---

**Chunk 3** — from `ig_rescue_foundation__diet.txt` (786 characters)

> IG Rescue Foundation - Diet: Feeding and Weight Maintenance
>
> The food you feed your Italian Greyhound is one of the primary ways that you can actively influence their health and lifespan.
>
> There are a number of viewpoints on what the "best" dog food is, but in truth, what is important is which food best meets your IG's
>
> Raw, Home-cooked, and Fresh Diets
>
> Some owners have reported improved health in their IG upon switching them to a raw diet.
>
> In theory, a raw diet comprised mainly of meat, bone, and organs is the best, most appropriate food for dogs because it is the freshest and least processed.
>
> In contrast, kibble or canned food is highly processed, contains some degree of non-nutritive filler, and when cooked compromises nutritional integrity and is more difficult to digest.

*Stands on its own:* mostly. It answers "is raw food better than kibble for an IG?" But one sentence is cut off on the source page itself — "which food best meets your IG's" just stops. That's how the original page reads, not a chunking bug, but it's a small piece of broken text sitting in my collection.

---

**Chunk 4** — from `iggy_rescue__other_pets_and_italian_greyhounds.txt` (974 characters)

> Iggy Rescue - Other Pets and Italian Greyhounds: People with cats know their cat's personality or personalities, if they have been accepting of other animals in the past, and how they may react.
>
> We do get some Italian Greyhounds in to rescue who have had bad experiences with cats in the past and are scared of them due to being attacked or scratched.
>
> And, on the opposite end of the spectrum, we also get IGs who are obsessed with chasing cats.
>
> However, there are harmonious placements too where the cats and dogs learn to become great friends.
>
> By visiting the Italian Greyhound message boards or forums, you will likely read stories or see pictures of Italian Greyhounds and cats living peacefully, or even cuddling together for a nap.
>
> (Since Italian Greyhounds have a nice warm body, the cats sometimes learn to appreciate their IG buddies as a heating pad.)
>
> IGs and Birds
>
> Italian Greyhounds ARE sighthounds!
>
> By nature they chase things including birds and rodents.

*Stands on its own:* yes. It fully answers "do Italian Greyhounds get along with cats?" The last two lines start the next section about birds, which is what the 150-character overlap is for — the bird section continues at the start of the following chunk, so neither topic gets cut off.

---

**Chunk 5** — from `mid_atlantic_iggy_rescue__housetraining.txt` (961 characters)

> Mid-Atlantic Iggy Rescue - Housetraining: Teach the dog the command "Kennel" before he enters his crate.
>
> If the dog is resistant to a crate initially, continue to give ALL meals and treats in the crate.
>
> Then place the dog in the crate but do not leave the room.
>
> Allow the dog to remain in the crate for just minutes, gradually increasing the time and eventually leaving the room and then the house for short intervals.
>
> The goal is to condition the animal to see the crate as positive and short term and to assure him that you are returning.
>
> Never let a dog out of the crate until he is quiet.
>
> Otherwise he will quickly learn he can get out of his crate by exhibiting negative behavior.
>
> When you let the dog out of the crate, do not make a big deal out of his exit.
>
> This just confirms to him that "whew! glad you are out of that awful place".
>
> Also, ignore a dog that is having problems with crate training 20-30 minutes before placing him in the crate.

*Stands on its own:* yes. This is a complete set of crate-training instructions and answers "how do I get my IG used to a crate?" without needing the rest of the page.

---

### What I fixed after reading these

The first time I printed these five chunks, three of them had problems, and I had to go back and change my cleaning code:

1. **Two chunks opened with the same site banner.** Four of my sources are pages on the same rescue website, so every one of them started with "Wren is a fighter…" and an all-caps scam warning. Those are real sentences on the right topic, so none of my line-by-line rules caught them. I fixed it by comparing documents to each other — any line appearing in 3 or more of my 10 documents is site furniture, and it gets dropped. That removed 9 lines and about 4,000 characters.

2. **One chunk started in the middle of a sentence** — "a very positive, important tool in housetraining" with the words "Crating is" stranded above it. My overlap was cutting at the nearest space. I changed it to start the overlap at a sentence boundary instead, and fall back to a space only if there isn't one.

3. **The Adopt-a-Pet chunk was full of interface text** — "Loading…", "Enter e-mail", "Send", plus three "Related Questions" that the page links to but never answers. I added a list of whole lines that are always buttons, and a rule that treats a short question on its own line as a link rather than as writing. That chunk went from 596 characters to 394, and now it's just the question and the answer.

**Still not perfect:** three of my 58 chunks are short leftovers from the very end of a document — a vet's author bio, a rescue group's tagline. They're on-topic enough not to be harmful, but they don't answer anything. I'd rather leave them in than write a rule aggressive enough to remove them, because that rule would probably eat real content too.

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
