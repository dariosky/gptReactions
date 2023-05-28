from .weather import text_to_weather


def add_weather_commands(bot):
    @bot.command("/meteo")
    def repeat_text(ack, respond, command):
        # Acknowledge command request
        request = command["text"].strip()
        ack()
        if not request:
            return respond(
                "Please give me a request - ex. `/meteo tomorrow in New York`"
            )
        respond(
            f"Hello @{command['user_name']}. Let me check the weather...\n"
            f"> {request}"
        )
        forecast = text_to_weather(request)
        respond(forecast)
