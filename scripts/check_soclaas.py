from mmfakebench_pipeline.soclaas import SoCLaaSClient, SoCLaaSError

client = SoCLaaSClient()

try:
    response = client.responses_text(
        'Search this exact caption verbatim: "The church that survived the California wildfire." Return source titles and URLs.',
        'You must use web search before answering. Perform the exact-phrase search and include the sources.',
        tools=[{"type": "web_search_preview"}],
        tool_choice="required",
        max_output_tokens=800,
    )

    print("output_types:", [
        item.get("type") for item in response.get("output", [])
    ])
    print("response:", client.text_from_response(response))

except SoCLaaSError as exc:
    print("error:", exc)