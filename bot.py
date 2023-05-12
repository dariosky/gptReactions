import html
import json
import textwrap
from json import JSONDecodeError
from typing import Iterable

import emoji
import openai
from cachier import cachier
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient

from emoji_map import UNICODE_TO_EMOJI, EMOJI_MAP

DEFAULT_MODEL = "gpt-3.5-turbo"

from dotenv import dotenv_values

config = dotenv_values(".env")

app = App(
    token=config["SLACK_BOT_TOKEN"],
    signing_secret=config["SLACK_APP_SIGNING_SECRET"],
)
openai.api_key = config["OPENAI_API_KEY"]


@cachier(cache_dir=".cache")
def get_openai_emoji(text):
    print(f"Asking OPENAPI emojis for {text}.", end="")
    prompt = textwrap.dedent(
        f"""
1. Check if the following text delimited by triple backticks contains a question with multiple choices
2. Return a json formatted in this way:
 If it does return a json object like:
    multiple:true, emojis: <a dictionary with every choice and a relevant emoji>
 If it doesn't: return json object like
    multiple:false, emojis: <one single emoji relevant to the text>

```{text}```
"""
    )
    messages = [
        {"role": "user", "content": prompt},
    ]

    response = openai.ChatCompletion.create(
        model=DEFAULT_MODEL,
        messages=messages,
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

    return answer


def get_reactions(emojis):
    if isinstance(emojis, dict):
        unicode_emojis: Iterable = emojis.values()
    else:
        unicode_emojis: str = emojis
        if (
            formatted_slack_emoji := unicode_emojis.strip(":")
        ) in EMOJI_MAP:  # it's already a slack emoji
            unicode_emoji = html.unescape(EMOJI_MAP[formatted_slack_emoji])
            unicode_emojis = unicode_emoji

    for unicode_emoji in unicode_emojis:
        unicode_emoji = unicode_emoji.strip()
        if emoji.is_emoji(unicode_emoji):
            if unicode_emoji in UNICODE_TO_EMOJI:
                slack_emoji_name = UNICODE_TO_EMOJI[unicode_emoji]
                print(unicode_emoji, slack_emoji_name)
                yield slack_emoji_name
            else:
                print(f"Unknown slack-emoji-name for {unicode_emoji}")
        else:
            print(f"Not an emoji {unicode_emoji}")


def text_to_reactions(text):
    print(f"Looking for reactions `{text}`")
    response = get_openai_emoji(text)
    return [slack_emoji_name for slack_emoji_name in get_reactions(response["emojis"])]


@app.message()
def listen_and_react(body, say, client: WebClient):
    # Check if the message is from a bot to avoid infinite loops
    if "bot_id" in body["event"]:
        return

    text = body["event"]["text"].lower()
    channel_id = body["event"]["channel"]
    message_ts = body["event"]["ts"]

    for slack_emoji_name in text_to_reactions(text):
        try:
            client.reactions_add(
                channel=channel_id,
                timestamp=message_ts,
                name=slack_emoji_name,
            )
        except Exception as e:
            print(f"Error sending reaction {e}")


def examples():
    print(text_to_reactions("Dogs or cats?"))
    print(text_to_reactions("Dogs or cats or wild boars?"))
    print(text_to_reactions("I didn't see the schedule"))


if __name__ == "__main__":
    handler = SocketModeHandler(app, config["SLACK_APP_TOKEN"])
    handler.start()
