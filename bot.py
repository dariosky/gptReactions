from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from config import config
from reactions.slack_utils import react_to_messages
from weather.weather_commands import add_weather_commands

bot = App(
    token=config["SLACK_BOT_TOKEN"],
    signing_secret=config["SLACK_APP_SIGNING_SECRET"],
)

if __name__ == "__main__":
    handler = SocketModeHandler(bot, config["SLACK_APP_TOKEN"])
    add_weather_commands(bot)
    react_to_messages(bot)
    bot.client.users_setPresence(presence="auto")
    handler.start()
