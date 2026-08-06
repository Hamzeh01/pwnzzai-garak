"""JSON schema the judge model is constrained to produce.

Ollama's `format` parameter accepts a JSON Schema and constrains generation
to match it -- this is what actually makes a small model like llama3.2:1b
produce reliable structured output, rather than just asking nicely in the
prompt.
"""

JUDGE_RESPONSE_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "verdict": {
            "type": "string",
            "enum": ["success", "failure", "ambiguous"],
        },
        "reasoning": {
            "type": "string",
        },
    },
    "required": ["verdict", "reasoning"],
}
