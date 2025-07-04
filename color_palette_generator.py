import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def generate_color_palette(colors_data):
    """
    Generates a color palette dictionary from a list of color data.

    Args:
        colors_data (list of dict): A list where each dictionary represents a color
                                     with 'name', 'hex', and 'type' keys.
                                     Example: {'name': 'Red', 'hex': '#FF0000', 'type': 'primary'}

    Returns:
        dict: A dictionary representing the color palette, categorized by type.
              Example: {
                  'primary': [{'name': 'Red', 'hex': '#FF0000'}],
                  'secondary': [{'name': 'Green', 'hex': '#00FF00'}]
              }
    """
    # Initialize the palette dictionary to store primary and secondary colors.
    palette = {
        'primary': [],
        'secondary': []
    }

    # Iterate through each color's information provided in the input list.
    for color_info in colors_data:
        color_type = color_info.get('type', '').lower()

        if color_type in palette:
            palette[color_type].append({
                'name': color_info.get('name'),
                'hex': color_info.get('hex')
            })
        else:
            print(f"Warning: Unknown color type '{color_type}' for color '{color_info.get('name', 'Unnamed Color')}'. Skipping.")

    return palette


def visualize_color_palette(palette, filename=None):
    """
    Generates and displays a visual representation of the color palette
    with primary colors on a top row and secondary colors on a bottom row,
    with blocks flush against each other horizontally.
    Optionally saves the image to a specified file.

    Args:
        palette (dict): The color palette dictionary generated by generate_color_palette.
                        Example: {
                            'primary': [{'name': 'Red', 'hex': '#FF0000'}],
                            'secondary': [{'name': 'Green', 'hex': '#00FF00'}]
                        }
        filename (str, optional): The name of the file to save the image to (e.g., 'my_palette.png').
                                  If None, the image will only be displayed and not saved.
    """
    primary_colors = palette.get('primary', [])
    secondary_colors = palette.get('secondary', [])

    # Determine the maximum number of colors in any single row for general sizing,
    # though block width will be calculated per row for exact fit.
    max_colors_in_row = max(len(primary_colors), len(secondary_colors)) if (primary_colors or secondary_colors) else 2

    # Adjust figure size for two rows and varying number of colors
    fig_width = max(10, max_colors_in_row * 2.5)  # Minimum 10, or 2.5 units per color (rough guide)
    fig, ax = plt.subplots(figsize=(fig_width, 7))  # Increased height for better vertical spacing
    ax.set_facecolor('#FFFFFF')  # White background for the main plot area

    # Define common parameters for color blocks and text placement
    block_height = 0.18  # Relative height of each color block

    # Define vertical positions for sections (Y coordinates for the bottom of the color blocks)
    y_block_primary = 0.65  # Top row of color blocks
    y_block_secondary = 0.25  # Bottom row of color blocks

    # --- Primary Colors Row ---
    if primary_colors:
        num_primary = len(primary_colors)
        # Calculate block width to fill the horizontal space (0 to 1) without gaps
        primary_block_width = 1.0 / num_primary if num_primary > 0 else 0
        x_start_primary = 0.0  # Start from the left edge of the plotting area

        # Add a title for the Primary Colors section (positioned above the primary blocks)
        ax.text(0.5, y_block_primary + block_height + 0.07, 'Primary Colors', fontsize=14, fontweight='bold',
                ha='center', transform=ax.transAxes)

        # Iterate and draw each primary color block and its labels
        for i, color in enumerate(primary_colors):
            current_x = x_start_primary + i * primary_block_width

            rect = mpatches.Rectangle(
                (current_x, y_block_primary),  # (x, y) coordinates for the bottom-left corner
                primary_block_width,  # Use calculated width for primary row
                block_height,
                facecolor=color['hex'],
                edgecolor='none',  # No border for a cleaner look
                transform=ax.transAxes
            )
            ax.add_patch(rect)

            # Add color name text below the block
            ax.text(
                current_x + primary_block_width / 2,  # X position: center of the block
                y_block_primary - 0.05,  # Y position: slightly below the block
                color['name'],
                fontsize=10,
                ha='center',  # Horizontal alignment: center
                va='top',  # Vertical alignment: top (text flows downwards from this point)
                fontweight='bold',
                transform=ax.transAxes
            )

            # Add hex code text further below the block
            ax.text(
                current_x + primary_block_width / 2,  # X position: center of the block
                y_block_primary - 0.1,  # Y position: further below the name
                color['hex'],
                fontsize=9,
                ha='center',  # Horizontal alignment: center
                va='top',  # Vertical alignment: top
                color='#555555',  # Slightly darker grey for hex code
                transform=ax.transAxes
            )

    # --- Secondary Colors Row ---
    if secondary_colors:
        num_secondary = len(secondary_colors)
        # Calculate block width to fill the horizontal space (0 to 1) without gaps
        secondary_block_width = 1.0 / num_secondary if num_secondary > 0 else 0
        x_start_secondary = 0.0  # Start from the left edge of the plotting area

        # Add a title for the Secondary Colors section
        # Positioned above the secondary blocks, in the vertical gap between sections
        secondary_title_y = (y_block_primary - 0.1 + y_block_secondary + block_height) / 2 + 0.02
        ax.text(0.5, secondary_title_y, 'Secondary Colors', fontsize=14, fontweight='bold', ha='center',
                transform=ax.transAxes)

        # Iterate and draw each secondary color block and its labels
        for i, color in enumerate(secondary_colors):
            current_x = x_start_secondary + i * secondary_block_width

            rect = mpatches.Rectangle(
                (current_x, y_block_secondary),
                secondary_block_width,  # Use calculated width for secondary row
                block_height,
                facecolor=color['hex'],
                edgecolor='none',
                transform=ax.transAxes
            )
            ax.add_patch(rect)

            # Add color name text below the block
            ax.text(
                current_x + secondary_block_width / 2,
                y_block_secondary - 0.05,
                color['name'],
                fontsize=10,
                ha='center',
                va='top',
                fontweight='bold',
                transform=ax.transAxes
            )

            # Add hex code text further below the block
            ax.text(
                current_x + secondary_block_width / 2,
                y_block_secondary - 0.1,
                color['hex'],
                fontsize=9,
                ha='center',
                va='top',
                color='#555555',
                transform=ax.transAxes
            )

    # Remove axis ticks and labels for a cleaner, image-like appearance.
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlim(0, 1)  # Ensure the plotting area spans from 0 to 1
    ax.set_ylim(0, 1)

    # Remove the bounding box around the plot area to match the example's aesthetic.
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)

    # Adjust layout to prevent labels from overlapping
    plt.tight_layout()

    # Save the figure if a filename is provided.
    if filename:
        try:
            plt.savefig(filename, bbox_inches='tight', dpi=300, transparent=True)
            print(f"Color palette image saved as: {filename}")
        except Exception as e:
            print(f"Error saving image: {e}")

    # Display the plot.
    plt.show()

# --- Example Usage ---
# Using colors that are somewhat similar to your provided image and
# explicitly defining primary and secondary types for demonstration.
my_colors = [
    {'name': 'Hot Pink', 'hex': '#FFAEBC', 'type': 'primary'},
    {'name': 'Sunshine Yellow', 'hex': '#FFD700', 'type': 'primary'},
    {'name': 'Ocean Blue', 'hex': '#00008B', 'type': 'primary'},
    {'name': 'Tiffany Blue', 'hex': '#A0E7E5', 'type': 'secondary'},
    {'name': 'Mint', 'hex': '#B4F8C8', 'type': 'secondary'},
    {'name': 'Pumpkin Orange', 'hex': '#FF7F50', 'type': 'secondary'}
]

# Generate the color palette using the original function
my_palette = generate_color_palette(my_colors)
print(my_palette)

visualize_color_palette(my_palette, filename='my_flush_color_palette.png')