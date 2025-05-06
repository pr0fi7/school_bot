import re
import Levenshtein

from config.settings import trigger_words_list

async def trigger_words(message, threshold=0.8):
    message = message.lower()

    for word in trigger_words_list:
        if re.search(rf"\b{word}\b", message, re.IGNORECASE):
            return {'status': True, 'word': word}

    for word in trigger_words_list:
        if Levenshtein.ratio(word.lower(), message) > threshold:
            return {'status': True, 'word': word}

    return {'status': False, 'word': None}