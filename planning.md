# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->

My domain is day-to-day care and ownership of Italian Greyhounds — what the breed is actually like to live with, not what a breed profile page says.

This is hard to find through official channels because kennel club and vet clinic pages give you the same short, generic summary for every breed. The real details come from rescue groups and owners: that these dogs get cold and need coats, that they are notoriously difficult to housetrain, and that their legs break easily. That information is spread across a dozen different rescue sites and forum answers, so someone deciding whether this is the right dog for them has to hunt for it one page at a time.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 |Italian Greyhound Rescue Foundation | Italian Greyhound diets | https://www.igrescue.com/html/basics/diet_for_italian_greyhounds.shtml|
| 2 | midatlanticiggyrescue| Housetraining| https://www.midatlanticiggyrescue.com/ig-helptraining/housetraining/|
| 3 | southern cross vet| Health issues| https://southerncrossvet.com.au/10-italian-greyhound-common-health-issues/|
| 4 |Houndtees | cold dogs| https://houndtees.com.au/en-us/blogs/blog/how-to-tell-if-your-sighthound-is-cold-how-to-keep-them-warm?srsltid=AfmBOoqwnl7UugoN1sZGtjNt382BoG-E0VJKtf1_Xj7G84TRIQFnSCzj|
| 5 |dimensions.com |Italian Greyhound size | https://www.dimensions.com/element/italian-greyhound|
| 6 |ig rescue | Color | https://www.igrescue.com/html/basics/coloration_&_patterns.shtml|
| 7 | ig rescue| health| https://www.igrescue.com/html/basics/caring_for_iggys.shtml|
| 8 |italiangreyhoundrescuecharity | Exercise| https://italiangreyhoundrescuecharity.org.uk/about-italian-greyhounds/exercise/|
| 9 | iggy rescue| compatibility with other pets|https://www.iggyrescue.com/html/basics/other_pets_&_italian_greyhounds.shtml |
| 10 | adopt a pet | barking | https://www.adoptapet.com/answers/do-italian-greyhounds-bark-a-lot|

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**

1,000 characters (about 250 tokens).

**Overlap:**

150 characters (15%).

**Strategy:** Recursive chunking.

**Why not the other two:**

Fixed chunking cuts every 1,000 characters no matter what, so it can cut a sentence in half. Semantic chunking splits by meaning, but it's more work to set up. Recursive is in the middle: it tries to split at paragraph breaks first, then at sentences, and only cuts mid-sentence if it has no other choice. My pages have clear paragraphs, so that fits them well.

**Why 1,000 characters:**

I read through my sources first. Most of them are guides broken into sections, and the sections are all about the same length — each of the 10 health issues on the vet page is about 150–200 words, and the housetraining sections are too. That's around 1,000 characters. So one chunk ends up being about one section, and one section usually answers one question.

If I made chunks smaller, like 500, a health issue would get split in two. The disease name would be in one chunk and the symptoms in another, so searching "night blindness" would only find half the answer. If I made them bigger, like 2,000, three different health issues would get squished into one chunk and it would be less clear what that chunk is about.

The 150-character overlap means the end of one chunk is repeated at the start of the next, so a sentence sitting right on the line doesn't get lost.

**How I load the documents:**

Each of my 10 sources is saved as a plain `.txt` file in `documents/`, holding the page's text exactly as it appears on the site.

My first attempt pulled the pages down and tried to pick out the article automatically, using a different rule for each site — one page needed `#main_content`, another needed `article`, the older rescue pages use table layouts with neither. That got complicated fast and broke on the two sites that don't follow the pattern. So I dropped it and went the other way: save all of the page's text, junk included, and let one set of cleaning rules in `ingest.py` sort out the menus and footers afterwards. That's simpler, and it works the same on all 10 pages.

The first line of each file is the source name. That line becomes the label on every chunk that comes out of that file.

**How I clean each document:**

Even copied-by-hand text drags along some junk, so `clean_text()` in `ingest.py` does four things:

1. **Fixes HTML entities.** `&amp;` becomes `&`, `&nbsp;` becomes a space, and curly quotes become straight ones.
2. **Strips any leftover HTML tags** with a regular expression, in case something like `<div>` came along with the copy.
3. **Throws out site furniture**, one line at a time. This is the important part, and it took three tries to get right:
   - Any line containing an obvious junk phrase is dropped — "cookie", "privacy policy", "©", "subscribe", "share on", "comment", "sponsored", and so on. I need this list because cookie banners and footers are written as complete sentences, so my next rule would let them through.
   - Any line with a period, question mark, or exclamation mark is real writing, so I keep it.
   - Whatever's left has no sentence punctuation. That's either a heading ("Feeding and Weight Maintenance") or a row of menu links ("Find a pet Adopt a dog Adopt a cat Find a shelter"). I tell them apart by counting words: 7 words or fewer and under 60 characters is a heading, anything longer is a menu.
