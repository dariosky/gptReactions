import datetime
import logging
import os
from pprint import pprint

import requests
from cachier import cachier

from llm import cache_folder, issue_command
from .weather_codes import WMO_CODES, WEATHER_CODES

logger = logging.getLogger(__name__)

ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


@cachier(cache_dir=cache_folder)
def get_weather_information_tomorrow_io(start_time, end_time, latitude, longitude):
    endpoint = "https://api.tomorrow.io/v4/timelines"
    logger.info(
        f"Getting the weather for {start_time}-{end_time} in {latitude},{longitude}"
    )
    fields = ["temperature", "weatherCode", "precipitationIntensity"]
    data = {
        "location": ",".join(map(str, [latitude, longitude])),
        "units": "metric",
        "timesteps": ["1h"],
        "fields": fields,
        "startTime": start_time,
        "endTime": end_time,
    }
    response = requests.get(
        endpoint,
        params={"apikey": os.environ.get("TOMORROW_API_KEY"), **data},
        headers={"accept": "application/json"},
    )
    response.raise_for_status()
    return response.json()


@cachier(cache_dir=cache_folder)
def get_weather_information_openweather(start_time, end_time, latitude, longitude):
    endpoint = "https://api.openweathermap.org/data/3.0/onecall"
    logger.info(
        f"Getting the weather for {start_time}-{end_time} in {latitude},{longitude}"
    )
    data = {
        "lat": latitude,
        "lon": longitude,
        "units": "metric",
    }
    response = requests.get(
        endpoint,
        params={"appid": os.environ["OPENWEATHER_API_KEY"], **data},
        headers={"accept": "application/json"},
    )
    if response.status_code != 200:
        raise (
            RuntimeError(
                f"Error getting weather info: {response.status_code} - {response.text}"
            )
        )
    return response.json()


@cachier(cache_dir=cache_folder, stale_after=datetime.timedelta(hours=1))
def get_weather_information_open_meteo(start_time, end_time, latitude, longitude):
    endpoint = "https://api.open-meteo.com/v1/forecast"
    logger.info(
        f"Getting the weather for {start_time}-{end_time} in {latitude},{longitude}"
    )
    response = requests.get(
        endpoint,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "temperature_2m,precipitation,weathercode",
            "units": "metric",
            "start_date": start_time[:10],
            "end_date": end_time[:10],
        },
        headers={"accept": "application/json"},
    )
    if response.status_code != 200:
        raise (
            RuntimeError(
                f"Error getting weather info: {response.status_code} - {response.text}"
            )
        )
    data = response.json()
    timeline = data["hourly"]
    precipitation_units = data["hourly_units"]["precipitation"]
    response = [
        {
            "ts": ts + ":00Z",
            "weatherCode": weather_code,
            "temperature": temperature,
            "precipitation": precipitation,
            "weather": WMO_CODES[weather_code],
        }
        for ts, temperature, precipitation, weather_code in zip(
            timeline["time"],
            timeline["temperature_2m"],
            timeline["precipitation"],
            timeline["weathercode"],
        )
        if start_time <= ts <= end_time
    ]
    return response


def simplify_data_tomorrow_io(weather_timeline):
    """From the weather.io hourly timeline to a shorter notation"""
    intervals = []
    timepoints = weather_timeline["data"]["timelines"][0]["intervals"]
    r = {}
    dateformat = "%Y-%m-%dT%H:%M:%SZ"
    for point in timepoints:
        last_weather_code = r.get("weatherCode")
        w = point["values"]
        if last_weather_code is not None and w["weatherCode"] != last_weather_code:
            intervals.append(r)
            r = {}
        dt = datetime.datetime.strptime(point["startTime"], dateformat)
        if r.get("ts") is None:
            r["startTime"] = dt.strftime(dateformat)
        r["endTime"] = (dt + datetime.timedelta(hours=1)).strftime(dateformat)
        r["weatherCode"] = w["weatherCode"]
        r["weather"] = w["weather"]
        r["precipitation"] = max(r.get("precipitation", 0), w["precipitationIntensity"])

        current_temperature = int(w["temperature"])
        max_temperature = r.get("maxTemperature")
        min_temperature = r.get("minTemperature")
        if max_temperature is None or current_temperature > max_temperature:
            r["maxTemperature"] = current_temperature
        if min_temperature is None or current_temperature < min_temperature:
            r["minTemperature"] = current_temperature

    intervals.append(r)
    for r in intervals:
        r["weather"] = WEATHER_CODES[r.pop("weatherCode")]
    return intervals


