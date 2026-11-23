"""voxtype post-process: lowercase sentence starts and the pronoun I, drop the final period.

Keeps acronyms like RAM; keeps a final ? ! or ellipsis.
"""

import re
import sys


def lower_start(match):
    word = match.group(3)
    if len(word) > 1 and word.isupper():
        return match.group(0)
    return match.group(1) + match.group(2) + word[0].lower() + word[1:]


text = sys.stdin.read().strip()
# Letters only: punctuation must stay free to end this sentence and start the next.
text = re.sub(r"(^|[.!?…]\s+)(\W*?)(\w+)", lower_start, text)
# I, I'm, I've… but not the I inside AI or IDE.
text = re.sub(r"\bI(?=$|[\s'’.,!?;:…])", "i", text)
if text.endswith(".") and not text.endswith(".."):
    text = text[:-1]
sys.stdout.write(text)