4. **Squashes extra blank lines** down to one, since blank lines are what the chunker uses to find paragraph breaks.

I tested this against a list of every junk type the assignment names — nav menus, cookie banners, ads, footers, repeated headers, "Read more" links, share buttons, comment counts — and it removes all of them while keeping real headings, sentences, and spec lines like "Weight: 7-14 lb."

**What it still gets wrong:** a bare short menu item like "Find a pet" survives, because it looks exactly like a real heading such as "Crates." I decided to live with it — the rule that would remove it would also remove my headings, and a stray 10-character line just gets absorbed into the paragraph next to it instead of becoming its own chunk.

**Other things to watch out for:**

- **Two of my sources are really short.** The Adopt-a-Pet barking answer is only about 70 words and the dimensions.com page is mostly measurements. There's no minimum chunk size in my code, so those stay as one small chunk each instead of being merged into something else.
- **The source name takes up room.** I put the source at the front of every chunk, like `Southern Cross Vet - 10 Common Health Issues: ...`, so I can always tell where an answer came from. That label is part of the 1,000 characters, so the code subtracts its length from the budget before packing. Without that, a full chunk plus a long source name came out over 1,000.

**Estimated chunk count:** about 70–100 total.

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

`all-MiniLM-L6-v2`, through the sentence-transformers library. I picked it because it's already in requirements.txt, it runs on my laptop for free with no API key, and it's fast. It handles 256 word-pieces at a time, which is a little under my 1,000-character chunks, so a long chunk may get slightly cut off at the end — something to keep an eye on.

I'm storing the vectors in Chroma.

**Top-k:**

5. My chunks are about one section each, and a lot of my questions touch more than one source — "is this dog right for me" pulls from exercise, barking, and health pages at once. Pulling 5 gives the model enough to work with. If I only pulled 2, I'd probably miss things; if I pulled 10, I'd start feeding it chunks that aren't really related to the question.

**Production tradeoff reflection:**

If this were a real product and money wasn't an issue, here's what I'd think about:

- **Context length.** MiniLM only looks at about 256 word-pieces, so it can miss the tail end of a longer chunk. A model like OpenAI's `text-embedding-3-large` or Voyage's models can take much longer text, which would let me use bigger chunks without losing anything.
- **Accuracy on my topic.** My documents are full of specific terms like "Progressive Retinal Atrophy" and "belly bands." A bigger model would do a better job of understanding those than a small general-purpose one.
- **Speed and where it runs.** MiniLM runs locally and answers instantly. An API model is more accurate but adds a network round-trip to every single search, and my whole document collection would get sent to another company.
- **Other languages.** All of my sources are in English, so I don't need this now. But if I wanted people to be able to ask questions in Spanish, I'd need a multilingual model.

For a class project MiniLM is the right call. For real users I'd probably pay for a hosted model and keep MiniLM as a backup.

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | Do Italian Greyhounds bark a lot? | No — they are generally quiet and not as vocal as many breeds, though they may bark when excited, nervous, or seeking attention. (Adopt-a-Pet) |
| 2 | What are the early signs of Progressive Retinal Atrophy in an Italian Greyhound? | Night blindness and dilated pupils. It's a genetic disease causing gradual permanent blindness, isn't thought to be painful, and has no known treatment. (Southern Cross Vet) |
| 3 | Why is it bad for an Italian Greyhound to be overweight? | IGs aren't built to carry extra weight — it increases the workload on vital organs, shortens life expectancy, and raises the risk of leg breaks and other orthopedic problems by straining muscles, bones, and joints. (IG Rescue Foundation) |
| 4 | What reason do rescue groups give for saying a crate is not cruel for an Italian Greyhound? | Because dogs are den animals and should have their own "room." Crates are described as a positive and important tool for housetraining. (Mid-Atlantic Iggy Rescue) |
| 5 | How tall and heavy is a typical Italian Greyhound? | Withers height about 13–15 in (33–38 cm), weight about 7–14 lb (3–6 kg), lifespan 12–15 years. (dimensions.com) |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. **Menu and footer text getting mixed in with the real content.** The vet page has more words in its menus, footer, and clinic addresses than in the actual article. If I don't strip that out, I'll end up with chunks that are just lists of links, and they could show up as answers. A question like "what should I feed my dog" might match a footer link that says "Nutrition Consults" and the system would give a useless answer that still looks like it came from a real source.

