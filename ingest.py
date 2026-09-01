"""
Milestone 3: load my documents and split them into chunks.

Follows the Chunking Strategy section of planning.md:
  - recursive splitting (paragraphs first, then sentences)
  - 1,000 characters per chunk
  - 150 characters of overlap
  - source name at the front of every chunk

Documents live in documents/ as plain .txt files. The first line of each
file should be the source name, like:

    Southern Cross Vet - 10 Common Health Issues

Run it with:  python ingest.py
"""

import random
import re
from pathlib import Path

DOCS_DIR = Path("documents")

# I started at 1,000 characters because that's about the size of one section
# in my documents. Testing retrieval showed that was too big: a section holds
# one useful sentence plus a lot of other material, and the embedding
# averages over all of it, so the useful sentence gets washed out. Measuring
# my 5 test questions at several sizes, 450 was the best -- see the Chunking
# Strategy section of planning.md.
CHUNK_SIZE = 200      # characters
OVERLAP = 30          # characters (about 15%)

# Lines containing any of these are site furniture, never article text.
# This catches cookie banners and footers, which are full sentences and so
# would otherwise sneak past my punctuation check below.
JUNK_PHRASES = [
    "cookie", "privacy policy", "terms of service", "all rights reserved",
    "©", "copyright", "subscribe", "newsletter", "sign up", "log in",
    "read more", "share on", "share this", "follow us", "sponsored",
    "advertisement", "skip to content", "back to top", "click here",
    "add to cart", "related questions", "you may also like",
    "comment", "reply", "posted by", "leave a", "sign in",
    # One of my sources is a shop, so its pages carry promo banners.
    "free shipping", "shipping over", "tariff", "duties included",
    "something went wrong", "% off", "checkout", "in stock", "sold out",
    "use your data", "opt out", "your preferences",
]

# Whole lines that are always buttons or placeholders. These are matched
# against the entire line, not as a substring, because words like "send"
# and "search" turn up inside real sentences all the time.
JUNK_LINES = {
    "loading", "loading...", "send", "search", "menu", "home", "next",
    "previous", "enter e-mail", "enter email", "your email", "submit",
    "close", "open", "more", "back",
}


# ---------------------------------------------------------------------------
# Step 1: load
# ---------------------------------------------------------------------------

def load_documents():
    """Read every .txt file in documents/.

    Returns a list of dicts: {"source": ..., "filename": ..., "text": ...}
    The first line of the file is the source name, the rest is the content.
    """
    documents = []

    for path in sorted(DOCS_DIR.glob("*.txt")):
        raw = path.read_text(encoding="utf-8").strip()
        if not raw:
            print(f"  WARNING: {path.name} is empty, skipping")
            continue

        lines = raw.split("\n")
        source = lines[0].strip().lstrip("# ").strip()
        body = "\n".join(lines[1:]).strip()

        # If the file has no title line, fall back to the filename.
        if not body:
            source = path.stem.replace("_", " ")
            body = raw

        documents.append({"source": source, "filename": path.name, "text": body})

    return documents


# ---------------------------------------------------------------------------
# Step 2: clean
# ---------------------------------------------------------------------------

def find_repeated_lines(cleaned_documents, appears_in=3):
    """Find lines that show up in lots of different documents.

    Four of my sources are pages on the same rescue website, and every one
    of them carries the same banner: "Wren is a fighter...", "ITALIAN
    GREYHOUND SCAM WARNING", "ScamPulse.com". Those are real sentences on
    the right topic, so none of my other rules catch them.

    The giveaway is that they appear on every page. Anything showing up in
    3 or more of my 10 documents is site furniture, not article content.
    """
    counts = {}
    for text in cleaned_documents:
        for line in set(text.split("\n")):
            line = line.strip()
            if line:
                counts[line] = counts.get(line, 0) + 1

    return {line for line, count in counts.items() if count >= appears_in}


