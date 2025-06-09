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
    with open("C:\InteriorGenie\generated_content_20250608_234846\Mid_Century_Modern_Study__Brow_view_2_234914.jpeg", "rb") as image_file:
        image_bytes = image_file.read()
    encoded_image = base64.b64encode(image_bytes).decode("utf-8")
    mime_type = "image/jpeg" # Adjust based on your image type (e.g., "image/png")
    print(mime_type)
except FileNotFoundError:
    print("Error: image.jpg not found. Please provide a valid image path.")
    exit()

# --- Define your text prompt ---
#text_prompt = "Generate a interior design color palette image based on the provided image, provide hex colors and specify if they are primary or secondary colors in the image"
text_prompt = (

     ""     
     "Analyze the provided interior design image and evaluate the dominant colors "
    "Provide a list of 5-7 key colors in JSON format. "
    "For each color, include: "
    "1. 'name' (common color name, e.g., 'Warm Brown') "
    "2. 'hex' (hexadecimal color code, e.g., '#RRGGBB') "
    "3. 'type' ('primary' or 'secondary' based on prominence). "
    "The JSON should be an array of objects. Do NOT include any additional text or markdown outside the JSON block. "
    "Example JSON format: "
    "```json\n"
    "[\n"
    "  {\"name\": \"Warm Brown\", \"hex\": \"#876C55\", \"type\": \"primary\"},\n"
    "  {\"name\": \"Light Beige\", \"hex\": \"#E3DACC\", \"type\": \"secondary\"}\n"
    "]\n"
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