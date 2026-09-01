# The Unofficial Guide — Italian Greyhounds

A question-answering system that answers only from 10 saved rescue, vet and owner pages about living with an Italian Greyhound.

**Run it:**

```
pip install -r requirements.txt
cp .env.example .env          # add a free Groq key from console.groq.com
python ingest.py              # load and chunk the documents
python embed.py               # embed them into ChromaDB
python app.py                 # web interface at http://localhost:7860
```

| File | What it does |
|---|---|
| `ingest.py` | Loads the 10 `.txt` documents, cleans them, splits them into chunks |
| `embed.py` | Embeds the chunks with all-MiniLM-L6-v2, stores them in ChromaDB, searches them |
| `generate.py` | Sends retrieved chunks to a Groq model with a grounding prompt; also a CLI |
| `app.py` | The Gradio web interface |

---

## Domain

Day-to-day care and ownership of Italian Greyhounds — what the breed is actually like to live with, rather than what a breed profile page says about it.

This is hard to find through official channels because kennel club and vet clinic pages give a short, generic summary that reads much the same for every breed. The details that matter come from rescue groups and owners: that these dogs get cold and need coats indoors, that they are notoriously difficult to housetrain, that their legs break easily, and that whether they can live with a cat depends entirely on the individual dog. That knowledge is scattered across a dozen rescue sites and forum answers, so somebody deciding whether this is the right dog for them has to hunt for it one page at a time.

The system answers questions like "how can I tell if my iggy is cold?", "how long can they be crated?", and "do they get along with cats?" — and refuses questions its documents don't cover, such as breeder recommendations or puppy prices.

---

## Document Sources

All 10 sources are saved as plain `.txt` files in `documents/`. The first line of each file is the source name, which becomes the label on every chunk drawn from it.

| # | Source | Type | URL | Saved as |
|---|--------|------|-----|----------|
| 1 | Italian Greyhound Rescue Foundation — Diet | Rescue organisation guide | https://www.igrescue.com/html/basics/diet_for_italian_greyhounds.shtml | `ig_rescue_foundation__diet.txt` |
| 2 | Mid-Atlantic Iggy Rescue — Housetraining | Rescue organisation guide | https://www.midatlanticiggyrescue.com/ig-helptraining/housetraining/ | `mid_atlantic_iggy_rescue__housetraining.txt` |
| 3 | Southern Cross Vet — 10 Common Health Issues | Veterinary clinic article | https://southerncrossvet.com.au/10-italian-greyhound-common-health-issues/ | `southern_cross_vet__10_common_health_issues.txt` |
| 4 | Houndtees — Keeping Your Sighthound Warm | Owner-facing blog (retailer) | https://houndtees.com.au/en-us/blogs/blog/how-to-tell-if-your-sighthound-is-cold-how-to-keep-them-warm | `houndtees__keeping_your_sighthound_warm.txt` |
| 5 | Dimensions.com — Italian Greyhound Size | Reference database | https://www.dimensions.com/element/italian-greyhound | `dimensions_com__italian_greyhound_size.txt` |
| 6 | IG Rescue Foundation — Coloration and Patterns | Rescue organisation guide | https://www.igrescue.com/html/basics/coloration_&_patterns.shtml | `ig_rescue_foundation__coloration_and_patterns.txt` |
| 7 | IG Rescue Foundation — Caring for Iggys | Rescue organisation guide | https://www.igrescue.com/html/basics/caring_for_iggys.shtml | `ig_rescue_foundation__caring_for_iggys.txt` |
| 8 | IG Rescue Charity UK — Exercise | Rescue organisation guide (UK) | https://italiangreyhoundrescuecharity.org.uk/about-italian-greyhounds/exercise/ | `ig_rescue_charity_uk__exercise.txt` |
| 9 | Iggy Rescue — Other Pets and Italian Greyhounds | Rescue organisation guide | https://www.iggyrescue.com/html/basics/other_pets_&_italian_greyhounds.shtml | `iggy_rescue__other_pets_and_italian_greyhounds.txt` |
| 10 | Adopt-a-Pet — Do Italian Greyhounds Bark a Lot? | Breed FAQ | https://www.adoptapet.com/answers/do-italian-greyhounds-bark-a-lot | `adopt_a_pet__do_italian_greyhounds_bark_a_lot.txt` |

The sources deliberately cover different subtopics — diet, health, housetraining, exercise, temperature, size, colour, other pets, barking — and different perspectives. Rescue groups write about the problems that cause people to surrender the breed; the vet clinic writes clinically about disease; the retailer blog writes casually for owners. Four of the ten are pages on the same rescue website, which caused a specific problem described under Chunking Strategy.

