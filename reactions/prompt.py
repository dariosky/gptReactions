import textwrap

from llm import issue_command


def get_openai_emoji(text):
    prompt = textwrap.dedent(
        f"""
            Consider the following text
            ```{text}```

        If the text is a question with multiple options return a JSON string
            {{"multiple":true, "emojis": {{choice:"emoji"}} }}
        Otherwise return a JSON string with
            {{"multiple":false, "emojis": "single relevant emoji"}}
        """
    )
    return issue_command(prompt, temperature=0, return_json=True)
