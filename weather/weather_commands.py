from .weather import text_to_weather


def add_weather_commands(bot):
    @bot.command("/meteo")
    def repeat_text(ack, respond, command):
        # Acknowledge command request
        request = command["text"]
        ack()
        respond(
            f"Hi @{command['user_id']}. Let me check the weather...\n" f"> {request}"
        )
        forecast = text_to_weather(request)
        respond(forecast)
