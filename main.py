import ollama

import requests

import base64

from homeassistant_api import Client
import wikipedia



# homeassistant api url
ASSIST_URL = 'http://homeassistant.local:8123/api'
# Uses Tool and Vision model in small size and on current Maschine.
model = 'ministral-3:3B'
llmHost = "127.0.0.1"

# Wikipedia language.
WIKI_LANG = "en"

# Needs to be set.
userName = ""
CAMERA_ENTITY_ID = ""





with open(".token") as f:
    TOKEN = f.read() 

def createPrompt(role, content):
    return {'role': role, 'content': content}

client = ollama.Client(
    llmHost
)

messages = [
    createPrompt("system", f"You are a helpfull Homeassistant with the Name Luna. The Name of the User is {userName}. Keep yourself short and concise.")
]

def get_camera_feed() -> str:
    """Get the current camera feed of the home.

    Returns:
        camera image
    """

    headers = {"Authorization": f"Bearer {TOKEN}"}
    r = requests.get(f"{ASSIST_URL}/camera_proxy/{CAMERA_ENTITY_ID}", headers=headers)

    return base64.b64encode(r.content).decode('utf-8')


def get_local_data() -> str:
    """Get home data from homeassistant.
    
    Args:
        city: The name of the city

    Returns:
        The current temperature for the city
    """

    client = Client(ASSIST_URL, TOKEN)

    data = ""

    states = client.get_states()
    
    for s in states:
        data+=s.entity_id+s.state+"\n"

    return data

def get_home_weather() -> str:
    """Get the home Weather from homeassistant.

    Returns:
        The current temperature for the city
    """

    client = Client(ASSIST_URL, TOKEN)

    data = ""

    weather = client.get_state(entity_id="weather.forecast_home")

    attrs = weather.attributes

    data+= "Condition: " + weather.state+"\n"

    for y, value in attrs.items():
        data+= f"{y}: " + str(value)+"\n"

    return data

def wikipedia_search(query: str):
    """Searches Wikipedia for the query and gives the first result back. Execute this on a question"""
    """
    Args:
        query: The search query
        b: The second number

    Returns:
        The product of the two numbers
    """
    # Set language (optional, default is English)!
    wikipedia.set_lang()

    # Search for pages related to a term
    results = wikipedia.search("Python programming")

    # Get a summary of the first search result
    summary = wikipedia.summary(results[0], sentences=3)

    return summary


tools = [get_camera_feed, get_local_data, get_home_weather,wikipedia_search]


while True:
    userInput = input("User: ")

    messages.append(createPrompt("user", userInput))

    response = client.chat(
        model,
        messages=messages,
        stream=False,
        tools=tools
        )

    if response.message.tool_calls:
        # only recommended for models which only return a single tool call
        call = response.message.tool_calls[0]

        result = None

        # tool call logic
        if call.function.name == "get_local_data":
            result = get_local_data(**call.function.arguments)
            messages.append({"role": "tool", "tool_name": call.function.name, "content": str(result)})
        elif call.function.name == "get_camera_feed":
            result = get_camera_feed(**call.function.arguments)
            messages.append({"role": "tool", "tool_name": call.function.name, "images": [result]})
        elif call.function.name == "get_home_weather":
            result = get_home_weather(**call.function.arguments)
            messages.append({"role": "tool", "tool_name": call.function.name, "content": str(result)})
        elif call.function.name == "wikipedia_search":
            result = wikipedia_search(**call.function.arguments)
            messages.append({"role": "tool", "tool_name": call.function.name, "content": str(result)})


        final_response = client.chat(model=model, messages=messages, tools=tools)
        messages.append(final_response.message)

        print("Luna: ", final_response.message.content)
    else:
        message = response['message']
        messages.append(response.message)

        print("Luna: ", message["content"])

    


