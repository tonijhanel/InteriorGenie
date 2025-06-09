import os
import asyncio
import base64
import re
import json
import shutil
from datetime import datetime
from typing import Optional, List, Dict, Any
from functools import lru_cache
import logging
from markdown import markdown
import io
import zipfile
import streamlit as st

import google.generativeai as genai
import vertexai
from vertexai.generative_models import GenerativeModel
from vertexai.preview.vision_models import ImageGenerationModel


from google.cloud import aiplatform
from google.cloud.aiplatform.gapic.schema import predict
from google.protobuf import json_format
import google.protobuf.struct_pb2


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Your existing code
project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
location = os.getenv("GOOGLE_CLOUD_LOCATION")

vertexai.init(project=project_id, location=location)

# Initialize API keys and configurations
#genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


# Test mode configuration
TEST_MODE = os.getenv("TEST_MODE", "False").lower() == "true"
TEST_RESPONSES_DIR = "test_responses"

# Define the prompt template for text generation
TEXT_GENERATION_PROMPT_TEMPLATE = """
Create a detailed interior design concept for a {user_room_type} in {user_design_style} style with a {user_color_scheme} color scheme.

Key design elements to incorporate: {user_key_design_elements}

Inspirational photo details: {user_inspirational_photo_details}

Please provide a comprehensive design plan including:
1. Overall Concept and Style
2. Color Scheme and Materials
3. Furniture Recommendations
4. Decorative Elements

Format the response in markdown with clear section headers (##) for each major component.
"""

def ensure_test_responses_dir():
    """Ensure the test responses directory exists."""
    os.makedirs(TEST_RESPONSES_DIR, exist_ok=True)

def get_test_response_key(room_type: str, design_style: str, color_palette: str) -> str:
    """Generate a unique key for test responses based on input parameters."""
    if TEST_MODE:
        return "test_response"  # Always return the same key in test mode
    return f"{room_type}_{design_style}_{color_palette}".lower().replace(" ", "_")

def save_test_response(key: str, response: str):
    """Save a test response to a file."""
    ensure_test_responses_dir()
    file_path = os.path.join(TEST_RESPONSES_DIR, f"{key}.json")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump({'response': response}, f)

def load_test_response(key: str) -> Optional[str]:
    """Load a test response from a file."""
    if TEST_MODE and not os.path.exists(os.path.join(TEST_RESPONSES_DIR, f"{key}.json")):
        # If in test mode and no test response exists, create a default one
        default_response = """
        ## Overall Concept and Style
        This is a test response for the interior design generator. It demonstrates the structure and formatting of the output.
        
        ## Color Scheme and Materials
        - Primary colors: Test colors
        - Materials: Test materials
        
        ## Furniture and Layout
        - Test furniture arrangement
        - Test layout details
        
               
        ## Decorative Elements
        - Test decorative items
        - Test styling elements
        
        """
        save_test_response(key, default_response)
        return default_response

    file_path = os.path.join(TEST_RESPONSES_DIR, f"{key}.json")
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('response')
    return None

# Cache for model instances
@lru_cache(maxsize=2)
def get_text_model():
    vertexai.init(project=project_id, location=location)
    model = GenerativeModel("gemini-2.0-flash-001")
    # return genai.GenerativeModel(model_name='gemini-1.5-flash')
    return model


@lru_cache(maxsize=1)
def get_image_model():
    vertexai.init(project=project_id, location=location)
    return ImageGenerationModel.from_pretrained("imagegeneration@006")