They also vary enormously in length. The housetraining page produced 62 chunks; the Adopt-a-Pet Q&A is 346 characters in total and produced 2.

---

## Chunking Strategy

**Chunk size:** 200 characters, using recursive splitting — paragraphs first, then sentences, with a new chunk started at every section heading. A sentence longer than 200 characters is kept whole rather than sliced.

**Overlap:** 30 characters (15%), starting at a sentence boundary.

**Why these choices fit your documents:**

I started at 1,000 characters, because that's about the size of one section in my sources — each of the 10 health issues on the Southern Cross Vet page runs 150–200 words, and the housetraining sections are similar. The idea was that one chunk would hold one section, and one section usually answers one question.

Testing retrieval showed that was wrong, and taught me something I hadn't understood: **an embedding is an average over everything in the chunk.** A section-sized chunk holds one sentence that answers the question plus a lot of other material, and the other material pulls the vector away from the answer.

I measured this on my crating question. The sentence "Crating is not cruel as dogs are den animals" scores **0.694** similarity against "Is crating cruel?" on its own. Inside its 898-character section chunk, it scored **0.072**. Adding just one neutral sentence about crates being a useful training tool dropped it from 0.598 to 0.340.

So I tested all 5 of my evaluation questions at several sizes and counted how many retrieved their answer in the top 5:

| Chunk size | Chunks | Answers found in top 5 |
|---|---|---|
| **200** | **282** | **5/5** |
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

**Final chunk count:** **282 chunks** across 10 documents, from 54,558 characters of cleaned text. Sizes run 67 to 363 characters, averaging 193. That's inside the expected 50–2,000 range. My planning.md estimate of 70–100 was made at the 1,000-character size and no longer applies.

The per-document breakdown follows the documents rather than cutting mechanically: the housetraining page (9,587 characters) produced 62 chunks and the vet page (7,423) produced 49, while the Adopt-a-Pet Q&A — 346 characters in total — produced 2. Only 8 of the 282 chunks don't end on sentence punctuation.

---

## Sample Chunks

Five **random** chunks printed by `python ingest.py`, copied exactly as they came out. Each begins with its source name, which the chunker adds for display and attribution.

I sample randomly rather than at even intervals. My first version took evenly spaced chunks and kept handing me the same presentable ones; the first random draw turned up three bad chunks immediately.

**Chunk 1** — from `ig_rescue_foundation__caring_for_iggys.txt` (195 characters)

> IG Rescue Foundation - Caring for Iggys: A dog who does not have dental care at home will need more regular dental cleanings by a veterinarian, generally costing a few hundred dollars every year.

*Stands on its own:* yes. It answers "what happens if I don't brush my IG's teeth?" with a specific consequence and a cost, and needs nothing before or after it.

---

**Chunk 2** — from `houndtees__keeping_your_sighthound_warm.txt` (171 characters)

> Houndtees - Keeping Your Sighthound Warm: Please do what you can to warm them up, so they're happy to stretch back out or roach the day away – suggestions on that to come.

*Stands on its own:* **no — this is the weakest chunk in the draw.** It's a complete sentence, but "warm them up" has no antecedent, and "suggestions on that to come" is a promise about content that lives in a different chunk. On its own it tells you almost nothing. This is the honest cost of 200-character chunks: a transitional sentence in the source becomes a chunk with nothing to say. It's low risk because it rarely outranks the substantive chunks in that document, but if it were retrieved alone it would be useless.

---

**Chunk 3** — from `iggy_rescue__other_pets_and_italian_greyhounds.txt` (233 characters)

> Iggy Rescue - Other Pets and Italian Greyhounds: Italian Greyhounds and Other Dogs
>
> As a general rule most dogs get along after getting to know one another, if properly introduced and given time.
>
> However there are always exceptions.

*Stands on its own:* yes, and it shows the heading rule working. "Italian Greyhounds and Other Dogs" sits directly above the text it introduces, so the chunk announces its own topic. Chunks used to be able to *end* on a dangling heading with nothing underneath; headings now move down to the chunk that carries their content.

---

**Chunk 4** — from `ig_rescue_foundation__diet.txt` (231 characters)

> IG Rescue Foundation - Diet: Excess weight creates an increased workload for vital organs, reduces life expectancy, and increases the risk of leg break and other orthopedic issues through added strain on muscles, bones, and joints.

*Stands on its own:* yes. This is the chunk that answers evaluation question 3, and it's a good illustration of why I cut the chunk size. At 1,000 characters this sentence shared a chunk with a long discussion of grain-free kibble, and the question "why is being overweight bad?" retrieved it at rank 15. Alone in a 231-character chunk, it comes back at rank 2.

---

