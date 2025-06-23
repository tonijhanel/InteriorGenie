import colorgram
from PIL import Image

import matplotlib.colors as mcolors
from colormap import rgb2hex, hex2rgb
import ast
import re

def string_to_rgb_tuple_regex(rgb_string):
    """
    Extracts r, g, b values from the string using regular expressions
    and returns them as a tuple.
    """
    # Regex to find numbers after r=, g=, b=
    match = re.search(r"r=(\d+), g=(\d+), b=(\d+)", rgb_string)

    if match:
        r = int(match.group(1))
        g = int(match.group(2))
        b = int(match.group(3))
        return (r, g, b)
    else:
        raise ValueError("Invalid RGB string format")

def get_colors_and_proportions(image_path, num_colors=5):
    """
    Extracts dominant colors and their proportions as a list of dictionaries,
    with RGB as plain numeric tuples.
    """
    colors_raw = colorgram.extract(image_path, num_colors)
    result = []
    for color_obj in colors_raw:
        result.append({
            'rgb': tuple(color_obj.rgb), # Convert namedtuple to plain tuple
            'proportion': color_obj.proportion
        })
    return result

if __name__ == '__main__':
    print("hello")

    colors = colorgram.extract('C:\InteriorGenie\generated_content_20250623_100956\Modern_Contemporary_Entryway___view_4_101019.jpeg', 6)
    print(colors)
    print(type(colors[0]))
    extracted_colors_dicts = []
    for color_obj in colors:
        color_dict = {
            'rgb': str(color_obj.rgb),
            'proportion': color_obj.proportion
        }
        extracted_colors_dicts.append(color_dict)

    print(extracted_colors_dicts)

    first_color = extracted_colors_dicts[0]
    print(f"\nRGB of the first dominant color: {first_color['rgb']}")
    print(f"Proportion of the first dominant color: {first_color['proportion']:.2f}")

    # Test the function
    rgb_str = "Rgb(r=172, g=161, b=148)"
    rgb_tuple = string_to_rgb_tuple_regex(rgb_str)
    print(f"Original String: {rgb_str}")
    print(f"Resulting Tuple: {rgb_tuple}")
    print(f"Type of Result: {type(rgb_tuple)}")

    first_rgb = string_to_rgb_tuple_regex(first_color['rgb'])
    print(f"Test RGB: {rgb_str}")

    newvalue = tuple(rgb_str)
    print(newvalue)

    extracted = get_colors_and_proportions("C:\InteriorGenie\generated_content_20250623_100956\Modern_Contemporary_Entryway___view_4_101019.jpeg", num_colors=6)

    for item in extracted:
        print(item)
        print(item['rgb'])
        print(item['proportion'])
