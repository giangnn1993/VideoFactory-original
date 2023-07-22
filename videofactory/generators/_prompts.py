# flake8: noqa

import json

# Prompts for image generation
# ------------------------------------

conversation_image_1 = {
    "subject": "An old monk",
    "prompt": {
        "media": "masterpiece, top quality, best quality, official art, beautiful and aesthetic:1.2, extremely detailed, high quality, highres, 16K, RAW, ultra highres, ultra detailed, finely detailed, an extremely delicate and beautiful, extremely detailed real shadow",
        "subject": "(an old monk:1.3)",
        "describe": "headshot, ((bald)), afghan, beard, wearing a brown outfit and a brown robe, (skin color: alabaster)",
        "art": "realistic face, a photorealistic painting, photorealism"
    }
}
conversation_image_2 = {
    "subject": "A human male merchant",
    "prompt": {
        "media": "((sketch)), brightly colored",
        "subject": "1_guy, (a human male merchant)",
        "describe": "headshot, mischievous smirk, wealthy, looking at viewer",
        "art": "fantasy portrait, roman empire aesthetic, old paper texture"
    }
}

# create an example template
examples_image = [
    {
        "query": "An old monk",
        "answer": json.dumps(conversation_image_1, indent=0).replace("{", "{{").replace("}", "}}")
    }, {
        "query": "A human male merchant",
        "answer": json.dumps(conversation_image_2, indent=0).replace("{", "{{").replace("}", "}}")
    }
]

# the prefix is our instructions
prefix_image = """
The following are excerpts from conversations with an AI assistant who acts as a prompt generator for Midjourney's artificial intelligence program (generative model).
The user provides a subject enclosed in square brackets having a conversation and shares some of their spoken lines, the assistant then analyzes the input 
and generates detailed and imaginative descriptions that will inspire the generative model to create unique and captivating images.
Keep in mind that the AI is capable of understanding a wide range of languages and can
interpret abstract concepts, so feel free to be as imaginative and descriptive as possible.
The more detailed and imaginative your description, the more interesting the resulting image will be.
Do not include any explanations, only provide a RFC8259 compliant JSON response following this format without deviation,
never mention being a Language Model AI or similar:
- "media" refers to the medium or format in which the artwork is presented.
- "subject" refers to the main focus or central figure depicted in the artwork.
- "describe" refers to the detailed descriptions of the subject, especially outer appearances such as (but not limited to) skin color, ethnicity, clothing, hairstyle, accessories.
- "art" encompasses the artistic style, technique, or genre of the artwork, including elements such as backgrounds, lighting, shadows, environments, and visuals.
Important: Ensure that the values for each category consist of keywords, not prose.

Footnote: If you want a certain keyword to be more important for the generative model, you can attempt to increase its weight, you do it
by simply writing your desired weight value after your prompt keyword in parentheses like this (keyword:1.40).
Another, simpler way to do this is to simply add parentheses to the keyword. The more parentheses you add, the more important
the keyword will be in the generation process. This is done like this: *((((outdoor scene))))*.
A keyword with one set of parentheses will have a weight of 1.1. Keyword with double parentheses – 1.1 * 1.1, and so on.
Use both methods to emphasize keywords if necessary.

Here are some examples:
"""


# Prompts for quote generation.
# ------------------------------------

conversation_quote = {
    "topic": "Positivity",
    "quotes": [
        {
            "quote": "Be strong now because things will get better. It might be stormy now, but it can't rain forever.",
            "short": "Be strong now because things will get better"
        },
        {
            "quote": "WHEN PEOPLE LAUGH AT YOU Do not react. Do not feel down. Wake up the lion inside you. Work hard in silence. Let your SUCCESS make the noise.",
            "short": "WHEN PEOPLE LAUGH AT YOU Do not react"
        },
        {
            "quote": "Train your mind to see the good in everything. Positivity is a choice. The happiness of your life depends on the quality of your thoughts.",
            "short": "See the good in everything"
        },
        {
            "quote": "Never regret anything that has happened in your life, it cannot be changed, undone or forgotten so take it as a lesson learned and move on.",
            "short": "Never regret anything that has happened"
        },
        {
            "quote": "IN 2 YEARS YOU REALLY CAN BE SOMEWHERE YOU NEVER IMAGINED, THAT'S WHY IT'S SO IMPORTANT TO KEEP GOING.",
            "short": "KEEP GOING"
        },
        {
            "quote": "No, your haters don't hate you. They hate the fact that even after all of their effort and energy, you are still growing, still thriving, and still loved.",
            "short": "No, your haters don't hate you"
        },
        {
            "quote": "Nothing is miserable unless you think it so; and on the other hand, nothing brings happiness unless you are content with it.",
            "short": "Nothing is miserable unless you think it so"
        }
    ]
}

# create an example template
examples_quote = [
    {
        "query": "Friendship",
        "answer": json.dumps(conversation_quote, indent=0).replace("{", "{{").replace("}", "}}")
    }
]

prefix_quote = """
The following are excerpts from conversations with an AI assistant. Provide 10 meaningful sayings related to a 
user-provided topic with each saying having rougly 100 characters in length. Include shortened forms of the 
sayings that are about half in length. The insights should guide day-to-day decisions with valuable lessons.
Optionally, suggest practical methods for putting them into action or explore related themes.
Do not include any explanations, only provide a RFC8259 compliant JSON response following this 
format without deviation, never mention being a Language Model AI or similar.

Here is an example:
"""

# wise advices, inspiring quotes, and 