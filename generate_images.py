import streamlit as st
import os
from dotenv import load_dotenv
from interior_design_generatorv2 import run_async_generate_content, get_text_model, get_image_model
import asyncio
import base64
from datetime import datetime
from get_image_colors import get_image_colors
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables (moved outside main function)
load_dotenv()

def select_image_callback(image_path, option_number):
    """Callback function to set selected image and option in session state."""
    logger.info(f"Callback: Option {option_number} selected")
    st.session_state.selected_image = image_path
    st.session_state.selected_option = option_number
    logger.info(f"DEBUG: Callback: Selected image set to: {st.session_state.selected_image}")

def main():
    logger.info("Starting main function")

    # Initialize session state variables if they don't exist
    if 'selected_image' not in st.session_state:
        st.session_state.selected_image = None
    if 'selected_option' not in st.session_state:
        st.session_state.selected_option = None
    if 'generated_images' not in st.session_state:
        st.session_state.generated_images = None
    if 'output_dir' not in st.session_state:
        st.session_state.output_dir = None
    if 'concept_text' not in st.session_state:
        st.session_state.concept_text = None

    st.set_page_config(
        page_title="Interior Design Generator - Image Generation",
        page_icon="🎨",
        layout="wide"
    )

    st.title("Interior Design Image Generator")
    st.write("Generate beautiful interior design images based on your preferences.")

    # Create a form for the inputs
    with st.form("image_generation_form"):
        logger.info("Creating form")
        # Room Type Selection
        room_type = st.selectbox(
            "Room Type",
            options=[
                "Entryway / Foyer",
                "Living Room",
                "Family Room",
                "Dining Room",
                "Kitchen",
                "Breakfast Nook",
                "Bedroom",
                "Guest Bedroom",
                "Kid's Bedroom",
                "Nursery",
                "Bathroom",
                "Guest Bathroom",
                "Powder Room",
                "Home Office",
                "Study",
                "Laundry Room",
                "Mudroom",
                "Hallway",
                "Front Porch",
                "Deck",
                "Deck with Outdoor Kitchen",
                "Patio",
                "Backyard",
                "Backyard with Pool",
                "Man Cave",
                "She Shed",
                "Game Room"
            ],
            index=0,
            placeholder="Select a room type"
        )

        # Design Style Selection
        design_style = st.multiselect(
            "Design Style (Select up to 3)",
            options=[
                "Traditional",
                "Modern",
                "Contemporary",
                "Transitional",
                "Farmhouse (Modern Farmhouse)",
                "Scandinavian",
                "Minimalist",
                "Bohemian (Boho)",
                "Coastal / Hamptons",
                "Mid-Century Modern",
                "Industrial",
                "Rustic",
                "Organic Modern",
                "Japandi",
                "French Country",
                "Mediterranean",
                "Spanish Modern",
                "Shabby Chic",
                "Art Deco",
                "Hollywood Glam (Hollywood Regency)",
                "Southwestern",
                "Biophilic",
                "Wabi-Sabi",
                "Maximalist",
                "Eclectic"
            ],
            max_selections=3,
            placeholder="Select up to 3 design styles"
        )

        # Color Scheme Input
        color_scheme = st.text_input(
            "Color Scheme",
            placeholder="e.g., Neutral with blue accents, Warm earth tones, etc."
        )

        # Key Design Elements Input
        key_elements = st.text_input(
            "Key Design Elements (Optional)",
            placeholder="e.g., Large windows, fireplace, built-in bookshelves"
        )

        # Submit button
        submitted = st.form_submit_button("Generate Images")

    if submitted:
        logger.info("Form submitted")
        if not all([room_type, design_style, color_scheme]):
            st.error("Please fill in all required fields: Room Type, Design Style, and Color Scheme")
            return

        # Clear previous results from session state
        st.session_state.selected_image = None
        st.session_state.selected_option = None
        st.session_state.generated_images = None
        st.session_state.output_dir = None
        st.session_state.concept_text = None

        # Display the selected options
        st.write("### Selected Options:")
        st.write(f"**Room Type:** {room_type}")
        st.write(f"**Design Style:** {', '.join(design_style)}")
        st.write(f"**Color Scheme:** {color_scheme}")
        if key_elements:
            st.write(f"**Key Design Elements:** {key_elements}")

        # Generate content
        with st.spinner("Generating your interior design concept and images..."):
            # Create output directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = f"generated_content_{timestamp}"
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Created output directory: {output_dir}")
            st.session_state.output_dir = output_dir # Store output_dir in session state

            # Generate text content for overall concept
            text_model = get_text_model()
            text_prompt = f"""Create a detailed interior design concept for a {room_type} in {', '.join(design_style)} style with a {color_scheme} color scheme{f' and featuring {key_elements}' if key_elements else ''}.

Please provide a concise 5-sentence design plan focusing on the Overall Concept and Style section only. Each sentence should be impactful and informative.

Format the response in markdown with a clear section header (##) for the Overall Concept and Style section."""
            
            response = asyncio.run(text_model.generate_content_async(text_prompt))
            concept_text = response.text
            st.session_state.concept_text = concept_text # Store concept_text in session state
            logger.info("Stored concept text in session state.")

            # Generate images
            image_model = get_image_model()
            image_prompt = f"High-quality interior design photograph. Room type: {room_type}. Design style: {', '.join(design_style)}. Color palette: {color_scheme}{f'. Key elements: {key_elements}' if key_elements else ''}. The image should be a realistic, professional interior design photograph."
            
            # Generate images synchronously
            response = image_model.generate_images(
                prompt=image_prompt,
                number_of_images=3,
                language="en",
                aspect_ratio="1:1",
                safety_filter_level="block_some",
                person_generation="allow_adult"
            )

            if response and response.images:
                # Save images and store paths in session state
                image_paths = []
                for i, image in enumerate(response.images):
                    image_data = base64.b64encode(image._image_bytes).decode('utf-8')
                    image_filename = f"design_option_{i+1}.jpeg"
                    image_path = os.path.join(output_dir, image_filename)
                    
                    with open(image_path, "wb") as f:
                        f.write(base64.b64decode(image_data))
                    
                    image_paths.append(image_path)
                    logger.info(f"Saved image {i+1} to {image_path}")
                
                st.session_state.generated_images = image_paths
                logger.info("Stored generated image paths in session state.")
                

    # Display the concept text if it exists in session state
    if st.session_state.concept_text:
        st.markdown("### Overall Concept and Style")
        st.markdown(st.session_state.concept_text)
        
        logger.info("Displayed concept text from session state.")

    # Display generated images and selection buttons if images exist in session state
    if st.session_state.generated_images:
        st.write("### Generated Images")
        st.write("Please select your preferred image:")
        
        cols = st.columns(3)
        
        for i, image_path in enumerate(st.session_state.generated_images):
            with cols[i]:
                st.image(image_path, caption=f"Option {i+1}")
                # Use on_click callback to reliably set session state before rerun
                st.button(f"Select Option {i+1}", key=f"select_{i}", 
                          on_click=select_image_callback, args=(image_path, i+1))

    # Display success message if an option is selected
    if st.session_state.selected_option:
        st.success(f"You selected Option {st.session_state.selected_option}!")

    # Display color analysis if an image is selected
    logger.info("Checking for selected image in session state for color analysis")
    logger.info(f"DEBUG: Session state keys: {list(st.session_state.keys())}")
    logger.info(f"DEBUG: st.session_state.selected_image value: {st.session_state.selected_image}")
    if st.session_state.selected_image:
        logger.info(f"Selected image found for color analysis: {st.session_state.selected_image}")
        try:
            with st.spinner("Analyzing colors in the selected image..."):
                logger.info("Calling get_image_colors")
                color_palette = get_image_colors(st.session_state.selected_image)
                logger.info(f"Color palette received: {color_palette}")
                if color_palette:
                    colors = json.loads(color_palette)
                    st.write("### Color Palette Analysis")
                    
                    # Create columns for color display
                    color_cols = st.columns(len(colors))
                    
                    for idx, color in enumerate(colors):
                        with color_cols[idx]:
                            # Create a colored box
                            st.markdown(
                                f'<div style="background-color: {color["hex"]}; width: 100%; height: 50px; border-radius: 5px;"></div>',
                                unsafe_allow_html=True
                            )
                            st.write(f"**{color['name']}**")
                            st.write(f"Hex: {color['hex']}")
                            st.write(f"Type: {color['type']}")
                else:
                    st.warning("Could not extract color palette from the image.")
        except Exception as e:
            logger.error(f"Error in color analysis: {str(e)}", exc_info=True)
            st.error(f"Error analyzing colors: {str(e)}")
    else:
        logger.info("No selected image found in session state for color analysis")

if __name__ == "__main__":
    main()
