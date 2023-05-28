import html
from typing import Iterable

import emoji
from slack_sdk import WebClient

from reactions.emoji_map import EMOJI_MAP, UNICODE_TO_EMOJI
from reactions.prompt import get_openai_emoji


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


def react_to_messages(bot):
    @bot.message()
    def listen_and_react(body, client: WebClient):
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
