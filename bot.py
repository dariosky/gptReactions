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
    print(f"Asking OPENAPI for an emoji for {text}.", end="")
    prompt = textwrap.dedent(
        f"""Get only one single representative emoji of the following text:\n\n{text}"""
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
    return response


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
    unicode_emoji = response.choices[0]["message"]["content"]
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
                return
            except Exception as e:
                print(f"Error sending reaction {e} - sending as text")
        else:
            print(f"Unknown slack-emoji-name for {unicode_emoji} - sending as text")
        say(unicode_emoji)


if __name__ == "__main__":
    handler = SocketModeHandler(app, config["SLACK_APP_TOKEN"])
    handler.start()
