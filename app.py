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

from generate import answer, check_citations


def handle_query(question):
    """Answer one question and return (answer text, source list)."""
    if not question.strip():
        return "Ask me something about Italian Greyhounds.", ""

    text, hits = answer(question)

    if not hits:
        return text, "Nothing in my documents matched this question."

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

    return text, "\n".join(lines)


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
    btn = gr.Button("Ask", variant="primary")

    answer_box = gr.Textbox(label="Answer", lines=8)
    sources_box = gr.Textbox(label="Retrieved from", lines=8)

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

    btn.click(handle_query, inputs=inp, outputs=[answer_box, sources_box])
    inp.submit(handle_query, inputs=inp, outputs=[answer_box, sources_box])


if __name__ == "__main__":
    demo.launch()
