import colorgram
from PIL import Image
from colorthief import ColorThief
import matplotlib.pyplot as plt
from colormap import rgb2hex, hex2rgb
import ast
import re
import colorsys
import webcolors

from googleapiclient.mimeparse import quality

image_path = "C:\InteriorGenie\generated_content_20250623_100956\Modern_Contemporary_Entryway___view_2_101019.jpeg"
if __name__ == '__main__':
    ct = ColorThief(image_path)
    dominant_color = ct.get_color(quality=1)

    #print(dominant_color)
    #plt.imshow([[dominant_color]])

    #plt.show()

    palette = ct.get_palette(color_count=6)
    print(palette)
    plt.imshow([[palette[i] for i in range (6)]])
    plt.show()

    for color in palette:
        print(color)
        print(f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}")
        print(colorsys.rgb_to_hsv(*color))
        print(colorsys.rgb_to_hls(*color))


    print(webcolors.hex_to_name("#daa520"))
