from openai import OpenAI
import os
import dotenv
import getpass


class OpenAIClient:
    def __init__(self, model: str = "gpt-4o-mini"):
        if dotenv.find_dotenv():
            dotenv.load_dotenv()
            api_key = os.environ["OPENAI_API_KEY"]
        else:
            api_key = getpass.getpass("Enter OpenAI API key: ")

        self.client = OpenAI(api_key=api_key)
        self.model = model