**Chunk 5** — from `ig_rescue_foundation__diet.txt` (167 characters)

> IG Rescue Foundation - Diet: Don't assume that "veterinary" diets are high quality. Check the ingredients label just as you would for any food, and evaluate carefully.

*Stands on its own:* yes. A complete, specific piece of advice that answers "are prescription dog foods better?"

**What this draw shows about the collection:** two of the five came from the diet document. Chunks aren't spread evenly across sources — the housetraining page produced 62 and the Adopt-a-Pet Q&A produced 2 — so a query has far more ways to land in the long documents than the short ones.

---

### What I had to debug

Each round of problems was found by reading output, not by guessing.

**Round 1 — repeated site banners.** Two chunks opened with "Wren is a fighter…" and an all-caps scam warning. Four sources are pages on the same rescue website, and all four carried that banner. They are real sentences about Italian Greyhounds, so no line-by-line rule could catch them. Fix: compare documents against each other and drop any line appearing in 3 or more of the 10. Without this, 8 banner chunks come back.

**Round 2 — interface text.** The Adopt-a-Pet chunk contained "Loading…", "Enter e-mail", "Send", and three "Related Questions" the page links to but never answers. Fix: a list of whole lines that are always buttons, plus treating a short standalone question as a link rather than as writing. The Houndtees shop pages carried promo banners too ("$12 SHIPPING OVER $175", "TARIFFS & DUTIES INCLUDED").

**Round 3 — paragraph splitting was never running.** A chunk started with the single word "Do". Tracing it, my cleaning function joined lines with a single newline while the chunker split paragraphs on blank lines — so every document arrived as **one enormous paragraph** and the paragraph step never executed. Everything fell through to sentence splitting, the opposite of the recursive strategy in planning.md. The code looked correct and produced plausible chunks the whole time.

**Round 4 — cleaning was deleting answers.** The worst one, and only found because retrieval failed. The housetraining page says *"Crating is **not** cruel as dogs are den animals."* The bold `not` splits that into three pieces in the HTML, and my fragment rule deleted the lowercase piece — destroying the answer to one of my own test questions. Fragments now rejoin the unfinished line above them, recovering about 4,000 characters across the collection. I checked specifically that the word "not" survived, because the careless version of this fix stores "Crating is cruel".

**Round 5 — lettered lists were being shredded.** The vet page lists seizure causes as "a. Stress b. Allergic reactions c. Low blood sugar d. Cancer". My sentence splitter treated each letter's full stop as a sentence end, producing a chunk that was just "Low blood sugar d." — meaningless, but still retrievable for a question about seizures. The splitter now refuses to break after a single letter, a number, or a title like "Dr." My first attempt at that fix did nothing at all: the lookbehinds checked the character immediately before the split point, which is always the full stop itself, so every rule passed trivially.

**Known remaining issues:**