def is_real_content(line):
    """Is this line article text, or is it site furniture?

    Three checks, in order:
      1. Anything on the junk list is out. This is how cookie banners and
         footers get caught, since those are written as full sentences.
      2. Anything with sentence punctuation is real writing, keep it.
      3. Anything left has no punctuation. That's either a heading
         ("Feeding and Weight Maintenance") or a row of menu links
         ("Find a pet Adopt a dog Adopt a cat"). Headings are short and
         only a few words, so I use word count to tell them apart.
    """
    lowered = line.lower()
    if lowered.strip(" .:") in JUNK_LINES:
        return False
    if any(phrase in lowered for phrase in JUNK_PHRASES):
        return False

    # Phone numbers and other bare numbers. The vet page lists its clinic
    # numbers right above the article, and they were ending up at the top of
    # my first chunk.
    digits = sum(c.isdigit() for c in line)
    if digits and digits >= len(line.replace(" ", "")) * 0.6:
        return False

    if re.search(r"[.!?]", line):
        return True

    return len(line) <= 60 and len(line.split()) <= 7


def drop_menu_runs(lines, run_length=3):
    """Remove navigation menus by looking at how the lines are grouped.

    A real heading sits by itself with paragraphs around it:

        Crates                          <- heading, alone
        Crates can be a very positive...

    A menu is a long stack of short lines all in a row:

        Find a pet                      <- menu
        Adopt a dog                     <- menu
        Adopt a cat                     <- menu

    So a short line is only a heading if it isn't part of a run of them.
    This is what finally got the Adopt-a-Pet menu out of my documents --
    checking each line on its own could never tell the two cases apart.
    """
    def is_short(line):
        if not line:
            return False
        # A short question on its own line is almost always a link to
        # another page ("Do Italian Greyhounds shed?"), not writing.
        if line.endswith("?") and len(line) < 60:
            return True
        return not re.search(r"[.!?]", line)

    kept = []
    i = 0
    while i < len(lines):
        if not is_short(lines[i]):
            kept.append(lines[i])
            i += 1
            continue

        # Found a short line -- see how many short lines follow it.
        run_start = i
        while i < len(lines) and (is_short(lines[i]) or not lines[i]):
            i += 1
        run = [line for line in lines[run_start:i] if line]

        # A short run is headings, a long run is a menu.
        if len(run) < run_length:
            kept.extend(run)

    return kept


def drop_fragments_and_repeats(lines):
    """Last tidy-up pass.

    Gets rid of two things I kept seeing when I read the cleaned files:
      - Half-sentences left behind when a page splits a sentence across
        several boxes, like ", Kinship Partners, Inc." or "for details
        about how we use your data." They give themselves away by starting
        with a lowercase letter or a punctuation mark.
      - The same line printed twice, which happens when a page shows its
        title as both a heading and a breadcrumb.
    """
    kept = []
    seen = set()

    for line in lines:
        if not line:
            kept.append(line)
            continue

        # A real sentence or heading starts with a capital letter, a digit,
        # or a quote mark. Anything else is a piece of a sentence.
        is_fragment = not re.match(r'["\'(\w]', line) or line[0].islower()

        if is_fragment:
            # A piece starting with punctuation (", Kinship Partners, Inc.")
            # is leftover footer text, not the rest of a sentence. Only a
            # piece starting with a lowercase letter is a real continuation.
            if not line[0].islower():
                continue

            # If the line above it is also unfinished, these two are halves
            # of one sentence that the page split apart -- usually because a
            # word in the middle was bold or a link. Join them back together.
            #
            # This matters. The housetraining page says "Crating is **not**
            # cruel as dogs are den animals", and the bold "not" broke it
            # into three pieces. I used to delete the lowercase piece, which
            # quietly threw away the answer to one of my test questions.
            if kept and kept[-1] and not re.search(r"[.!?:]$", kept[-1]):
                kept[-1] = kept[-1] + " " + line
            # Otherwise the sentence above it is complete, so this really is
            # leftover junk (", Kinship Partners, Inc.") and it goes.
            continue

        if line.lower() in seen:
            continue
        seen.add(line.lower())

        kept.append(line)

    return kept


def clean_text(text):
    """Tidy up text that was copied out of a web page."""

    # Fix HTML entities that sometimes survive a copy-paste.
    replacements = {
        "&amp;": "&", "&nbsp;": " ", "&quot;": '"', "&#39;": "'",
        "&lt;": "<", "&gt;": ">", " ": " ",
        "‘": "'", "’": "'", "“": '"', "”": '"',
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)

    # Drop any leftover HTML tags.
    text = re.sub(r"<[^>]+>", " ", text)

    lines = []
    for line in text.split("\n"):
        line = re.sub(r"[ \t]+", " ", line).strip()

        if line and not is_real_content(line):
            continue

        lines.append(line)

    lines = drop_menu_runs(lines)
    lines = drop_fragments_and_repeats(lines)

    # Join with a BLANK line between blocks, not a single newline. Each line
    # I kept is its own paragraph or heading, and the chunker looks for
    # blank lines to find paragraph breaks. When I joined with "\n" the
    # whole document came out as one giant paragraph, so the chunker skipped
    # straight to sentence splitting every time and never split on
    # paragraphs at all -- the opposite of the strategy in planning.md.
    text = "\n\n".join(line for line in lines if line.strip())

    return text.strip()


