import os
import sys
from typing import List
import g4f

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

try:
    from llm import LargeLanguageModel
except ImportError:
    # Handle the case where the module cannot be imported
    LargeLanguageModel = None
    # Log an error or raise an exception, as appropriate


class gpt4freeLLM(LargeLanguageModel):
    def __init__(self) -> None:
        super().__init__('gpt4free')

    def generate_chat_response(self, provider, stream: bool, content: str) -> str:
        # print(g4f.Provider.DeepAi.params) # supported args
        try:
            response = g4f.ChatCompletion.create(
                model='gpt-3.5-turbo',
                provider=provider,
                stream=stream,
                messages=[{"role": "user", "content": content}],
            )
            return response
        except Exception as e:
            print(f"Unknown error occurred for provider {provider}: {e}")
            return ""

    def generate_chat_responses(self, query: str) -> List:
        providers = {
            "DeepAi": {
                "provider": g4f.Provider.DeepAi,
                "stream": True
            },
            "GetGpt": {
                "provider": g4f.Provider.GetGpt,
                "stream": True
            },
            "Aichat": {
                "provider": g4f.Provider.Aichat,
                "stream": False
            },
            "AItianhu": {
                "provider": g4f.Provider.AItianhu,
                "stream": False
            }
        }

        responses = []  # Store the responses
        for provider_name, data in providers.items():
            provider = data["provider"]
            # We don't need to use stream here, default is set to False for non-streaming responses
            stream = False  # stream = data["stream"]

            response = self.generate_chat_response(provider=provider, stream=stream, content=query)

            if stream is True:
                for message in response:
                    # Append the response and provider name to the list
                    responses.append((message, provider_name))
            else:
                # Append the response and provider name to the list
                responses.append((response, provider_name))

        return responses


# # Usage:
# # To use the gpt4freeLLM class, create an instance:
# llm = gpt4freeLLM()
# # Then, call the generate_chat_responses function with a query:
# query = "Tell a joke"
# responses = llm.generate_chat_responses(query=query)

# # Iterate over the responses and print the response and provider name
# for response, provider_name in responses:
#     print("User:", query)
#     print(f'{provider_name}:', response)