- The Dimensions.com document includes that site's self-description ("a comprehensive reference database of dimensioned drawings…"), which has nothing to do with dogs. It appears in only one document, so the repeated-line check can't see it.
- A bare short menu item like "Find a pet" would still survive, because it is shaped exactly like a real heading such as "Crates".
- Transitional sentences like Chunk 2 above become chunks with no standalone meaning.

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2`, loaded locally through sentence-transformers. It produces 384-dimension vectors and runs on my laptop with no API key and no rate limits. Vectors are stored in ChromaDB with cosine distance (`hnsw:space: cosine`) — Chroma's default is squared L2, which ranks results differently, so I set it explicitly.

Its input limit is 256 tokens. I checked whether my chunks get truncated: the longest is 223 tokens and the average is 168, so **nothing is cut off**. At my original 1,000-character chunk size this would have been a real risk, which is why I measured it.

Each chunk is stored with metadata: the readable source name, the filename, the chunk's position within its document, and its length. The source name is what appears in answers; the filename and position let me trace any claim back to a specific place in a specific document.

**Production tradeoff reflection:**

If this were a real product and cost weren't a constraint, I'd weigh four things.

**Context length.** MiniLM sees 256 tokens. That's fine at my current chunk size, but it locks me out of the larger chunks I'd want if I ever solved the dilution problem another way. `text-embedding-3-large` or a Voyage model would accept far longer chunks, so chunk size could be chosen for meaning rather than for the model's limit.

**Accuracy on domain-specific text.** My documents contain terms like "Progressive Retinal Atrophy", "luxating patella", "belly bands" and "snowballing". A larger model would represent these better. My clearest evidence that MiniLM struggles is in the Failure Case below — it ranks a chunk containing a near-verbatim answer 20th, because the query wording drifts.

**Latency and where it runs.** MiniLM answers instantly and my documents never leave my machine. An API model adds a network round trip to every search and means sending the whole collection to another company. For a public guide that's acceptable; for anything private it isn't.

**Multilingual support.** All 10 sources are English, so I don't need it. If I wanted people to ask in Spanish, MiniLM would fail and I'd need a multilingual model.

For a class project MiniLM is clearly right. For real users I'd pay for a hosted embedding model and keep MiniLM as an offline fallback.

---

## Retrieval Test Results

Distances are cosine distance — **lower is better**, 0 would be identical.

**Query 1: "Do Italian Greyhounds bark a lot?"**

Top returned chunks:
- **0.299** — `adopt_a_pet…txt` chunk 1 — *"However, like all dogs, Italian Greyhounds might bark in response to certain stimuli or situations, such as when they are excited, nervous, or seeking attention."*
- **0.346** — `adopt_a_pet…txt` chunk 0 — *"No, Italian Greyhounds are generally not excessive barkers. They tend to be relatively quiet and are not as vocal as some other breeds."*
- **0.481** — `mid_atlantic_iggy_rescue__housetraining.txt` chunk 54 — *"Most Italian Greyhounds will not go to the door and bark, but most will give you a subtle signal."*

Relevance explanation: the top two are the two halves of the only page in my collection that addresses barking directly — one gives the answer ("not excessive barkers"), the other the qualification ("might bark when excited"). Together they are the complete answer. The third is genuinely relevant but from a different angle: it's about barking as a housetraining signal, retrieved because it's the only other chunk in 282 that discusses an Italian Greyhound barking. The jump from 0.346 to 0.481 marks the boundary between "answers the question" and "mentions the topic".

**Query 2: "What are the early signs of Progressive Retinal Atrophy in an Italian Greyhound?"**

Top returned chunks:
- **0.246** — `southern_cross_vet…txt` chunk 14 — *"…signs that an Italian Greyhound may suffer from Retinal Atrophy include night blindness and dilated pupils."*
- **0.251** — `southern_cross_vet…txt` chunk 11 — *"2) Progressive Retinal Atrophy (PRA): Another very common issue in Italian Greyhounds is Progressive Retinal Atrophy."*
- **0.559** — `southern_cross_vet…txt` chunk 12 — *"This is a genetic disease that leads to permanent blindness in affected dogs over a period of time."*

Relevance explanation: this is the best-performing query and shows chunking and overlap working as designed. The disease is introduced in chunk 11, described in chunk 12, and its symptoms given in chunk 14 — the answer is spread across three consecutive chunks, and all three were retrieved. This is exactly the "key information split across a chunk boundary" risk I predicted in planning.md, and retrieval handled it because consecutive chunks about one disease are all close to the query.

**Query 3: "How can I tell if my Italian Greyhound is cold?"**

Top returned chunks:
- **0.408** — `houndtees…txt` chunk 8 — *"If you're cold, check your doggo's ears."*
- **0.438** — `houndtees…txt` chunk 0 — *"It don't take much for your sighthound to feel the cold!"*
- **0.520** — `houndtees…txt` chunk 3 — *"Signs your sighthound is a chilly billy / 'Snowballing' or curling up tightly — If your doggo is all curled up (usually with their tail draped over their nose), they're doing their best to conserve body heat."*

Relevance explanation: all six retrieved chunks came from the only source that covers temperature, and between them they carry the full list of signs. Chunk 3 is the one that matters most — and it only reads properly because of a fix I made after an earlier test. "Signs your sighthound is a chilly billy" is a heading, and at 200 characters it had become a chunk with no content underneath it. The model then cited it as evidence, producing an answer that said "the signs are listed in the [heading] section" instead of listing them. Heading-only chunks are now merged into the chunk that follows.

---

## Grounded Generation

Grounding is enforced three ways, not one.

**1. The system prompt.** The instruction that does the real work is the one that names the failure mode explicitly:

> *"Answer using ONLY the information in those sources. You may have your own knowledge about this breed. Do not use it. If a fact is not in the sources, it does not go in your answer."*

A prompt that only says "use the provided documents" leaves the model free to blend in training knowledge, because it isn't being told not to. The full prompt also requires a `[n]` citation on every factual sentence, requires the exact refusal wording "The documents I have don't cover that", requires disagreements between sources to be surfaced rather than silently resolved, and forbids adding advice of its own ("consult your veterinarian" unless a source says it). Temperature is 0.1.

**2. A structural refusal that never reaches the model.** Chroma always returns *k* chunks — there is no "nothing found" result. So chunks further than 0.85 cosine distance are discarded, and if nothing survives, `answer()` returns a refusal **without calling the model at all**. No prompt can be talked around if there is no prompt.

I measured where to set that threshold and it does less than I hoped:

| Query | Best distance | Covered by my documents? |
|---|---|---|
| "why is being overweight bad" | 0.382 | yes |
| "which breeder should I buy from" | 0.445 | **no** |
| "how much does a Labrador cost" | 0.533 | **no** |
| "is crating cruel" | 0.751 | yes |
| "how do I change a car tyre" | 0.769 | no |
| "what is the capital of France" | 0.848 | no |

An off-topic dog question scores *better* than a real question of mine. Any threshold tight enough to reject the breeder question would also reject my own crating question. So the filter only catches queries with nothing to do with dogs, and the prompt does the real refusing. Being honest about that: the filter is a backstop, not the defence.

**3. Attribution built by code, not by the model.** This is the part I'd defend hardest. The source list under every answer is built from the chunks retrieval actually returned — filename, chunk position and distance — so it cannot be forgotten or invented. On top of that, `check_citations()` parses the `[n]` markers the model wrote and checks them against the sources it was given. If it cites `[9]` when it had six sources, or writes no citations at all, a warning is printed. Attribution that depends on the model behaving is not attribution.

**How source attribution is surfaced:** every answer is followed by a numbered source list naming the document, the file, the chunk position and the distance, with the sources the model actually cited marked.

---

## Example Responses

**Grounded response 1**

Query: *How can I tell if my Italian Greyhound is cold?*

Response:
> You can tell an Italian Greyhound is cold by looking for these signs:
> - Their ears feel cold to the touch – cold ears mean the whole dog is feeling chilly [4].
> - They may "snowball," curling up tightly with their tail draped over their nose as they try to conserve body heat [3].
> - Because sighthounds normally run at a higher base temperature than people, they should feel warm when you touch them; if they feel cool, they are likely cold [6].

Source attribution:
```
• [2] Houndtees - Keeping Your Sighthound Warm (cited in the answer)
      file: houndtees__keeping_your_sighthound_warm.txt  chunk 0  distance 0.438
