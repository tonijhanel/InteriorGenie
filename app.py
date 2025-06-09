import streamlit as st
import os
import asyncio
from dotenv import load_dotenv
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import shutil
import json
import zipfile
import io
from markdown import markdown

from interior_design_generator import (
    generate_content,
    setup_output_directory,
    save_to_html,
    display_html_report,
    reset_session_state,
    TEST_MODE,
    TEST_RESPONSES_DIR,
    run_async_generate_content
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def main():
    st.set_page_config(
        page_title="Interior Design Generator",
        page_icon="🏠",
        layout="wide"
    )

    st.title("Interior Design Generator")
    st.write("Generate beautiful interior design concepts with AI-powered text and images.")

    # Display test mode status
    if TEST_MODE:
        st.info("Running in TEST MODE - Using cached responses when available")

    # Initialize session state for form data if not exists
    if 'form_data' not in st.session_state:
        st.session_state.form_data = {
            'room_type': '',
            'design_style': '',
            'color_palette': '',
            'key_elements': '',
            'inspirational_photo_details': ''
        }
    
    # Initialize session state for generated content
    if 'generated_content' not in st.session_state:
        st.session_state.generated_content = {
            'html_path': None,
            'output_dir': None,
            'markdown_content': None
        }

    # Add New Design button at the top if content is generated
    if st.session_state.generated_content['html_path']:
        if st.button("New Design", type="primary"):
            reset_session_state()
            st.rerun()

    # Create a container for the form
    form_container = st.container()
    
    # Input form
    with form_container:
        with st.form("design_form", clear_on_submit=False):
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
                index=0 if not st.session_state.form_data['room_type'] else None,
                placeholder="Select a room type"
            )
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
                default=st.session_state.form_data['design_style'].split(', ') if st.session_state.form_data['design_style'] else None,
                placeholder="Select up to 3 design styles",
                max_selections=3
            )
            color_palette = st.text_input("Color Palette", 
                                        value=st.session_state.form_data['color_palette'],
                                        placeholder="e.g., Neutral with blue accents")
            key_elements = st.text_input("Key Design Elements (optional)", 
                                       value=st.session_state.form_data['key_elements'],
                                       placeholder="e.g., Velvet sofa, brass fixtures")
            inspirational_photo_details = st.text_area("Inspirational Photo Details (optional)", 
                                                     value=st.session_state.form_data['inspirational_photo_details'],
                                                     placeholder="Describe any inspirational photo you'd like to reference")

            submitted = st.form_submit_button("Generate Design")

    if submitted:
        if not all([room_type, design_style, color_palette]):
            st.error("Please fill in all required fields: Room Type, Design Style, and Color Palette")
            return

        # Update session state with form data
        st.session_state.form_data = {
            'room_type': room_type,
            'design_style': ', '.join(design_style),
            'color_palette': color_palette,
            'key_elements': key_elements,
            'inspirational_photo_details': inspirational_photo_details
        }

        with st.spinner("Generating your interior design concept..."):
            run_async_generate_content(
                room_type=room_type,
                design_style=st.session_state.form_data['design_style'],
                color_palette=color_palette,
                key_elements=key_elements or "Not specified",
                inspirational_photo_details=inspirational_photo_details or "None provided"
            )
    
    # Display content if it exists
    if st.session_state.generated_content['html_path'] and st.session_state.generated_content['output_dir']:
        # Create a container for the content
        content_container = st.container()
        
        with content_container:
            # Split the content into sections
            sections = st.session_state.generated_content['markdown_content'].split('\n\n')
            
            for section in sections:
                # Check if the section contains an image
                if '<div class="section-image">' in section:
                    # Split the section into parts
                    parts = section.split('<div class="section-image">')
                    
                    # Display the text before the image (section title)
                    if parts[0].strip():
                        st.markdown(parts[0].strip())
                    
                    # Extract and display the image
                    img_start = parts[1].find('<img src="') + 10
                    img_end = parts[1].find('"', img_start)
                    img_path = parts[1][img_start:img_end]
                    
                    caption_start = parts[1].find('<div class="image-caption">') + 25
                    caption_end = parts[1].find('</div>', caption_start)
                    caption = parts[1][caption_start:caption_end]
                    
                    # Get the full path to the image
                    full_image_path = os.path.join(
                        st.session_state.generated_content['output_dir'],
                        img_path
                    )
                    
                    # Display the image if it exists
                    if os.path.exists(full_image_path):
                        st.image(full_image_path, caption=caption)
                    
                    # Display the remaining content after the image
                    content_start = parts[1].find('</div>', caption_end) + 6
                    if content_start < len(parts[1]):
                        st.markdown(parts[1][content_start:].strip())
                else:
                    # If no image, just display the text
                    st.markdown(section)
        
        # Display the download button
        display_html_report(
            st.session_state.generated_content['html_path'],
            st.session_state.generated_content['output_dir']
        )

if __name__ == "__main__":
    main() 