import vertexai
from vertexai.generative_models import GenerativeModel, Part
import base64
import os

# --- Re-initialize Vertex AI (or ensure it's still initialized from Step 1) ---
# If running as a single script, this will already be initialized.
# For clarity, assuming it's part of a larger workflow.
project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
location = os.getenv("GOOGLE_CLOUD_LOCATION") # e.g., "us-central1"

if not project_id or not location:
    print("Error: GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION environment variables must be set.")
    exit()

vertexai.init(project=project_id, location=location)

# --- Load the multimodal model (Gemini) ---
GEMINI_MODEL_NAME = "gemini-2.0-flash-001" # Or "gemini-1.5-pro-001" for higher quality
multimodal_model = GenerativeModel(GEMINI_MODEL_NAME)

# --- Path to the image generated in Step 1 ---
# This variable should hold the path from the previous step.
# For a single script, it would be 'generated_image_for_step2'.
#if 'generated_image_for_step2' not in locals() or generated_image_for_step2 is None:
 #   print("Error: No generated image found from Step 1. Please ensure Step 1 ran successfully.")
 #   exit()

image_to_analyze_path = "C:\InteriorGenie\generated_content_20250608_234846\Mid_Century_Modern_Study__Brow_view_3_234914.jpeg"

# --- Prepare the image for the multimodal prompt ---
try:
    with open(image_to_analyze_path, "rb") as image_file:
        image_bytes = image_file.read()
    encoded_image = base64.b64encode(image_bytes).decode("utf-8")
    mime_type = "image/jpeg" # Assuming JPEG, adjust if your image generation creates PNG etc.
    print(f"Image for color palette analysis: {image_to_analyze_path}")
except FileNotFoundError:
    print(f"Error: The image '{image_to_analyze_path}' was not found.")
    exit()

# --- Define your text prompt for the color palette ---
# IMPORTANT: Instruct the model to GENERATE an image.
text_prompt_for_palette = "Based on the provided interior design image, generate a new image that displays a clear and concise color palette. Show 5-7 dominant colors from the image, each as a distinct color swatch, with their hexadecimal or RGB values if possible. Arrange them neatly."

# --- Construct the multimodal content for Gemini ---
contents_for_palette = [
    Part.from_text(text_prompt_for_palette),
    Part.from_data(data=encoded_image, mime_type=mime_type)
]

# --- Send the request to Gemini to generate the color palette image ---
print("Generating color palette image based on the interior design image...")
try:
    palette_response = multimodal_model.generate_content(contents_for_palette)

    # Gemini's response will contain Parts, potentially including image parts
    # You need to iterate through parts to find the image.
    generated_palette_image_saved = False
    for part in palette_response.candidates[0].content.parts:
        if part.inline_data and "image" in part.inline_data.mime_type:
            # This part contains an image
            palette_image_bytes = base64.b64decode(part.inline_data.data)
            palette_image_path = "generated_color_palette.jpeg" # You might get PNG, check mime_type
            with open(palette_image_path, "wb") as f:
                f.write(palette_image_bytes)
            print(f"Generated color palette image saved to: {palette_image_path}")
            generated_palette_image_saved = True
            break # Assuming only one image is generated

    if not generated_palette_image_saved:
        print("No image part found in the Gemini response for the color palette.")
        # If no image was generated, perhaps Gemini provided text output instead.
        # You might want to print palette_response.text here to see what it did return.
        print("Gemini's text response (if any):")
        print(palette_response.text)


except Exception as e:
    print(f"An error occurred during color palette image generation: {e}")