• [3] Houndtees - Keeping Your Sighthound Warm (cited in the answer)
      file: houndtees__keeping_your_sighthound_warm.txt  chunk 3  distance 0.52
• [4] Houndtees - Keeping Your Sighthound Warm (cited in the answer)
      file: houndtees__keeping_your_sighthound_warm.txt  chunk 5  distance 0.557
• [6] Houndtees - Keeping Your Sighthound Warm (cited in the answer)
      file: houndtees__keeping_your_sighthound_warm.txt  chunk 7  distance 0.606
```

**Grounded response 2**

Query: *Do Italian Greyhounds get along with cats?*

Response:
> Italian Greyhounds can get along with cats, but the outcome varies. Some IGs become "obsessed with chasing cats," while other pairs learn to become great friends [1]. More often than not, cats tend to be more particular about a dog entering their home than the dog is about the cat [4]. Additionally, some Italian Greyhounds have had negative experiences with cats—being attacked or scratched—and may be scared of them [6].

Source attribution: all six chunks from `iggy_rescue__other_pets_and_italian_greyhounds.txt`, chunks 0, 5, 18, 19, 20, 21, distances 0.363–0.509. Four were cited.

This answer is worth comparing to what the same model says with no retrieved context: *"Yes—Italian Greyhounds can get along very well with cats… their temperament, size, and prey drive make them generally cat-friendly."* That is smoother, confident, and flatly less accurate than what the rescue actually says. The grounded answer keeps the rescue's hedge, because the rescue's real position is "it depends on the individual dog".

**Out-of-scope query**

Query: *How much should I pay for an Italian Greyhound puppy?*

System response (refusal):
> The documents I have don't cover the price of an Italian Greyhound puppy. The closest cost information they provide is that a dog without dental care at home will need regular veterinary dental cleanings that can cost "a few hundred dollars every year" [1], that dog tooth brushes and paste are sold at "a very reasonable cost" [2], and that expressing a dog's anal glands at a clinic or grooming salon is done for "a small fee" [3].

It refuses, then offers the nearest thing the documents genuinely contain, with citations — rather than inventing a price range, which is exactly what an ungrounded model produces here.

I also tested a question the model certainly knows from training: *"What were Italian Greyhounds originally bred for in ancient Rome?"* It refused rather than answering from memory.

---

## Query Interface

A Gradio web page, launched with `python app.py` at `http://localhost:7860`.

**Input fields:** a single text box labelled "Your question", with an "Ask" button. Pressing Enter also submits. Five example questions are shown below the box, one of which ("Which breeder should I buy a puppy from?") is there so the refusal behaviour is visible without having to think of an out-of-scope question.

