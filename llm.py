import json
import logging
import pathlib
import textwrap
from json import JSONDecodeError

from cachier import cachier
from openai import OpenAI

from config import config

DEFAULT_MODEL = "gpt-3.5-turbo-1106"

openai_client = OpenAI(api_key=config["OPENAI_API_KEY"])
cache_folder = pathlib.Path(__file__).parent / ".cache"
logger = logging.getLogger(__name__)


@cachier(cache_dir=cache_folder)
def issue_command(text, temperature=0.3, return_json=False):
    prompt = textwrap.dedent(text).strip()
    print(f"Asking OPENAPI {prompt}")
    messages = [
        {"role": "user", "content": prompt},
    ]

    response = openai_client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=messages,
        temperature=temperature,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        response_format={"type": "json_object" if return_json else "text"},
    )
    usage = response.usage
    logger.debug(f"OpenAPI {DEFAULT_MODEL} used: {usage}")
    choice = response.choices[0].message.content
    if return_json:
        try:
            response = json.loads(choice)
        except JSONDecodeError:
            print(f"Error decoding JSON: {choice}")
            raise
        return response
    return choice
