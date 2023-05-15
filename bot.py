from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient

from config import config
from slack_utils import text_to_reactions

app = App(
    token=config["SLACK_BOT_TOKEN"],
    signing_secret=config["SLACK_APP_SIGNING_SECRET"],
)


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


if __name__ == "__main__":
    handler = SocketModeHandler(app, config["SLACK_APP_TOKEN"])
    handler.start()
