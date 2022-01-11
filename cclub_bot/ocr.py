import logging

import pytesseract
import re
from io import BytesIO

from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def resolve_stream(image: bytes) -> str:
    image = Image.open(BytesIO(image))
    image = image.convert('RGB')
    height, width = image.size
    raw = image.load()
    for loop1 in range(height):
        for loop2 in range(width):
            r, g, b = raw[loop1, loop2]
            if (r+g+b) > 254*3:
                raw[loop1, loop2] = 255, 255, 255
            else:
                raw[loop1, loop2] = 0, 0, 0
    text = pytesseract.image_to_string(image, config='digits')
    text = re.sub(r"[^0-9]", "", text)
    if not len(text) == 4:
        return ""
    print(f"Cracked captcha: {text}")
    return text
