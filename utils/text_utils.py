import re


def strip_formatting(text):
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Remove **
    text = re.sub(r'<(.*?)>', r'\1', text)         # Remove <>
    return text