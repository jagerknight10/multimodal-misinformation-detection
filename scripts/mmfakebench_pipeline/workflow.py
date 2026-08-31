"""Reliable staged multimodal verification workflow for SoCLaaS."""


IMAGE_DESCRIPTION_INSTRUCTIONS = """Describe only what is visibly present in the supplied
image. Extract readable text, names, logos, people, places, events, and other
distinctive clues that could be used for inverse evidence retrieval. Do not judge
the caption."""

EVIDENCE_INSTRUCTIONS = """Retrieve evidence for the supplied news caption using the
web_search_preview tool. Search the exact claim and distinctive entities, including
image-derived clues. Return a concise evidence brief with source titles, URLs when
available, dates, and whether each source supports or contradicts the claim. Do not
make a final benchmark classification. If retrieval fails, say so explicitly."""


def retrieve_evidence(client, caption, image_path, tools, max_output_tokens=1000):
    image_response = client.chat_completions(
        caption, image_path, IMAGE_DESCRIPTION_INSTRUCTIONS, max_tokens=500)
    image_description = client.text_from_chat_response(image_response)
    evidence_prompt = (
        f"News caption:\n{caption}\n\n"
        f"Image-derived clues:\n{image_description}"
    )
    evidence_response = client.responses_text(
        evidence_prompt, EVIDENCE_INSTRUCTIONS, tools,
        max_output_tokens=max_output_tokens)
    return {
        "image_description": image_description,
        "retrieved_evidence": client.text_from_response(evidence_response),
        "image_runtime_seconds": image_response.get("_runtime_seconds"),
        "evidence_runtime_seconds": evidence_response.get("_runtime_seconds"),
        "image_usage": image_response.get("usage"),
        "evidence_usage": evidence_response.get("usage"),
        "evidence_api_response": evidence_response,
    }
