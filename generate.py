"""
Milestone 5: answer questions using only my retrieved chunks.

Takes a question, finds the most relevant chunks with search() from embed.py,
and asks a model on Groq to answer using nothing but those chunks.

The whole point here is grounding. Left alone, the model already "knows"
plenty about Italian Greyhounds from its training, and it will happily
answer from that instead of from my documents -- which defeats the purpose,
because then the sources I show underneath the answer are decoration rather
than evidence.

Run it with:  python generate.py            (asks questions in a loop)
              python generate.py "question" (answers one question)

For the web interface, run app.py instead.
"""

import os
import re
import sys

from dotenv import load_dotenv
from groq import Groq

from embed import search

load_dotenv()

# The assignment suggests meta-llama/llama-4-scout-17b-16e-instruct, but my
# key gets a 404 for it -- there are no Llama chat models on my account at
# all. openai/gpt-oss-120b is the largest general model I can actually reach.
# Run  python generate.py --models  to see the current list, and set
# GROQ_MODEL in .env to use a different one.
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

# The chunks are only 200 characters, so related facts often span several of
# them. Eight keeps that context while hybrid retrieval improves their order.
TOP_K = 8

# Chroma always hands back k chunks, even for a question my documents can't
# answer -- there is no "nothing found" result. So I drop anything past this
# distance before the model ever sees it.
#
# I measured where to put the line, and it can't do as much as I hoped:
#
#   "why is being overweight bad"     best 0.382   (mine, should answer)
#   "is crating cruel"                best 0.751   (mine, should answer)
#   "which breeder should I buy from" best 0.445   (NOT in my documents)
#   "how much does a Labrador cost"   best 0.533   (NOT in my documents)
#   "how do I change a car tyre"      best 0.769   (nothing to do with dogs)
#   "what is the capital of France"   best 0.848   (nothing to do with dogs)
#
# An off-topic dog question scores better than a real question of mine, so no
# threshold can separate them. Anything low enough to catch the breeder
# question would also refuse my own crating question.
#
# So 0.85 only catches questions that have nothing to do with dogs at all,
# and the real work of refusing is done by the system prompt. This is worth
# knowing: the filter is a backstop, not the defence.
MAX_DISTANCE = 0.85


SYSTEM_PROMPT = """You answer questions about Italian Greyhounds for people \
deciding whether to get one or learning to care for one.

You will be given numbered sources. Follow these rules exactly:

1. Answer using ONLY the information in those sources. You may have your own \
knowledge about this breed. Do not use it. If a fact is not in the sources, \
it does not go in your answer.

2. Cite the source number after each claim, like [1] or [2]. Every factual \
sentence needs a citation.

3. If the sources do not answer the question, say so plainly: "The documents \
I have don't cover that." Then say what they do cover that is closest. Do not \
guess, and do not fill the gap from memory.

4. If the sources genuinely disagree, say so and give both positions with \
their citations. Do not quietly pick one. But check first that they are \
describing the same thing: two figures with different labels are two \
different measurements, not a contradiction. Report each with its own label.

4b. Give every part of the answer the sources contain. If a source states \
several relevant facts, do not stop after the first one.

4c. Two numbered sources with the same name are two passages from ONE \
document, not two documents. Never write "another source" about them -- \
write "the same source also says", and never present them as disagreeing.

5. If the sources only partly answer the question, answer the part they cover \
and say which part they don't.

6. Do not add advice, warnings, or context of your own. No "consult your \
veterinarian" unless a source says it.

Write plainly, a few sentences. You are summarising what these specific \
documents say, not writing a general article about the breed."""


def format_context(hits):
    """Turn the retrieved chunks into a numbered list for the prompt.

    Each source gets a number, a name, and its text. The numbers are what
    the model cites, and they let me check afterwards whether a claim in the
    answer really came from the chunk it points at.
    """
    # Several of the numbered sources are usually different passages of the
    # same document. Saying so explicitly stops the model reporting two
    # passages of one page as "two sources", which it did on my size
    # question -- it called a withers height and a standing height from the
    # same Dimensions.com page a disagreement between sources.
    seen = {}
    for hit in hits:
        seen[hit["source"]] = seen.get(hit["source"], 0) + 1

    blocks = []
    for n, hit in enumerate(hits, start=1):
        label = hit["source"]
        if seen[label] > 1:
            label += " (one of several passages from this same document)"
        blocks.append(f"[{n}] Source: {label}\n{hit['body_text']}")
    return "\n\n".join(blocks)


def build_messages(question, hits):
    context = format_context(hits)
    user_message = (
        f"Sources:\n\n{context}\n\n"
        f"Question: {question}\n\n"
        f"Answer using only the sources above, with citations."
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]


