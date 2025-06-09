import vertexai
from vertexai.generative_models import GenerativeModel, Part
import base64
import os
import json
import re

def get_image_colors(image_path):
    """
    Analyze an image and return its color palette in JSON format.
    
    Args:
        image_path (str): Path to the image file to analyze
        
    Returns:
        str: JSON string containing the color palette information
    """
    MODEL_NAME = "gemini-2.0-flash-001"
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION")

    # Initialize Vertex AI
    vertexai.init(project=project_id, location=location)
    
    # Load the model
    model = GenerativeModel(MODEL_NAME)

    try:
        # Read and encode the image
        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        mime_type = "image/jpeg"  # Adjust based on your image type if needed

        # Define the text prompt for color analysis
        text_prompt = (
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

        # Construct the multimodal content
        contents = [
            Part.from_text(text_prompt),
            Part.from_data(data=encoded_image, mime_type=mime_type)
        ]

        # Generate content using the model
        response = model.generate_content(contents)
        
        # Extract the response text
        raw_text_response = ""
        for part in response.candidates[0].content.parts:
            if part.text:
                raw_text_response += part.text

        # Extract JSON from the response
        json_match = re.search(r"```json\s*(\{.*\}|\[.*\])\s*```", raw_text_response, re.DOTALL)
        
        if json_match:
            return json_match.group(1)
        else:
            return None

    except FileNotFoundError:
        raise FileNotFoundError(f"Error: Image not found at {image_path}")
    except Exception as e:
        raise Exception(f"An error occurred while analyzing the image: {str(e)}")

if __name__ == "__main__":
    # Example usage
    try:
        image_path = "path/to/your/image.jpg"  # Replace with actual image path
        color_palette = get_image_colors(image_path)
        if color_palette:
            print("Color Palette:")
            print(color_palette)
        else:
            print("No color palette could be extracted from the image.")
    except Exception as e:
        print(f"Error: {str(e)}") 