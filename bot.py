import json
import textwrap

import emoji
import openai
from cachier import cachier
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient

from emoji_map import UNICODE_TO_EMOJI

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
    answer = json.loads(response.choices[0]["message"]["content"])
    return answer


@app.message()
def listen_and_react(body, say, client: WebClient):
    # Check if the message is from a bot to avoid infinite loops
    if "bot_id" in body["event"]:
        return

    text = body["event"]["text"].lower()
    print(f"Looking for an emoji to {text}")
    channel_id = body["event"]["channel"]
    message_ts = body["event"]["ts"]

    response = get_openai_emoji(text)
    multiple = response["multiple"]
    if multiple:
        unicode_emojis = response["emojis"].values()
    else:
        unicode_emojis = response["emojis"]
    for unicode_emoji in unicode_emojis:
        unicode_emoji = unicode_emoji.strip()
        if emoji.is_emoji(unicode_emoji):
            if unicode_emoji in UNICODE_TO_EMOJI:
                slack_emoji_name = UNICODE_TO_EMOJI[unicode_emoji]
                print(unicode_emoji, slack_emoji_name)
                try:

                    client.reactions_add(
                        channel=channel_id,
                        timestamp=message_ts,
                        name=slack_emoji_name,
                    )
                except Exception as e:
                    print(f"Error sending reaction {e}")
            else:
                print(f"Unknown slack-emoji-name for {unicode_emoji}")


def examples():
    print(get_openai_emoji("Dogs or cats?"))
    print(get_openai_emoji("Dogs or cats or wild boars?"))
    print(get_openai_emoji("I didn't see the schedule"))


if __name__ == "__main__":
    handler = SocketModeHandler(app, config["SLACK_APP_TOKEN"])
    handler.start()