# ---------------------------------------------------------------------------
# Step 3: chunk
# ---------------------------------------------------------------------------

def is_heading(piece):
    """A heading is a short line with no sentence punctuation in it."""
    return len(piece) <= 100 and not re.search(r"[.!?]", piece)


def split_into_sentences(paragraph):
    """Break a paragraph after . ! or ? followed by a space.

    Not every full stop ends a sentence. The vet page lists the causes of
    seizures as "a. Stress b. Allergic reactions c. Low blood sugar d.
    Cancer", and splitting on every full stop turned that into fragments
    like "Low blood sugar d." -- a chunk that says nothing and could still
    be retrieved for a question about seizures.

    So I don't split after:
      - a single letter ("a." "d."), which is a list marker
      - a common title ("Dr." "Mr." "St.")
      - a number ("4." in a numbered list)
    """
    # Each lookbehind has to reach back past the full stop itself, so they
    # all include the "\." -- my first attempt checked the character
    # immediately before the split point, which is always the full stop, so
    # none of the rules did anything.
    #
    # \b before a single letter is what makes "d." (a list marker) different
    # from "and." (the end of a sentence).
    pattern = (
        r"(?<!\b[A-Za-z]\.)"                  # a. b. c. d.
        r"(?<!\b\d\.)(?<!\b\d\d\.)"           # 4. 10.
        r"(?<!\bDr\.)(?<!\bMr\.)(?<!\bMs\.)"  # titles
        r"(?<!\bSt\.)(?<!\bvs\.)(?<!\betc\.)"
        r"(?<=[.!?])\s+"
    )
    parts = re.split(pattern, paragraph)
    return [p.strip() for p in parts if p.strip()]