def setup_output_directory() -> str:
    """Create a timestamped output directory and return its path."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"generated_content_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def save_to_html(content: str, output_dir: str) -> str:
    """Save markdown content as HTML file."""
    # First, convert the content to HTML
    html_content = markdown(content, extensions=['extra', 'codehilite'], output_format='html5')
    
    # Remove any ">" characters that might have been added to captions
    html_content = html_content.replace('&gt;', '')
    
    # Create the full HTML document
    full_html = f"""<!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Generated Interior Design Content</title>
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                line-height: 1.6; 
                max-width: 1200px; 
                margin: 0 auto; 
                padding: 20px;
                color: #333;
            }}
            h1, h2 {{ 
                color: #2c3e50;
                margin-top: 1.5em;
                margin-bottom: 0.5em;
            }}
            .section {{
                margin-bottom: 40px;
                padding: 20px;
                background: #fff;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            .section-image {{
                margin-bottom: 20px;
                text-align: center;
            }}
            .section-image img {{ 
                max-width: 100%;
                height: auto;
                max-height: 500px;
                object-fit: cover;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .image-caption {{
                margin-top: 8px;
                font-size: 1.1em;
                color: #666;
                font-style: italic;
            }}
            p {{
                margin-bottom: 1em;
            }}
            @media (max-width: 768px) {{
                .section-image img {{
                    max-height: 300px;
                }}
            }}
        </style>
    </head>
    <body>
    {html_content}
    </body>
    </html>"""
    
    html_path = os.path.join(output_dir, "generated.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(full_html)
    return html_path

def save_image_from_base64(base64_image_bytes: str, image_alt: str, section_title: str, output_dir: str) -> str:
    """Saves a base64 encoded image to a file in the output directory."""
    try:
        image_data = base64.b64decode(base64_image_bytes)
        # Create a shorter, unique filename
        timestamp = datetime.now().strftime("%H%M%S")
        safe_section_title = "".join(c if c.isalnum() else "_" for c in section_title)[:30]
        safe_image_alt = "".join(c if c.isalnum() else "_" for c in image_alt[:10])
        image_filename = f"{safe_section_title}_{safe_image_alt}_{timestamp}.jpeg"
        image_path = os.path.join(output_dir, image_filename)

        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Save the image
        with open(image_path, "wb") as f:
            f.write(image_data)
        
        logger.info(f"Saved image as {image_filename}")
        return image_path
    except Exception as e:
        logger.error(f"Could not save image '{image_alt}': {e}")
        return ""

def parse_sections(full_markdown_text: str) -> List[str]:
    """Efficiently parse markdown sections."""
    parts = full_markdown_text.split("\n## ")
    sections = []
    
    if not parts:
        return sections
        
    # Handle first section (introduction)
    if not full_markdown_text.lstrip().startswith("## ") and parts[0].strip():
        sections.append(parts[0].strip())
        parts = parts[1:]
    
    # Handle remaining sections
    for part in parts:
        if part.strip():
            # Remove any leading ## if present and clean up the section
            clean_part = part.strip()
            if clean_part.startswith("##"):
                clean_part = clean_part[2:].strip()
            sections.append(clean_part)  # Don't add ## prefix here
    
    return sections

def extract_section_title(section_content: str) -> str:
    """Extract section title from markdown content."""
    # First try to match ## prefix
    match = re.match(r"##\s*(.*?)\n", section_content, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # If no ## prefix, try to get the first line
    first_line = section_content.split('\n')[0].strip()
    if first_line:
        return first_line
    
    return "Untitled Section"

async def generate_section_image(section_content: str, section_title: str, room_type: str, design_style: str, color_palette: str, output_dir: str) -> List[str]:
    """Generate image for a section using cached model."""
    if TEST_MODE:
        # In test mode, use existing images from test_responses folder
        test_images = [f for f in os.listdir(TEST_RESPONSES_DIR) if f.endswith(('.jpg', '.jpeg', '.png'))]
        if test_images:
            # Use the first available test image
            test_image_path = os.path.join(TEST_RESPONSES_DIR, test_images[0])
            # Copy the test image to the output directory with section-specific name
            output_image_path = os.path.join(output_dir, f"{section_title}.jpeg")
            shutil.copy2(test_image_path, output_image_path)
            return [output_image_path]
        return []
    
    # Normal mode - generate image using the model
    image_prompt_text_body = re.sub(r"##+\s*.*?\n", '', section_content, count=1).strip()[:300]
    image_prompt = (
        f"High-quality interior design photograph. Room type: {room_type}. "
        f"Design style: {design_style}. Color palette: {color_palette}. "
        f"The image should visually represent: '{section_title} - {image_prompt_text_body}'"
    )
    
    try:
        img_model = get_image_model()
        logger.info(f"Generating images for section: {section_title}")
        response = await asyncio.to_thread(
            img_model.generate_images,
            prompt=image_prompt,
            number_of_images=4,
            language="en",
            aspect_ratio="1:1",
            safety_filter_level="block_some",
            person_generation="allow_adult"
        )
        
        if response and response.images:
            # Save all generated images
            image_paths = []
            for i, image in enumerate(response.images):
                logger.info(f"Processing image {i+1} for section: {section_title}")
                generated_image_bytes_base64 = base64.b64encode(image._image_bytes).decode('utf-8')
                image_path = save_image_from_base64(
                    generated_image_bytes_base64,
                    f"view_{i+1}",
                    section_title,
                    output_dir
                )
                if image_path:
                    image_paths.append(image_path)
                    logger.info(f"Saved image {i+1} to: {image_path}")
            
            if image_paths:
                logger.info(f"Successfully generated {len(image_paths)} images for section: {section_title}")
                return image_paths
            else:
                logger.warning(f"No images were saved for section: {section_title}")
        else:
            logger.warning(f"No images were generated for section: {section_title}")
    except Exception as e:
        logger.error(f"Failed to generate image for section '{section_title}': {e}", exc_info=True)
    
    return []

async def process_single_section(section_md_content: str, room_type: str, design_style: str, color_palette: str, output_dir: str) -> str:
    """Process a single section including text and image generation."""
    section_title = extract_section_title(section_md_content)
    logger.info(f"Processing section: {section_title}")
    logger.info(f"Raw section content: {section_md_content[:100]}...")  # Log first 100 chars of content
    
    # Generate images for the section
    try:
        image_paths = await generate_section_image(section_md_content, section_title, room_type, design_style, color_palette, output_dir)
        logger.info(f"Received {len(image_paths)} images for section: {section_title}")
        
        if image_paths:
            # Split the section content at the first newline to insert image after title
            section_lines = section_md_content.split('\n', 1)
            if len(section_lines) > 1:
                # Create HTML for the section
                section_with_image = f"""## {section_title}

{section_lines[1]}"""

                # Add first image only to main title section
                #if "overall concept" in section_title.lower() and len(image_paths) > 0:
                first_image_path = image_paths[0]
                first_image_filename = os.path.basename(first_image_path)
                logger.info(f"Adding first image to main title section: {first_image_filename}")
                section_with_image = f"""## {section_title}

<div class="section-image">
    <img src="{first_image_filename}" alt="{section_title}">
    <div class="image-caption">{section_title}</div>
</div>

{section_lines[1]}"""

                # Add second image only to Color Scheme section
                #if "color scheme" in section_title.lower() and len(image_paths) > 1:
                second_image_path = image_paths[1]
                second_image_filename = os.path.basename(second_image_path)
                logger.info(f"Adding second image to Color Scheme section: {second_image_filename}")
                section_with_image += f"""

<div class="section-image">
    <img src="{second_image_filename}" alt="{section_title} - View 2">
    <div class="image-caption">{section_title} - View 2</div>
</div>"""

                # Add third image only to Furniture section
                if "furniture" in section_title.lower() and len(image_paths) > 2:
                    third_image_path = image_paths[2]
                    third_image_filename = os.path.basename(third_image_path)
                    logger.info(f"Adding third image to Furniture section: {third_image_filename}")
                    section_with_image += f"""

<div class="section-image">
    <img src="{third_image_filename}" alt="{section_title} - View 3">
    <div class="image-caption">{section_title} - View 3</div>
</div>"""

                # Add fourth image only to Lighting section
                if "lighting" in section_title.lower() and len(image_paths) > 3:
                    fourth_image_path = image_paths[3]
                    fourth_image_filename = os.path.basename(fourth_image_path)
                    logger.info(f"Adding fourth image to Lighting section: {fourth_image_filename}")
                    section_with_image += f"""

<div class="section-image">
    <img src="{fourth_image_filename}" alt="{section_title} - View 4">
    <div class="image-caption">{section_title} - View 4</div>
</div>"""
            else:
                # If no newline in content, just add the section title
                section_with_image = f"""## {section_title}"""
            
            return section_with_image
    except Exception as e:
        logger.error(f"Error processing section '{section_title}': {e}", exc_info=True)
    
    return section_md_content

async def generate_content(room_type: str, design_style: str, color_palette: str, key_elements: str, inspirational_photo_details: str):
    """Generate interior design content and display it in Streamlit."""
    output_dir = setup_output_directory()
    logger.info(f"Created output directory: {output_dir}")

    text_prompt = TEXT_GENERATION_PROMPT_TEMPLATE.format(
        user_room_type=room_type,
        user_design_style=design_style,
        user_color_scheme=color_palette,
        user_key_design_elements=key_elements,
        user_inspirational_photo_details=inspirational_photo_details
    )

    try:
        full_markdown_text = None
        
        if TEST_MODE:
            # Try to load from test responses
            test_key = get_test_response_key(room_type, design_style, color_palette)
            full_markdown_text = load_test_response(test_key)
            
            if not full_markdown_text:
                # If no test response exists, generate one and save it
                text_model = get_text_model()
                response = await text_model.generate_content_async(text_prompt)
                full_markdown_text = response.text
                save_test_response(test_key, full_markdown_text)
                logger.info(f"Saved new test response for key: {test_key}")
        else:
            # Normal mode - always generate new content
            text_model = get_text_model()
            response = await text_model.generate_content_async(text_prompt)
            full_markdown_text = response.text

        if not full_markdown_text or full_markdown_text.strip() == "":
            st.error('Failed to generate editorial text or text was empty.')
            return

        # Parse sections more efficiently
        sections_markdown = parse_sections(full_markdown_text)
        if not sections_markdown:
            st.error("No sections found in generated text.")
            st.markdown(full_markdown_text)
            return

        # Process sections sequentially to maintain inline order
        processed_sections = []
        for section in sections_markdown:
            processed_section = await process_single_section(section, room_type, design_style, color_palette, output_dir)
            if processed_section:
                processed_sections.append(processed_section)

        # Combine all processed sections with their images
        final_content = "\n\n".join(processed_sections)
        
        # Save the complete content as HTML
        html_path = save_to_html(final_content, output_dir)
        logger.info(f"Saved HTML content to: {html_path}")
        
        # Store the generated content paths in session state
        st.session_state.generated_content = {
            'html_path': html_path,
            'output_dir': output_dir,
            'markdown_content': final_content  # Store the markdown content as well
        }

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        st.error(f"An error occurred: {str(e)}")

def run_async_generate_content(room_type: str, design_style: str, color_palette: str, key_elements: str, inspirational_photo_details: str):
    """Wrapper function to run generate_content in a new event loop."""
    try:
        # Create a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the async function
        result = loop.run_until_complete(
            generate_content(
                room_type=room_type,
                design_style=design_style,
                color_palette=color_palette,
                key_elements=key_elements,
                inspirational_photo_details=inspirational_photo_details
            )
        )
        
        # Clean up
        loop.close()
        return result
    except Exception as e:
        logger.error(f"Error in run_async_generate_content: {e}", exc_info=True)
        st.error(f"An error occurred: {str(e)}")
        return None

def reset_session_state():
    """Reset all session state variables to their initial state."""
    st.session_state.form_data = {
        'room_type': '',
        'design_style': '',
        'color_palette': '',
        'key_elements': '',
        'inspirational_photo_details': ''
    }
    st.session_state.generated_content = {
        'html_path': None,
        'output_dir': None,
        'markdown_content': None
    }
    if 'zip_content' in st.session_state:
        del st.session_state.zip_content 

def display_html_report(html_path: str, output_dir: str):
    """Display the generated HTML report and provide download options."""
    # Create a zip file containing all generated content
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add the HTML file
        zip_file.write(html_path, os.path.basename(html_path))
        
        # Add all images from the output directory
        for root, _, files in os.walk(output_dir):
            for file in files:
                if file.endswith(('.jpg', '.jpeg', '.png')):
                    file_path = os.path.join(root, file)
                    # Store images in the root directory of the zip
                    zip_file.write(file_path, os.path.basename(file_path))
    
    # Prepare the zip file for download
    zip_buffer.seek(0)
    
    # Display download button
    st.download_button(
        label="Download Design Report (ZIP)",
        data=zip_buffer,
        file_name="interior_design_report.zip",
        mime="application/zip"
    ) 