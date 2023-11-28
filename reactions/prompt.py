import textwrap

from llm import issue_command


def get_openai_emoji(text):
    prompt = textwrap.dedent(
        f"""
            Analyse the following text and return a json output
            describing its relevant content with emojis:
            ```{text}```

        If the text is a question with multiple options return a JSON string
            {{"multiple":true, "emojis": ""{{choice:"emoji"}}"" }}
        Otherwise return a JSON string with
            {{"multiple":false, "emojis": "single relevant emoji"}}

        Example:
        1. Do you want water or wine?
        {{ "multiple":true, "emojis": {{ "water": "💦", "wine": "🍷"}} }}

        2. This is a dog
        {{ "multiple":false, "emojis": "🐶" }}

        3. Good morning
        {{ "multiple":false, "emojis": "☀️" }}

        """
    )
    return issue_command(prompt, temperature=0, return_json=True)
