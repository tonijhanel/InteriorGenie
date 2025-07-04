import vertexai
from vertexai.generative_models import GenerativeModel, Part
import base64
import os
import json
import re

MODEL_NAME = "gemini-2.0-flash-001"
project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
location = os.getenv("GOOGLE_CLOUD_LOCATION")

# --- Initialize Vertex AI ---
vertexai.init(project=project_id, location=location)

# --- Load the model ---
model = GenerativeModel(MODEL_NAME)

try:
    with open("C:\InteriorGenie\colorpalette.png", "rb") as image_file:
        image_bytes = image_file.read()
    encoded_image = base64.b64encode(image_bytes).decode("utf-8")
    mime_type = "image/png" # Adjust based on your image type (e.g., "image/png")
    print(mime_type)
except FileNotFoundError:
    print("Error: image.png not found. Please provide a valid image path.")
    exit()

# --- Define your text prompt ---
#text_prompt = "Generate a interior design color palette image based on the provided image, provide hex colors and specify if they are primary or secondary colors in the image"
text_prompt = (
"""
     Generate an interior design color palette image based on the following json and provided image
     [
          {"name": "Medium Brown", "hex": "#A0785A", "prevalence": "primary"},
          {"name": "Warm Beige", "hex": "#E6D9C3", "prevalence": "secondary"},
          {"name": "Dark Brown", "hex": "#4A3A2E", "prevalence": "secondary"},
          {"name": "Light Brown", "hex": "#C9B191", "prevalence": "secondary"},
          {"name": "Dark Gray", "hex": "#3C3B3A", "prevalence": "secondary"},
          {"name": "Tan", "hex": "#D6C2A8", "prevalence": "secondary"}
    ]
     """
)
# --- Construct the multimodal content ---
# The 'contents' parameter expects a list of 'Part' objects.
# Each 'Part' can be text, inline data (like base64 encoded image), or file data (GCS URI).
contents = [
    Part.from_text(text_prompt),
    Part.from_data(data=encoded_image, mime_type=mime_type)
]
# --- Send the request ---
try:
    response = model.generate_content(contents)
    raw_text_response = ""
    for part in response.candidates[0].content.parts:
        if part.text:
            raw_text_response += part.text

    #print("\n--- Raw Text Response from Gemini ---")
    #print(raw_text_response)
    #print("Generated content:")
    #print(response.text)
    json_match = re.search(r"```json\s*(\{.*\}|\[.*\])\s*```", raw_text_response, re.DOTALL)
    #print("formatted json")
    #print(json_match)
    if json_match:
        json_string = json_match.group(1)
        print("\n--- Found JSON Block ---")
        print(json_string)

    else:
        print("\n--- No JSON block found in the response. ---")
        print("Gemini might not have followed the JSON format request.")
    #print(response.candidates[0].content.parts)

except Exception as e:
    print(f"An error occurred: {e}")