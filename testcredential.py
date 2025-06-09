import os
import vertexai
from vertexai.generative_models import GenerativeModel
from vertexai.vision_models import ImageGenerationModel

# Add these lines to check the environment variables
print(f"GOOGLE_CLOUD_PROJECT: {os.getenv('GOOGLE_CLOUD_PROJECT')}")
print(f"GOOGLE_CLOUD_LOCATION: {os.getenv('GOOGLE_CLOUD_LOCATION')}")
print(f"GOOGLE_GENAI_USE_VERTEXAI: {os.getenv('GOOGLE_GENAI_USE_VERTEXAI')}")
print(f"GOOGLE_APPLICATION_CREDENTIALS: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")

# Your existing code
project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
location = os.getenv("GOOGLE_CLOUD_LOCATION")

vertexai.init(project=project_id, location=location)

model = GenerativeModel("gemini-2.0-flash-001")
response = model.generate_content("Tell me a data science joke.")
print(response.text)

generation_model = ImageGenerationModel.from_pretrained("imagegeneration@002")

response = generation_model.generate_images(
    prompt="cute blond and white chihuahua with green eyes"
)

print(response)
response.images[0].show()

# --- Save the generated image ---
# The 'response' object from generate_images contains a list of Image objects.
# We assume you want to save the first image (at index 0)
if response.images:
    output_filename = "chihuahua_image.jpg" # You can change the filename and extension (e.g., .png)
    response.images[0].save(location=output_filename)
    print(f"Image saved successfully to {output_filename} in the current directory.")
else:
    print("No image was generated or found in the response.")