def chunk_text(text, source, chunk_size=CHUNK_SIZE, overlap=OVERLAP):
    """Split one document into chunks.

    Recursive means: try paragraphs first. If a paragraph is too big on its
    own, break it into sentences. Only cut mid-sentence as a last resort.
    """
    # The source name goes on the front for display, but it isn't part of
    # what gets embedded any more, so it doesn't eat into the chunk budget.
    label = f"{source}: "

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    # Build a list of pieces that are all small enough to fit in a chunk.
    pieces = []
    for paragraph in paragraphs:
        if len(paragraph) <= chunk_size:
            pieces.append(paragraph)
            continue

        # Too long, so go down a level to sentences.
        for sentence in split_into_sentences(paragraph):
            # A sentence longer than the limit is kept whole and allowed to
            # go over, rather than sliced in the middle. Slicing produced
            # chunks that trailed off like "...because of their slim", which
            # are useless on their own. A slightly oversized chunk is a much
            # smaller problem than a broken one.
            pieces.append(sentence)

    # Now pack the pieces into chunks, filling each one up to chunk_size.
    chunks = []
    current = ""

    for piece in pieces:
        # Start a new chunk at every heading, instead of packing the next
        # section on to the end of the last one.
        #
        # This is the fix for my worst retrieval failure. The sentence
        # "Crating is not cruel as dogs are den animals" scores 0.668
        # against the question "is crating cruel?" on its own -- but it was
        # sitting in a 911-character chunk with seven other sentences about
        # crate sizes and bathroom breaks, and the chunk as a whole only
        # scored 0.312. An embedding averages over everything in the chunk,
        # so one useful sentence in a pile of unrelated ones gets washed
        # out. Keeping a chunk to one section keeps it about one thing.
        if is_heading(piece) and current:
            current, _ = move_trailing_headings(current)
            if current.strip():
                chunks.append(current)
            current = piece

        elif not current:
            current = piece
        elif len(current) + 2 + len(piece) <= chunk_size:
            current += "\n\n" + piece
        else:
            # A heading belongs with the text underneath it, so if this
            # chunk ends on one, hand it to the next chunk instead of
            # leaving it dangling at the bottom with nothing after it.
            current, moved = move_trailing_headings(current)

            chunks.append(current)

            # Start the next chunk with the tail of this one, so a sentence
            # sitting on the boundary shows up in both.
            tail = tail_of(current, overlap) if overlap else ""
            current = "\n\n".join(p for p in [tail] + moved + [piece] if p)

            # Carrying the overlap AND a moved heading can push the new
            # chunk over the limit before I've added anything to it. The
            # overlap is the least important of the three, so it goes.
            if len(current) > chunk_size:
                current = "\n\n".join(p for p in moved + [piece] if p)

    if current.strip():
        # Headings at the very end of a document have nothing under them,
        # so they get dropped rather than moved forward.
        current, _ = move_trailing_headings(current)
        if current.strip():
            chunks.append(current)

    # Merge a tiny leftover at the end of a document into the chunk before
    # it. Otherwise the last scrap of a page becomes its own chunk, which is
    # how I ended up with a chunk that was just a rescue group's tagline.
    # A chunk that is only a heading has no information in it. Retrieval
    # still finds it, and the model then cites it as if it were evidence --
    # I got an answer saying "the signs are listed in the 'Signs your
    # sighthound is a chilly billy' section" instead of listing the signs.
    # So a heading-only chunk gets glued onto the front of the next one,
    # even if that pushes the chunk over its size limit.
    merged = []
    for chunk in chunks:
        if merged and is_heading(merged[-1]):
            merged[-1] = merged[-1] + "\n\n" + chunk
        else:
            merged.append(chunk)
    # A heading left at the very end has nothing to attach to, so it goes.
    if merged and is_heading(merged[-1]):
        merged.pop()
    chunks = merged

    # Only merge if it still fits, otherwise I'd blow past my 1,000 limit.
    if (len(chunks) > 1 and len(chunks[-1]) < 250
            and len(chunks[-2]) + len(chunks[-1]) + 2 <= chunk_size):
        chunks[-2] = chunks[-2] + "\n\n" + chunks[-1]
        chunks.pop()

    # Drop anything under 4 words. A chunk that short can't answer a
    # question -- the one this removes is "St Peters.", the vet clinic's
    # location, left over at the end of that document. I checked where to
    # put the line: 4 words removes only that, while 5 would also remove
    # "Use your discretion here.", which at least reads like advice.
    chunks = [c for c in chunks if len(c.split()) >= 4]

    # Attach the source name to each chunk and drop any empties.
    # "text" has the source name on the front, which is what I show to a
    # reader and hand to the LLM. "body" is the same chunk without it.
    #
    # I embed the body, not the text. Putting the source name on every chunk
    # meant every embedding contained "Italian Greyhound" and a rescue
    # group's name, and that shared wording drowned out the words that
    # actually tell chunks apart. Attribution still works because the source
    # is stored in the metadata.
    return [
        {"source": source, "text": f"{label}{c.strip()}", "body": c.strip()}
        for c in chunks
        if c.strip()
    ]


def move_trailing_headings(chunk):
    """Take any headings off the end of a chunk.

    A heading with nothing under it is useless on its own -- a chunk that
    ends with "Basic Medical Care / Routine Medical Care" and stops tells
    you nothing. Those lines belong at the top of the next chunk, with the
    text they introduce.

    Returns the trimmed chunk, plus the headings to move forward.
    """
    pieces = chunk.split("\n\n")
    moved = []

    while len(pieces) > 1 and not re.search(r"[.!?]", pieces[-1]):
        moved.insert(0, pieces.pop())

    return "\n\n".join(pieces), moved


def tail_of(text, overlap):
    """Grab roughly the last `overlap` characters for the next chunk.

    I start the overlap at a sentence boundary if there is one. My first
    version cut at the nearest space, which produced chunks that opened
    mid-sentence like "a very positive, important tool in housetraining" --
    readable, but it looks broken and it starts the chunk on a fragment.
    """
    if len(text) <= overlap:
        return text

    tail = text[-overlap:]

    # Prefer starting right after a . ! or ?
    sentence_start = re.search(r"[.!?]\s+", tail)
    if sentence_start:
        tail = tail[sentence_start.end():]
    else:
        # No sentence break in the tail, so fall back to a word boundary.
        space = tail.find(" ")
        tail = tail[space + 1:] if space != -1 else tail

    # If that left almost nothing, don't bother. I had a chunk start with
    # the single word "Do" because the sentence break happened to fall two
    # characters from the end. A two-letter overlap helps nobody.
    return tail if len(tail.strip()) >= 40 else ""


