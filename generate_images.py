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

def generate_content(text_model, text_prompt):
    """Helper function to generate content synchronously"""
    try:
        logger.info("Starting text generation process")
        logger.info(f"Text prompt: {text_prompt}")
        
        # Ensure we have a clean event loop
        loop = ensure_event_loop()
        logger.info("Ensured clean event loop")
        
        # Generate content
        logger.info("Calling generate_content_async")
        response = loop.run_until_complete(text_model.generate_content_async(text_prompt))
        logger.info("Received response from model")
        
        if response and hasattr(response, 'text') and response.text:
            logger.info("Successfully generated text content")
            return response.text
        else:
            logger.error(f"Empty or invalid response from text model. Response type: {type(response)}")
            if response:
                logger.error(f"Response attributes: {dir(response)}")
            return None
    except Exception as e:
        logger.error(f"Error generating content: {str(e)}", exc_info=True)
        return None
    finally:
        # Don't close the loop here as it might be needed for other operations
        pass

def regenerate_images_callback():
    """Callback function to regenerate images with the same parameters."""
    logger.info("Regenerating images with same parameters")
    if st.session_state.form_data:
        # Create new output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"generated_content_{timestamp}"
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Created new output directory: {output_dir}")
        st.session_state.output_dir = output_dir

        # Generate images
        image_model = get_image_model()
        
        # Build the image prompt
        key_elements_text = f". Key elements: {st.session_state.form_data['key_elements']}" if st.session_state.form_data.get('key_elements') else ""
        image_prompt = (
            f"High-quality interior design photograph. "
            f"Room type: {st.session_state.form_data['room_type']}. "
            f"Design style: {', '.join(st.session_state.form_data['design_style'])}. "
            f"Color palette: {st.session_state.form_data['color_scheme']}"
            f"{key_elements_text}. "
            f"The image should be a realistic, professional interior design photograph."
        )
        
        # Generate images synchronously
        response = image_model.generate_images(
            prompt=image_prompt,
            number_of_images=3,
            language="en",
            aspect_ratio="4:3",
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
            logger.info("Stored new generated image paths in session state.")
        else:
            st.error("Failed to generate new images. Please try again.")

def start_over_callback():
    """Callback function to reset all session state variables."""
    logger.info("Resetting all session state variables")
    try:
        # Clean up any existing event loops
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.stop()
            if not loop.is_closed():
                loop.close()
        except Exception as e:
            logger.info(f"No active event loop to clean up: {str(e)}")

        # Clear all session state variables
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        logger.info("All session state variables cleared")
    except Exception as e:
        logger.error(f"Error during reset: {str(e)}", exc_info=True)

def ensure_event_loop():
    """Ensure we have a clean event loop for async operations."""
    try:
        # Try to get the current event loop
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            # Create new event loop if the current one is closed
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        # If no event loop exists, create a new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop

def load_css():
    """Load the external CSS file."""
    with open('styles.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def main():
    # Set page config must be the first Streamlit command
    st.set_page_config(
        page_title="Interior Design Generator - Image Generation",
        page_icon="🎨",
        layout="wide"
    )

    logger.info("Starting main function")

    # Load custom styling
    load_css()

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
    if 'form_data' not in st.session_state:
        st.session_state.form_data = None
    if 'show_reset_confirm' not in st.session_state:
        st.session_state.show_reset_confirm = False

    st.title("Interior Design Image Generator")
    st.write("Generate beautiful interior design images based on your preferences.")

    # Add Start Over button at the top of the page
    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("🔄 Start Over", use_container_width=True):
            st.session_state.show_reset_confirm = True

    # Show confirmation modal if needed
    if st.session_state.show_reset_confirm:
        st.markdown("""
            <style>
            .stButton button {
                width: 100%;
            }
            </style>
        """, unsafe_allow_html=True)
        
        st.warning("Are you sure you want to start over? This will clear all your current selections and generated content.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Cancel", use_container_width=True):
                st.session_state.show_reset_confirm = False
                st.rerun()
        with col2:
            if st.button("Yes, Start Over", type="primary", use_container_width=True):
                start_over_callback()
                st.session_state.show_reset_confirm = False
                st.rerun()

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
                "Primary Bathroom",
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

        # Store form data in session state
        st.session_state.form_data = {
            'room_type': room_type,
            'design_style': design_style,
            'color_scheme': color_scheme,
            'key_elements': key_elements
        }

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
            try:
                # Create output directory
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir = f"generated_content_{timestamp}"
                os.makedirs(output_dir, exist_ok=True)
                logger.info(f"Created output directory: {output_dir}")
                st.session_state.output_dir = output_dir

                # Generate text content for overall concept
                logger.info("Initializing text model")
                text_model = get_text_model()
                if not text_model:
                    logger.error("Failed to initialize text model")
                    st.error("Failed to initialize text model. Please try again.")
                    return

                text_prompt = f"""Create a detailed interior design concept for a {room_type} in {', '.join(design_style)} style with a {color_scheme} color scheme{f' and featuring {key_elements}' if key_elements else ''}.

Please provide a concise 5-sentence design plan focusing on the Overall Concept and Style section only. Each sentence should be impactful and informative.

Format the response in markdown with a clear section header (##) for the Overall Concept and Style section."""
                
                logger.info("Generating concept text")
                concept_text = generate_content(text_model, text_prompt)
                if concept_text:
                    st.session_state.concept_text = concept_text
                    logger.info("Successfully stored concept text in session state")
                else:
                    logger.error("Failed to generate concept text")
                    st.error("Failed to generate concept text. Please try again.")
                    return

                # Generate images
                logger.info("Initializing image model")
                image_model = get_image_model()
                if not image_model:
                    logger.error("Failed to initialize image model")
                    st.error("Failed to initialize image model. Please try again.")
                    return

                image_prompt = f"High-quality interior design photograph. Room type: {room_type}. Design style: {', '.join(design_style)}. Color palette: {color_scheme}{f'. Key elements: {key_elements}' if key_elements else ''}. The image should be a realistic, professional interior design photograph."
                
                # Generate images synchronously
                logger.info("Generating images")
                response = image_model.generate_images(
                    prompt=image_prompt,
                    number_of_images=3,
                    language="en",
                    aspect_ratio="4:3",
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
                    logger.info("Successfully stored generated image paths in session state")
                else:
                    logger.error("Failed to generate images")
                    st.error("Failed to generate images. Please try again.")
                    return
            except Exception as e:
                logger.error(f"Error during generation: {str(e)}", exc_info=True)
                st.error("An error occurred during generation. Please try again.")
                return

    # Display the concept text if it exists in session state
    if st.session_state.concept_text:
        st.markdown("### Overall Concept and Style")
        st.markdown(st.session_state.concept_text)
        logger.info("Displayed concept text from session state.")

    # Display generated images and selection buttons if images exist in session state
    if st.session_state.generated_images:
        # Add regenerate images button if no image is selected
        if not st.session_state.selected_image:
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("🔄 Generate New Images", use_container_width=True):
                    regenerate_images_callback()
                    st.rerun()

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
