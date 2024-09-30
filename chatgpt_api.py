from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import json
import os

load_dotenv()

key = os.getenv("OPENAI_API_KEY")

openai = OpenAI(
    api_key=key,
)

class Round(BaseModel):
    message: str
    survivors: list[str]

bot_prompt = """
You are a computer game that selects who's plans are good enough to survive the scenario the players are put in.
Always and only one person survives. You have to decide who that person is.
From what the players say, you have to play out the scenario in text showing what would happen to the player and the outcome.
If a player uses a power or ability that is too unfair, make it work but with a twist that likely ends in their fate
Always disallow players from using godlike or invincible abilities.
Whenever a player states they do something, instead say that they try to, and then describe the outcome.
Please make sure to always have a clear outcome for each player and how they interact with eachother, restating what players said in their prompt.
The output should only be about 100 to 200 words long and build anticipation of who survives till the end. Always ensure that only one survives.
All and all, be creative and make us laugh!
"""

# ask the ai who survives
def get_fate(scenario, messages):
    input_messages = [
        {"role": "system", "content": bot_prompt},
        {"role": "system", "content": "Scenario: " + scenario},
    ]
    input_messages.extend(
        [
            {"role": "user", "content": messages}
        ]
    )


    completion = openai.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=input_messages,
        response_format=Round,
    )
    return json.loads(completion.choices[0].message.content)