import re
import Levenshtein

from config.settings import trigger_words_list

async def trigger_words(message, threshold=0.8):
    """
    Check if the message contains any trigger words or closely related words
    and respond accordingly using Levenshtein distance for fuzzy matching.
    """

    # Normalize the message (convert to lowercase)
    message = message.lower()

    # Check if the message contains any exact trigger words
    for word in trigger_words_list:
        if re.search(rf"\b{word}\b", message, re.IGNORECASE):
            return {'status': True, 'word': word}

    # If no exact match, check for fuzzy matches using Levenshtein distance
    for word in trigger_words_list:
        # Compare the trigger word with the message using Levenshtein distance
        if Levenshtein.ratio(word.lower(), message) > threshold:
            return {'status': True, 'word': word}

    # No match found
    return {'status': False, 'word': None}