"""
The query interface.

Run it with:  python app.py
Then open:    http://localhost:7860

All the actual work happens in the other three files:
    ingest.py    load the documents and split them into chunks
    embed.py     embed the chunks, store them, search them
    generate.py  ask the model, using only what search found

This file is just the web page.
"""

import gradio as gr

from generate import FOLLOW_UP_WORDS, answer, check_citations
from ingest import load_documents


ALL_SOURCES = "All sources"
SOURCE_CHOICES = [ALL_SOURCES] + sorted(
    {document["source"] for document in load_documents()}
)


def handle_query(question, source_choice, history):
    """Answer one question and retain enough history for a follow-up."""
    if not question.strip():
        return "Ask me something about Italian Greyhounds.", "", history, ""

    history = history or []
    source = None if source_choice == ALL_SOURCES else source_choice
    used_memory = bool(history and FOLLOW_UP_WORDS.search(question))
    text, hits = answer(question, source=source, history=history)
    history = (history + [(question, text)])[-5:]
    status = "Used the previous question for context." if used_memory else ""

    if not hits:
        return text, "Nothing in my documents matched this question.", history, status

    # The source list is built from the chunks retrieval actually returned,
    # not from anything the model wrote. If the model forgets to cite, the
    # sources still show up here.
    check = check_citations(text, hits)

    lines = []
    for n, hit in enumerate(hits, start=1):
        used = " (cited in the answer)" if n in check["cited"] else ""
        lines.append(f"• [{n}] {hit['source']}{used}")
        lines.append(f"      file: {hit['filename']}  "
                     f"chunk {hit['position']}  distance {hit['distance']}")

    if check["invented"]:
        lines.append(f"\nWarning: the answer cites {check['invented']}, "
                     f"which don't exist.")
    if check["uncited"]:
        lines.append("\nWarning: the answer has no citations.")

    return text, "\n".join(lines), history, status


def clear_conversation():
    return "", "", "", [], ""


with gr.Blocks(title="The Unofficial Italian Greyhound Guide") as demo:
    gr.Markdown(
        "# The Unofficial Italian Greyhound Guide\n"
        "Ask about living with an Italian Greyhound — diet, health, "
        "housetraining, exercise, keeping them warm, other pets.\n\n"
        "Answers come **only** from 10 saved rescue, vet and owner pages. "
        "If those pages don't cover something, it says so instead of guessing."
    )

    inp = gr.Textbox(
        label="Your question",
        placeholder="e.g. how do I stop my iggy getting cold at night?",
    )
    source_filter = gr.Dropdown(
        choices=SOURCE_CHOICES,
        value=ALL_SOURCES,
        label="Limit retrieval to one source (optional)",
    )
    btn = gr.Button("Ask", variant="primary")
    clear_btn = gr.Button("Clear conversation")

    answer_box = gr.Textbox(label="Answer", lines=8)
    sources_box = gr.Textbox(label="Retrieved from", lines=8)
    memory_status = gr.Markdown()
    history_state = gr.State([])

    gr.Examples(
        examples=[
            "Do Italian Greyhounds bark a lot?",
            "How can I tell if my Italian Greyhound is cold?",
            "How long can they be left in a crate?",
            "Do they get along with cats?",
            "Which breeder should I buy a puppy from?",
        ],
        inputs=inp,
    )

    query_inputs = [inp, source_filter, history_state]
    query_outputs = [answer_box, sources_box, history_state, memory_status]
    btn.click(handle_query, inputs=query_inputs, outputs=query_outputs)
    inp.submit(handle_query, inputs=query_inputs, outputs=query_outputs)
    clear_btn.click(
        clear_conversation,
        outputs=[inp, answer_box, sources_box, history_state, memory_status],
    )


if __name__ == "__main__":
    demo.launch()