2. **Answers getting split across two chunks.** Even with overlap, a section that runs long will get cut somewhere. The health page is the biggest risk — if the name of a disease lands in one chunk and its symptoms land in the next, then searching for the symptom finds a chunk that doesn't say what the disease is called. My fix for this is putting the source and section name at the top of every chunk so there's always some context attached.

3. **My sources don't always agree.** Different rescue groups say different things about how much exercise these dogs need or what to feed them. When two chunks disagree, the model might blend them into one confident-sounding answer that neither source actually said. I want it to say when sources differ instead of picking one.

4. **Questions my documents can't answer.** Someone will ask about price, breeders, or a different breed entirely. My pages don't cover that, but the search will still return the 5 closest chunks no matter what — there's no "nothing found" result. So the model has to be told to refuse when the chunks it got don't actually answer the question.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

```
   10 sources saved as .txt
   (documents/ folder)
           |
           v
+---------------------------+
| 1. INGESTION + CLEANING   |   load_documents() reads each .txt.
|    Python, pathlib + re   |   clean_text() fixes HTML entities,
|    (ingest.py)            |   strips tags, and drops menus,
|                           |   cookie banners, and footers.
+---------------------------+
           |
           v
+---------------------------+
| 2. CHUNKING               |   Recursive split: paragraphs first,
|    chunk_text()           |   then sentences.
|                           |   1,000 chars, 150 overlap.
|                           |   Add source name to each chunk.
+---------------------------+
           |
           v  ~70-100 chunks
+---------------------------+
| 3. EMBEDDING + STORAGE    |   Turn each chunk into a vector.
|    sentence-transformers  |   Save vector + text + source name
|    all-MiniLM-L6-v2       |   into a Chroma collection.
|    -> Chroma              |
+---------------------------+
           |
           v
     [ vector store ]
           ^
           |  top 5 closest chunks
+---------------------------+
| 4. RETRIEVAL              |   Embed the user's question with the
|    Chroma similarity      |   same model, find the 5 nearest chunks.
|    search, k=5            |
+---------------------------+
           |
           v
+---------------------------+
| 5. GENERATION             |   Send the 5 chunks + the question
|    Groq API (Llama)       |   to the model with a system prompt
|                           |   telling it to only use those chunks
|                           |   and to list its sources.
+---------------------------+
           |
           v
+---------------------------+
| 6. INTERFACE              |   Text box for the question,
|    Gradio (or CLI)        |   answer + source list underneath.
+---------------------------+

           ^
           |
   user types a question
```

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**

- *Tool:* Claude Code.
- *What I'll give it:* my Chunking Strategy section from this file, plus a note that my saved pages still have menus and footers in them.
- *What I expect back:* two functions — one that loads every file in `documents/` and pulls out just the article text, and one `chunk_text()` that splits recursively at paragraphs, then sentences, at 1,000 characters with 150 overlap, and puts the source name at the front of each chunk.
- *How I'll check it:* print the total chunk count and see if it's near my estimate of 70–100. Then print 5 random chunks and read them. I'm looking for chunks that stop mid-sentence, chunks that are just menu links, and whether the two short sources stayed in one piece.

**Milestone 4 — Embedding and retrieval:**

- *Tool:* Claude Code.
- *What I'll give it:* my Retrieval Approach section and the output format of my chunking function.
- *What I expect back:* code that embeds every chunk with `all-MiniLM-L6-v2`, saves them to Chroma along with the source name, and a `search()` function that takes a question and returns the top 5 chunks.
- *How I'll check it:* run my 5 test questions through `search()` and read the chunks that come back before any model touches them. If question 2 doesn't return the PRA chunk, retrieval is broken and there's no point moving on. I'll also try an off-topic question like "how much does a Labrador cost" to see what junk comes back, since that tells me what the generation step will have to refuse.

**Milestone 5 — Generation and interface:**

- *Tool:* Claude Code.
- *What I'll give it:* my `search()` function and my Anticipated Challenges section, especially the parts about sources disagreeing and questions my documents can't answer.
- *What I expect back:* a function that sends the 5 chunks plus the question to Groq with a system prompt saying to only use the provided chunks, to say "I don't know" if they don't cover it, to point out when sources disagree, and to list which sources it used. Plus a small Gradio page with a question box and an answer area.
- *How I'll check it:* run all 5 test questions and compare to my expected answers. Then ask something off-topic and confirm it refuses instead of guessing. Then ask something that's only *half* in my documents to see if it makes up the other half. I'll write down whatever fails for the Failure Case section of the README.

**Where I expect to push back on the AI:** it tends to default to a plain fixed-size split and to skip the boilerplate stripping. It also writes very polite system prompts that don't actually refuse anything. Those are the two places I'll have to be specific.
