def process_text(text):
    # Create a config object
    config = {}

    # Extracting the text enclosed in square brackets
    start_index = text.find("[") + 1
    end_index = text.find("]")
    bracket_text = text[start_index:end_index]

    # Splitting the bracket text by "|"
    items = bracket_text.split("|")

    first_item = items[0].strip()

    # Setting the rest of the items as environmental variables
    for item in items[1:]:
        key, value = item.split("=")
        config[key.strip()] = value.strip()

    outside_text = (text[:start_index-1] + text[end_index+1:]).strip()

    return first_item, outside_text, config