def simplify_data_open_meteo(weather_timeline):
    """From the openmeteo hourly timeline to a shorter notation"""
    intervals = []
    r = {}

    for w in weather_timeline:
        last_weather_code = r.get("weatherCode")
        if last_weather_code is not None and w["weatherCode"] != last_weather_code:
            intervals.append(r)
            r = {}
        dt = datetime.datetime.strptime(w["ts"], ISO_FORMAT)
        if r.get("startTime") is None:
            r["startTime"] = dt.strftime(ISO_FORMAT)
        r["endTime"] = (dt + datetime.timedelta(hours=1)).strftime(ISO_FORMAT)
        r["weatherCode"] = w["weatherCode"]
        r["precipitation"] = max(r.get("precipitation", 0), w["precipitation"])

        current_temperature = int(w["temperature"])
        max_temperature = r.get("maxTemperature")
        min_temperature = r.get("minTemperature")
        if max_temperature is None or current_temperature > max_temperature:
            r["maxTemperature"] = current_temperature
        if min_temperature is None or current_temperature < min_temperature:
            r["minTemperature"] = current_temperature

    intervals.append(r)
    for r in intervals:
        r["weather"] = WMO_CODES[r.pop("weatherCode")]
    return intervals


def summarize_weather(summarized_weather_timeline):
    prompt = f"""
        Summarize the following weather conditions with maximum 50 words and using emojis like ☀️☔️🥵:
        
        {summarized_weather_timeline}
    """
    return issue_command(prompt)


def text_to_weather_request(text):
    now = datetime.datetime.utcnow()
    now = now.replace(minute=0)  # 1h cache
    now_formatted = now.strftime("%d %B, %Y - %H:%M UTC")
    prompt = f"""
        Now is {now_formatted}
        Given the following text with a request for weather information - return me a json with:
        startTime: initial timestamp of the date the user is interested into or null if not specified
        endTime: end timestamp of the date the user is interested into or null if not specified
        location: the geographic latitude and longitude of the place the user is interested into
        
        Format the timestamps as ISO 8601 format
        
        {text}
    """
    response = issue_command(prompt, temperature=0, return_json=True)
    if not response.get("endTime"):
        start_time = datetime.datetime.strptime(response["startTime"], ISO_FORMAT)
        response["endTime"] = (start_time + datetime.timedelta(hours=24)).strftime(
            ISO_FORMAT
        )
    return response


def text_to_weather(text):
    weather_request = text_to_weather_request(text)
    latitude = weather_request["location"]["latitude"]
    longitude = weather_request["location"]["latitude"]
    weather_timeline = get_weather_information_open_meteo(
        weather_request["startTime"],
        weather_request["endTime"],
        latitude,
        longitude,
    )
    simplified_timeline = simplify_data_open_meteo(weather_timeline)
    return summarize_weather(simplified_timeline)


def example():
    data = {
        "startTime": "2023-05-21T00:00:00",
        "endTime": "2023-05-21T23:59:59",
        "location": {"latitude": 36.510071, "longitude": -4.882447},
    }
    latitude = data["location"]["latitude"]
    longitude = data["location"]["latitude"]
    weather_timeline = get_weather_information_open_meteo(
        data["startTime"], data["endTime"], latitude, longitude
    )

    pprint(simplify_data_open_meteo(weather_timeline))