**Output format:** two boxes. "Answer" holds the generated text with `[n]` citation markers. "Retrieved from" holds the numbered source list — source name, filename, chunk position and distance — with the sources the answer cited marked as such, plus warnings if the model invented a citation or omitted them.

There is also a command-line version: `python generate.py "your question"` for one question, or `python generate.py` for a loop.

**Sample Interaction Transcript**

> **User:** Do Italian Greyhounds get along with cats?

> **System:** Italian Greyhounds can get along with cats, but the outcome varies. Some IGs become "obsessed with chasing cats," while other pairs learn to become great friends [1]. More often than not, cats tend to be more particular about a dog entering their home than the dog is about the cat [4]. Additionally, some Italian Greyhounds have had negative experiences with cats—being attacked or scratched—and may be scared of them [6]. The rescue organization notes that many people ask whether IGs "tolerate cats," indicating that compatibility is a common concern [5].
>
> **Sources:**
> ```
>  *[1] Iggy Rescue - Other Pets and Italian Greyhounds
>       file: iggy_rescue__other_pets_and_italian_greyhounds.txt  chunk 21  distance 0.363
>   [2] Iggy Rescue - Other Pets and Italian Greyhounds
>       file: iggy_rescue__other_pets_and_italian_greyhounds.txt  chunk 19  distance 0.422
>   [3] Iggy Rescue - Other Pets and Italian Greyhounds
>       file: iggy_rescue__other_pets_and_italian_greyhounds.txt  chunk 5   distance 0.432
>  *[4] Iggy Rescue - Other Pets and Italian Greyhounds
>       file: iggy_rescue__other_pets_and_italian_greyhounds.txt  chunk 18  distance 0.442
>  *[5] Iggy Rescue - Other Pets and Italian Greyhounds
>       file: iggy_rescue__other_pets_and_italian_greyhounds.txt  chunk 0   distance 0.487
>  *[6] Iggy Rescue - Other Pets and Italian Greyhounds
>       file: iggy_rescue__other_pets_and_italian_greyhounds.txt  chunk 20  distance 0.509
>   * = cited in the answer above
> ```

---

## Evaluation Report

All 5 questions from planning.md, run through the finished system.

| # | Question | Expected answer | System response (summarised) | Retrieval quality | Response accuracy |
|---|---|---|---|---|---|
| 1 | Do Italian Greyhounds bark a lot? | No — generally quiet, not as vocal as many breeds, though they may bark when excited, nervous or seeking attention | "Generally not excessive barkers and relatively quiet compared with many other breeds [2]. However, like all dogs they may bark in response to certain stimuli such as excitement, nervousness, or when seeking attention [1]." | Relevant | **Accurate** |
| 2 | What are the early signs of Progressive Retinal Atrophy? | Night blindness and dilated pupils; genetic, gradual, no known treatment | "Night blindness and dilated pupils [1]. Affected dogs are born with normal vision that then gradually declines over time [3]." | Relevant | **Accurate** |
| 3 | Why is it bad for an IG to be overweight? | Not built to carry weight; increases workload on organs, reduces life expectancy, raises risk of leg break and orthopedic problems | "Excess weight puts extra strain on vital organs, shortening life expectancy, and adds stress to muscles, bones and joints, raising the risk of fractures and orthopedic problems [1]. IGs are not built to carry extra weight [2]. Extra calories from people food must be accounted for [4]." | Relevant | **Accurate** |
| 4 | What reason do rescue groups give for saying a crate is not cruel? | Because dogs are den animals and should have their own "room" | "Because it's meant to be a short-term, positive tool that helps train the breed and reassures the dog that you'll be back [1][2]." | **Off-target** | **Partially accurate** |
| 5 | How tall and heavy is a typical IG? | Withers height 13–15 in (33–38 cm), weight 7–14 lb (3–6 kg), lifespan 12–15 years | "About 13–15 inches (33–38 cm) at the withers and roughly 7–14 lb (3–6 kg) [1]. Another source gives a standing height of 17–20 inches (43–51 cm) [2]. The two sources differ on the height measurement." | Relevant | **Partially accurate** |

**Retrieval quality:** Relevant / Partially relevant / Off-target
**Response accuracy:** Accurate / Partially accurate / Inaccurate

**Score: 3 accurate, 2 partially accurate, 0 inaccurate.**

Notes on the two partials:

**Question 4** is the failure case analysed in full below. The retrieved chunks were about crates, but the specific chunk containing the documented reason was ranked 20th and never reached the model. The answer it gave is supported by the chunks it *did* get, so it isn't a hallucination — it's a true statement that doesn't answer the question asked.

