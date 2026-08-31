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
| 1 |Italian Greyhound Rescue Foundation | Itlian Greyhound Diets | https://www.igrescue.com/html/basics/diet_for_italian_greyhounds.shtml|
| 2 | midatlanticiggyrescue| Housetraining| https://www.midatlanticiggyrescue.com/ig-helptraining/housetraining/|
| 3 | southern cross vet| Health issues| https://southerncrossvet.com.au/10-italian-greyhound-common-health-issues/|
| 4 |Houndtees | cold dogs| https://houndtees.com.au/en-us/blogs/blog/how-to-tell-if-your-sighthound-is-cold-how-to-keep-them-warm?srsltid=AfmBOoqwnl7UugoN1sZGtjNt382BoG-E0VJKtf1_Xj7G84TRIQFnSCzj|
| 5 |dimensions.com |Italian Greyhound size | https://www.dimensions.com/element/italian-greyhound|
| 6 |ig rescue | Color | https://www.igrescue.com/html/basics/coloration_&_patterns.shtml|
| 7 | ig rescue| health| https://www.igrescue.com/html/basics/caring_for_iggys.shtml|
| 8 |italiangreyhoundrescuecharity | Exercise| https://italiangreyhoundrescuecharity.org.uk/about-italian-greyhounds/exercise/|
| 9 | iggy rescue| compatability|https://www.iggyrescue.com/html/basics/other_pets_&_italian_greyhounds.shtml |
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

**Two things I have to watch out for:**

1. **Junk text on the pages.** The vet page has about 2,500 words of menus, footers, and clinic addresses — more than the actual article. If I chunk the whole page, some chunks will just be menu links, and a question like "what should I feed my dog" could match a footer link that says "Nutrition Consults." So I need to grab only the article text before chunking.

2. **Two of my sources are really short.** The Adopt-a-Pet barking answer is only about 70 words and the dimensions.com page is mostly measurements. Those should just stay as one small chunk each instead of getting merged with something else.

I'm also going to put the source name at the front of each chunk, like `Italian Greyhound Diet — Weight Maintenance: ...`, so it's easier to tell where an answer came from.

**Estimated chunk count:** about 70–100 total.

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

**Top-k:**

**Production tradeoff reflection:**

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
| 4 | Is crating an Italian Greyhound cruel? | No — crates are described as a positive and important housetraining tool, since dogs are den animals and benefit from having their own space. (Mid-Atlantic Iggy Rescue) |
| 5 | How tall and heavy is a typical Italian Greyhound? | Withers height about 13–15 in (33–38 cm), weight about 7–14 lb (3–6 kg), lifespan 12–15 years. (dimensions.com) |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1.

2.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

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

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
