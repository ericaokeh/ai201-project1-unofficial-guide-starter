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

import re
from pathlib import Path

DOCS_DIR = Path("documents")

CHUNK_SIZE = 1000     # characters
OVERLAP = 150         # characters

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
        # or a quote mark.
        if not re.match(r'["\'(\w]', line) or line[0].islower():
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

    text = "\n".join(lines)

    # Squash runs of blank lines down to one blank line, which is what the
    # chunker uses to find paragraph breaks.
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ---------------------------------------------------------------------------
# Step 3: chunk
# ---------------------------------------------------------------------------

def split_into_sentences(paragraph):
    """Break a paragraph after . ! or ? followed by a space."""
    parts = re.split(r"(?<=[.!?])\s+", paragraph)
    return [p.strip() for p in parts if p.strip()]


def chunk_text(text, source, chunk_size=CHUNK_SIZE, overlap=OVERLAP):
    """Split one document into chunks.

    Recursive means: try paragraphs first. If a paragraph is too big on its
    own, break it into sentences. Only cut mid-sentence as a last resort.
    """
    # The source name gets stuck on the front of every chunk at the end, so
    # leave room for it now. Otherwise a full chunk plus a long source name
    # comes out over the limit.
    label = f"{source}: "
    chunk_size = chunk_size - len(label)

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    # Build a list of pieces that are all small enough to fit in a chunk.
    pieces = []
    for paragraph in paragraphs:
        if len(paragraph) <= chunk_size:
            pieces.append(paragraph)
            continue

        # Too long, so go down a level to sentences.
        for sentence in split_into_sentences(paragraph):
            if len(sentence) <= chunk_size:
                pieces.append(sentence)
            else:
                # Last resort: one really long sentence, cut it.
                for i in range(0, len(sentence), chunk_size):
                    pieces.append(sentence[i:i + chunk_size])

    # Now pack the pieces into chunks, filling each one up to chunk_size.
    chunks = []
    current = ""

    for piece in pieces:
        if not current:
            current = piece
        elif len(current) + 2 + len(piece) <= chunk_size:
            current += "\n\n" + piece
        else:
            chunks.append(current)
            # Start the next chunk with the tail of this one, so a sentence
            # sitting on the boundary shows up in both.
            current = tail_of(current, overlap) + "\n\n" + piece if overlap else piece

    if current.strip():
        chunks.append(current)

    # Attach the source name to each chunk and drop any empties.
    return [
        {"source": source, "text": f"{label}{c.strip()}"}
        for c in chunks
        if c.strip()
    ]


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
        return tail[sentence_start.end():]

    # No sentence break in the tail, so fall back to a word boundary.
    space = tail.find(" ")
    return tail[space + 1:] if space != -1 else tail


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
    """Print a few chunks spread across the collection so I can read them."""
    if not chunks:
        return

    print("\n" + "=" * 62)
    print("SAMPLE CHUNKS")
    print("=" * 62)

    step = max(1, len(chunks) // how_many)
    for n, chunk in enumerate(chunks[::step][:how_many], start=1):
        print(f"\n--- Chunk {n} ({len(chunk['text'])} chars) ---")
        print(f"Source: {chunk['source']}")
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
