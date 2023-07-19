import os
import sys

# Setting path
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(SCRIPT_DIR)

try:
    from apis.llm.gpt4free_llm import gpt4freeLLM
except ImportError:
    # Handle the case where the module cannot be imported
    CoquiTTS = None
    # Log an error or raise an exception, as appropriate


class TextGenerator:
    LLM_CLASSES = {
        'g4f': gpt4freeLLM,
    }

    def __init__(self, llm_provider):
        self.llm_provider = llm_provider
        self.llm = self._create_llm_instance()

    def _create_llm_instance(self):
        LLMClass = self.LLM_CLASSES.get(self.llm_provider)
        if LLMClass is None:
            raise ValueError(f'Unsupported LLM provider: {self.llm_provider}')
        return LLMClass()

    def set_llm_provider(self, llm_provider):
        self.llm_provider = llm_provider
        self.llm = self._create_llm_instance()

    def generate_chat_responses(self, query):
        return self.llm.generate_chat_responses(query)


# Usage:
# To use the TextGenerator class, create an instance:
llm1 = TextGenerator('g4f')
# Then, call the generate_chat_responses function with a query:
query = "Tell a joke"
responses = llm1.generate_chat_responses(query=query)
# Iterate over the responses and print the response and provider name

if responses is not None:
    for response, provider_name in responses:
        print("User:", query)
        print(f'{provider_name}:', response)
else:
    print('Error occurred while generating chat response')
