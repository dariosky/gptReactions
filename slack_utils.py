import html
from typing import Iterable

import emoji

from emoji_map import EMOJI_MAP, UNICODE_TO_EMOJI
from llm import get_openai_emoji


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