def retrieve_for(question, k=TOP_K, max_distance=MAX_DISTANCE):
    """Search, then throw away anything too far away to be relevant."""
    hits = search(question, k=k)

    for hit in hits:
        # The stored text has the source name on the front. Strip it so the
        # model reads the chunk itself, and gets the source from the label
        # I add in format_context.
        hit["body_text"] = hit["text"].split(": ", 1)[-1].strip()

    return [hit for hit in hits if hit["distance"] <= max_distance]


def answer(question, k=TOP_K, show_sources=True):
    """Answer one question. Returns (answer_text, hits_used)."""
    hits = retrieve_for(question, k=k)

    # Nothing relevant came back, so don't even call the model. This is the
    # cheapest and most reliable refusal I can do -- no prompt can be
    # jailbroken if there is no prompt.
    if not hits:
        return (
            "The documents I have don't cover that. They're about Italian "
            "Greyhound care: diet, health problems, housetraining, exercise, "
            "keeping them warm, and how they get on with other pets.",
            [],
        )

    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=build_messages(question, hits),
            # Low temperature. I want it repeating the documents, not being
            # creative.
            temperature=0.1,
            max_tokens=500,
        )
    except Exception as e:
        if "model" in str(e).lower():
            return (f"Model '{MODEL}' didn't work: {e}\n"
                    f"Run  python generate.py --models  to see what's available.", hits)
        raise

    return response.choices[0].message.content.strip(), hits


def check_citations(text, hits):
    """Check the [n] markers the model wrote actually point at real sources.

    The model is told to cite, but nothing stops it inventing "[9]" when it
    was only given 6 sources, or writing an answer with no citations at all
    and hoping I don't notice. So I check rather than trust.
    """
    # Match [1] but also 【1】, (1), [1, 5] and 【1†L1-L2】. The model varies
    # its citation style a lot, and my first version only looked for plain
    # square brackets -- so a properly cited answer got flagged as having no
    # citations at all.
    #
    # The group has to be numbers and separators and nothing else. Accepting
    # any short bracketed text read the "(33 - 38 cm)" in a height answer as
    # a citation of source 33, and warned that source 33 didn't exist.
    cited = set()
    citation = re.compile(r"^\s*\d+\s*([,;]\s*\d+\s*)*(†[^\s]*)?$")
    for group in re.findall(r"[\[\(【]([^\]\)】]{0,20})[\]\)】]", text):
        if not citation.match(group):
            continue
        # Split "1, 5" into two citations, then take the number each part
        # starts with. Taking every number in the group was wrong: the
        # citation 【1†L1-L2】 has a stray "2" in it that isn't a source.
        for part in re.split(r"[,;]", group):
            match = re.match(r"\s*(\d+)", part)
            if match:
                cited.add(int(match.group(1)))
    valid = set(range(1, len(hits) + 1))

    return {
        "cited": sorted(cited & valid),
        "invented": sorted(cited - valid),   # numbers with no source behind them
        "uncited": not cited,                # no citations at all
    }


def format_answer(text, hits):
    """Print the answer with its sources listed underneath.

    The source list is built from the chunks that retrieval actually
    returned, not from anything the model said. That's deliberate -- if I
    let the model write its own source list, the attribution would be
    another thing it could get wrong, and the whole point of the sources is
    that they're checkable.
    """
    out = [text]

    if hits:
        check = check_citations(text, hits)

        out.append("\nSources:")
        for n, hit in enumerate(hits, start=1):
            used = "*" if n in check["cited"] else " "
            out.append(f" {used}[{n}] {hit['source']}")
            out.append(f"      file: {hit['filename']}  "
                       f"chunk {hit['position']}  distance {hit['distance']}")
        out.append("  * = cited in the answer above")

        # Warn me when the model didn't follow the citation rule.
        if check["invented"]:
            out.append(f"\nWARNING: the answer cites {check['invented']}, "
                       f"which don't exist. Only [1]-{[len(hits)]} were given.")
        if check["uncited"]:
            out.append("\nWARNING: the answer has no citations, so I can't "
                       "check it against the sources.")

    return "\n".join(out)


def list_models():
    """Print the models my key can use, for when the default stops working."""
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    for model in sorted(client.models.list().data, key=lambda m: m.id):
        print(" ", model.id)


def ask(question):
    text, hits = answer(question)
    print()
    print(format_answer(text, hits))


def repl():
    """Ask questions until I type quit."""
    print("Italian Greyhound guide. Ask a question, or 'quit' to stop.")
    print("Answers come only from my 10 saved sources.\n")

    while True:
        try:
            question = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return

        if question.lower() in {"quit", "exit", "q"}:
            return
        if not question:
            continue

        ask(question)
        print()


if __name__ == "__main__":
    if not os.getenv("GROQ_API_KEY"):
        print("No GROQ_API_KEY found.")
        print("Copy .env.example to .env and put your key in it.")
        print("Free keys: https://console.groq.com")
        sys.exit(1)

    if len(sys.argv) > 1 and sys.argv[1] == "--models":
        list_models()
    elif len(sys.argv) > 1:
        ask(" ".join(sys.argv[1:]))
    else:
        repl()