# ---------------------------------------------------------------------------
# Step 4: run it and look at the results
# ---------------------------------------------------------------------------

def build_chunks():
    documents = load_documents()

    if not documents:
        print(f"No .txt files found in {DOCS_DIR}/")
        print("Save each of your 10 sources as a .txt file there first.")
        return []

    # Clean every document first, then look across all of them for the
    # banners and headers that repeat from page to page.
    for doc in documents:
        doc["cleaned"] = clean_text(doc["text"])

    repeated = find_repeated_lines([d["cleaned"] for d in documents])
    if repeated:
        print(f"Removing {len(repeated)} lines that repeat across documents "
              f"(site banners and headers)\n")

    all_chunks = []
    print(f"{'DOCUMENT':45} {'CHARS':>7} {'CHUNKS':>7}")
    print("-" * 62)

    for doc in documents:
        cleaned = "\n".join(
            line for line in doc["cleaned"].split("\n")
            if line.strip() not in repeated
        )
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
        chunks = chunk_text(cleaned, doc["source"])
        for chunk in chunks:
            chunk["filename"] = doc["filename"]
        all_chunks.extend(chunks)
        print(f"{doc['filename']:45} {len(cleaned):7,} {len(chunks):7}")

    print("-" * 62)
    print(f"{'TOTAL':45} {sum(len(c['text']) for c in all_chunks):7,} {len(all_chunks):7}")

    # Sanity check against the numbers in planning.md.
    sizes = [len(c["text"]) for c in all_chunks]
    print(f"\nChunk size: smallest {min(sizes)}, biggest {max(sizes)}, "
          f"average {sum(sizes) // len(sizes)}")

    if len(all_chunks) < 50:
        print("WARNING: under 50 chunks — my chunks may be too big.")
    elif len(all_chunks) > 2000:
        print("WARNING: over 2,000 chunks — my chunks may be too small.")
    else:
        print("Chunk count is in the expected range.")

    return all_chunks


def print_samples(chunks, how_many=5):
    """Print random chunks so I can read them.

    I started out taking evenly spaced chunks, but that quietly picked the
    same nice-looking ones every time. Switching to random turned up three
    bad chunks in the first draw. The seed just means I get the same five
    back each run, so I can fix something and compare.
    """
    if not chunks:
        return

    print("\n" + "=" * 62)
    print("SAMPLE CHUNKS (random)")
    print("=" * 62)

    random.seed(42)
    for n, chunk in enumerate(random.sample(chunks, min(how_many, len(chunks))), start=1):
        print(f"\n--- Chunk {n} ({len(chunk['text'])} chars) ---")
        print(f"Source file: {chunk['filename']}")
        print(chunk["text"])


def print_one_document(which=0):
    """Print a whole cleaned document so I can read it before chunking.

    I'm looking for: leftover menu text, leftover &amp; or &nbsp;, and
    anything that isn't about Italian Greyhounds. If I see any of that,
    the cleaning needs more work before I go any further.
    """
    documents = load_documents()
    if not documents:
        print(f"No .txt files in {DOCS_DIR}/ yet.")
        return

    doc = documents[which]
    cleaned = clean_text(doc["text"])

    print("=" * 62)
    print(f"CLEANED: {doc['filename']}  ({len(cleaned):,} chars)")
    print("=" * 62)
    print(cleaned)

    # Quick automatic check for the things I'd otherwise miss by eye.
    print("\n" + "-" * 62)
    leftovers = re.findall(r"&\w+;|<[^>]+>", cleaned)
    print("Leftover HTML/entities:", leftovers if leftovers else "none")


if __name__ == "__main__":
    import sys

    # "python ingest.py read" prints one whole document to check the cleaning.
    # "python ingest.py" chunks everything and shows samples.
    if len(sys.argv) > 1 and sys.argv[1] == "read":
        which = int(sys.argv[2]) if len(sys.argv) > 2 else 0
        print_one_document(which)
    else:
        chunks = build_chunks()
        print_samples(chunks)
