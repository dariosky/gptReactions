import datetime

from weather.weather import text_to_weather, text_to_weather_request, ISO_FORMAT


class TestMeteo:
    text = '"Weather in Estepona this afternoon from 6pm onward"'

    def test_get_time_and_location(self):
        weather_request = text_to_weather_request(self.text)
        assert weather_request["location"] == {
            "latitude": 36.4256,
            "longitude": -5.1477,
        }
        start_time = datetime.datetime.strptime(
            weather_request["startTime"], ISO_FORMAT
        )
        assert start_time.hour == 18 and start_time.minute == 0
        assert weather_request["endTime"] is not None

    def test_full(self):
        response = text_to_weather(self.text)
