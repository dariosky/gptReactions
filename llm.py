import json
import logging
import pathlib
import textwrap
from json import JSONDecodeError

import openai
from cachier import cachier

from config import config

DEFAULT_MODEL = "gpt-3.5-turbo"

openai.api_key = config["OPENAI_API_KEY"]
cache_folder = pathlib.Path(__file__).parent / ".cache"
logger = logging.getLogger(__name__)


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


@cachier(cache_dir=cache_folder)
def issue_command(text, temperature=0.3, return_json=False):
    prompt = textwrap.dedent(text).strip()
    print(f"Asking OPENAPI {prompt}")
    messages = [
        {"role": "user", "content": prompt},
    ]

    response = openai.ChatCompletion.create(
        model=DEFAULT_MODEL,
        messages=messages,
        temperature=temperature,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )
    usage = response["usage"]
    logger.debug(f"OpenAPI {DEFAULT_MODEL} used: {usage}")
    choice = response.choices[0]["message"]["content"]
    if return_json:
        try:
            response = json.loads(choice)
        except JSONDecodeError:
            print(f"Error decoding JSON: {choice}")
            raise
        return response
    return choice
