from openai import OpenAI
from dotenv import load_dotenv
import os
import httpx


load_dotenv()

CITY_CODES = {
    "合肥市": "340100",
    "合肥": "340100",
    "HEFEI": "340100",
    "芜湖市": "340200",
    "芜湖": "340200",
    "WUHU": "340200"
}

tools_list = """
1. get_weather(city: str) - Returns the current weather for a given city.
2. search_file(folder: str, query: str) - Returns a summary from file for the given query.
"""

# System prompt with embedded tools list
system_prompt = f"""
You have the following tools available to you:
Available Tools: {tools_list}

If you decide to use a tool, respond ONLY with a valid JSON object:
{{ "tools":
  [
    {{ "name": "<tool_name>", "arguments": {{ ... }} }}
  ]
}}

If you do not use a tool, respond normally in plain text.
"""


def get_city_code(city_name):
    city_name = city_name.strip().upper()
    return CITY_CODES.get(city_name, "340100")



def get_weather(city_name):
    """Get weather of a city."""
    url = "https://restapi.amap.com/v3/weather/weatherInfo"
    params = {
        "city": get_city_code(city_name),
        "key": os.getenv("LBS_API_KEY")
    }
    response = httpx.get(url, params=params, verify=False)
    return response.json()["lives"][0]