**Question 5** is a subtler and more interesting partial. The system correctly reported withers height and weight, then noticed a second measurement (17–20 in) and flagged the two as contradictory. They aren't: withers height is measured to the shoulder and standing height to the top of the head, so both figures are correct and describe different things. The source page labels them clearly, but chunking separated the two measurements from the labels that distinguished them, so the model saw two conflicting heights with no way to tell them apart. Flagging the conflict was the right behaviour given what it could see; the conflict itself is an artefact of my chunking. It also omitted lifespan, which is present in the same chunk.

---

## Failure Case Analysis

**Question that failed:** *"What reason do rescue groups give for saying a crate is not cruel for an Italian Greyhound?"*

**What the system returned:**

> "Rescue groups say a crate isn't cruel because it's meant to be a short-term, positive tool that helps train the breed and reassures the dog that you'll be back — making crate use helpful and even essential for Italian Greyhounds [1][2]."

**What it should have returned:** the documented reason, which appears almost verbatim in my collection — *"Crating is not cruel as dogs are den animals and should have their own 'room'."*

**Root cause: query-side embedding dilution at the retrieval stage.**

The chunk containing that sentence was ranked **20th, at distance 0.625**. Only the top 6 are passed to the model, so it never saw the answer and wrote a reasonable answer from the neighbouring chunks instead.

The reason isn't that the chunk is bad. It's that the *question* is long. I tested the same question at four lengths:

| Query | Words | Rank of the chunk holding the answer |
|---|---|---|
| "Is crating cruel?" | 3 | **1** |
| "Is crating an Italian Greyhound cruel?" | 6 | **1** |
| "Why is a crate not cruel?" | 6 | 7 |
| "What reason do rescue groups give for saying a crate is not cruel for an Italian Greyhound?" | 17 | **20** |

An embedding is an average over every token. The framing words in the long version — *what reason, do rescue groups, give for saying* — are eleven tokens of scaffolding that carry no information about crates, and they pull the query vector toward chunks about rescue processes and training goals. The two chunks that outranked the answer are about conditioning a dog to see the crate as "positive and short term" and about crate use being "imperative for training this breed" — both closer to a query about what rescues say and why than to the flat statement of fact I wanted.

This is the same mechanism I diagnosed and fixed on the chunk side. Earlier, the sentence "Crating is not cruel as dogs are den animals" scored 0.694 similarity on its own but only 0.072 inside a 898-character chunk, because the surrounding sentences averaged it away. I fixed that by cutting chunk size from 1,000 to 200 characters. What I did not realise is that **the same dilution happens to the query**, and I can't fix that by changing my documents — the user writes the query.

**What I would change to fix it:**

1. **Strip framing words from the query the same way I strip the breed name.** I already treat "Italian Greyhound" as a stopword because every document contains it. Phrases like "what reason do X give for saying" are query scaffolding with the same problem — they add tokens without adding meaning. Testing showed the short form retrieves at rank 1, so this alone would fix it.
2. **Retrieve using several rephrasings of the question** and merge the results, so a badly-worded query gets a second chance.
3. **Combine embedding search with keyword search.** The word "cruel" appears in exactly one chunk in all 282. A keyword match would have found it instantly, where semantic similarity buried it at rank 20. This is the more robust fix, and the failure is a good argument for why production systems use hybrid retrieval rather than embeddings alone.

I have deliberately not implemented these. The failure is real and reproducible, and I'd rather report it accurately than tune the system until my own test questions pass.

---

## Spec Reflection

**One way the spec helped during implementation:**

Writing the Documents and Chunking Strategy sections *before* any code meant I had actually read my sources, and that shaped the code in a way it wouldn't have been otherwise. Because I'd noted that the Southern Cross Vet page carries more menu text than article text, boilerplate removal was in the plan from the start rather than something I discovered when my chunks turned out to be lists of links. The same applies to the two very short sources — I'd written down that the Adopt-a-Pet answer was only about 70 words, so when I wrote the chunker I knew not to impose a minimum chunk size that would have merged or discarded it.

The evaluation questions were the more valuable half. Having five specific, checkable questions written down before I built anything gave me a measurement I could run at every stage. When I changed the chunk size, I could tell in seconds whether it made things better or worse — 5/5 at 200 characters against 4/5 at 1,000 — instead of eyeballing a few results and guessing. Almost every fix in this project came from that number dropping.

**One way the implementation diverged from the spec, and why:**

The chunk size, and the reasoning behind it, was wrong.

planning.md specified **1,000 characters with 150 overlap**, reasoning that a chunk should hold one complete section, since each health issue on the vet page runs 150–200 words and each housetraining section is similar. One section, one question, one answer. That reasoning is intuitive and it is wrong, and I only found out because retrieval failed.

