import os
import numpy as np
import multiprocessing

from PIL import Image
from multiprocessing import Pool
from SpriteSplitter import *


# The number of available CPU cores
#NUMBER_OF_PROCESSES = multiprocessing.cpu_count() - 2




def segment_image_by_color(image_data):
    """
    Segment the image by color.

    Args:
        image_data (numpy.ndarray): The pixel data of the original image as a NumPy array.
        n_colors (int): The number of colors to segment the image into.

    Returns:
        dict: A dictionary with keys as color (r, g, b) and values as masks of the segmented parts.
    """
    # Convert image data to a list of tuples and find unique colors
    unique_colors = set(map(tuple, image_data.reshape(-1, image_data.shape[2])))

    # Create masks for each unique color
    segmented_masks = {}
    for color in unique_colors:
        mask = np.all(image_data[:, :, :3] == color, axis=-1)
        segmented_masks[color] = mask

    return segmented_masks


def process_color_segment(color, mask, output_folder, image_data, min_size, alpha_threshold):
    print(f"Processing color segment: {color}")
    color_segment_folder = os.path.join(output_folder, f"{color[0]:02x}{color[1]:02x}{color[2]:02x}")
    os.makedirs(color_segment_folder, exist_ok=True)

    # Apply mask to alpha channel
    masked_image_data = np.copy(image_data)
    masked_image_data[:, :, 3] = np.where(mask, image_data[:, :, 3], 0)

    split_sprite(image_data=masked_image_data, output_folder=color_segment_folder, min_size=min_size, alpha_threshold=alpha_threshold)

def split_sprite_by_color(image_path, output_folder, min_size=10, alpha_threshold=0, number_of_processes=multiprocessing.cpu_count()-2):
    """
    Splits an image into separate components based on color segments and saves each as a new image.

    Args:
        image_path (str): The path to the source image.
        output_folder (str): The directory where the split images will be saved.
        min_size (int, optional): The minimum pixel count for a component to be saved. Defaults to 10.
        alpha_threshold (int, optional): The alpha value threshold to consider a pixel as part of a component. Defaults to 0.
    """
    print(f"Loading an image from {image_path}\n")
    with Image.open(image_path) as image:
        if image.mode in ['P', 'L']:
            image = image.convert('RGBA')
        image_data = np.array(image)

    # Segment image by color
    segmented_masks = segment_image_by_color(image_data[:, :, :3])

    # Parallel processing of each color segment
    with Pool(processes=number_of_processes) as pool:
        pool.starmap(process_color_segment, [(color, mask, output_folder, image_data, min_size, alpha_threshold) for color, mask in segmented_masks.items()])
    
    print("All color segments have been processed.")




#if __name__ == '__main__':
#    split_sprite_by_color('MainSprite.png', 'Output', min_size=100, alpha_threshold=188)