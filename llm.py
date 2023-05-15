import json
import pathlib
import textwrap
from json import JSONDecodeError

import openai
from cachier import cachier

from config import config

DEFAULT_MODEL = "gpt-3.5-turbo"

openai.api_key = config["OPENAI_API_KEY"]
cache_folder = pathlib.Path(__file__).parent / ".cache"


@cachier(cache_dir=cache_folder)
def get_openai_emoji(text):
    print(f"Asking OPENAPI emojis for {text}.")
    prompt = textwrap.dedent(
        f"""
Determine if text within triple backticks has a multi-option question.
Return JSON:
If yes: {{"multiple":true, "emojis": {{choice:"emoji"}}}}
If no: {{"multiple":false, "emojis": "single relevant emoji"}}

```{text}```
"""
    )
    messages = [
        {"role": "user", "content": prompt},
    ]

    response = openai.ChatCompletion.create(
        model=DEFAULT_MODEL,
        messages=messages,
        temperature=0,
        top_p=1,
        max_tokens=200,
        frequency_penalty=0,
        presence_penalty=0,
    )
    usage = response["usage"]
    print(f"Used {usage}")
    choice = response.choices[0]["message"]["content"]
    try:
        answer = json.loads(choice)
    except JSONDecodeError:
        print(f"Error decoding JSON: {choice}")
        answer = {"error": True, "multiple": False, "emojis": ""}
        # raise

    return answer