What I hadn't understood is that an embedding is an *average* over everything in the chunk. A whole section contains the one sentence that answers the question plus eight sentences that don't, and the eight drown out the one. I measured it directly: the sentence "Crating is not cruel as dogs are den animals" scores 0.694 similarity against "Is crating cruel?" on its own, but only 0.072 inside its 898-character chunk. Adding a single neutral sentence about crates being a useful training tool dropped it from 0.598 to 0.340.

So the implementation uses **200 characters with 30 overlap** — five times smaller than specified. I tested 200, 450, 600 and 1,000 against my five evaluation questions; 200 and 450 both answered 5/5 while 600 and 1,000 answered 4/5, and 200 gave the lowest distances. The cost is real and visible in the Sample Chunks above: a chunk is now one or two sentences rather than a whole section, and some chunks are thin on their own.

Two smaller divergences came from the same testing. The spec said to put the source name at the front of every chunk — I still do for display, but I stopped *embedding* it, because having the same rescue group's name and the words "Italian Greyhound" inside all 282 vectors swamped the words that actually distinguish chunks. And the spec described plain recursive splitting; the implementation also starts a new chunk at every section heading, for the same anti-dilution reason.

---

## AI Usage

**Instance 1 — generating the ingestion and chunking code**

- *What I gave the AI:* my Chunking Strategy section from planning.md (1,000 characters, 150 overlap, recursive splitting, source name on each chunk), my Documents section describing the file types, and the note that my saved pages still contained menus and footers.
- *What it produced:* a working `load_documents()` and `chunk_text()` matching the spec, plus a `clean_text()` that fixed HTML entities, stripped tags, and dropped short lines with no sentence punctuation.
- *What I changed or overrode:* the cleaning was far too weak, and I only found out by testing it against the specific junk types the assignment lists. Navigation runs, cookie banners and footer legal lines all sailed through, because cookie banners are written as complete sentences and so passed the punctuation test. I added a junk-phrase list and, more usefully, a rule the AI hadn't thought of: a menu is a *run* of short unpunctuated lines while a real heading sits alone between paragraphs, so run length distinguishes them.

  I also had to correct a bug in the generated chunker. It added the source label to each chunk *after* packing, so a full chunk plus a long source name came out over the 1,000-character limit. And later I found the AI's `clean_text` joined lines with a single newline while its `chunk_text` split paragraphs on blank lines — meaning every document arrived as one enormous paragraph and the paragraph-splitting step never ran at all. The code looked correct and produced plausible chunks; it was silently doing sentence splitting on everything.

**Instance 2 — debugging a retrieval failure**

- *What I gave the AI:* a failing query ("why is it bad to be overweight?"), the chunks it returned with their distances, and the assignment's debugging checklist. The checklist suggests that loosely related results mean chunks are too *small* and to try larger ones.
- *What it produced:* an initial diagnosis that agreed with my own guess — that the answer was buried in a chunk covering several topics — and a suggestion to strip boilerplate more aggressively.
- *What I changed or directed differently:* I asked for the hypothesis to be **measured rather than argued**, by rebuilding the index at 500/700/1,000/1,400/2,000 characters and counting how many of my five questions retrieved their answer. That inverted the checklist's advice: smaller chunks were better, not larger, and the best size was 200.

  The measurement also exposed something neither of us had suspected. One question failed at *every* chunk size, which meant it wasn't a chunking problem at all — the cleaning code was deleting the answer. The page says "Crating is **not** cruel as dogs are den animals", and the bold word splits that sentence into three pieces in the HTML; the rule that dropped lowercase fragments was throwing the third piece away. I directed the fix to rejoin fragments onto unfinished lines rather than dropping them, and checked specifically that the word "not" survived — the careless version of that fix stores "Crating is cruel" and inverts the meaning.

**Instance 3 — writing the grounding prompt**

- *What I gave the AI:* the requirement that answers come only from retrieved context, with source attribution.
- *What it produced:* a system prompt instructing the model to "answer based on the provided documents" and to cite sources.
- *What I changed or overrode:* that phrasing suggests grounding rather than enforcing it — it never tells the model not to use what it already knows, and the model knows plenty about this breed. I rewrote it to name the failure mode directly: *"You may have your own knowledge about this breed. Do not use it."* I also rejected the idea of letting the model produce its own source list, and built the attribution in code from the retrieved chunks instead, with a checker that verifies the `[n]` markers point at sources that actually exist. Attribution that depends on the model behaving is not attribution.

  Testing found a bug in my own checker, too: it flagged correctly-cited answers as uncited, because the model writes `【2】` and `【1†L1-L2】` rather than `[2]`. A verification tool that cries wolf is worse than none, because you learn to ignore it.
