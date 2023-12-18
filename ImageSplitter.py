import os
import numpy as np
import multiprocessing
import traceback

from PIL import Image
from multiprocessing import Pool
from sklearn.cluster import KMeans
from SpriteSplitter import split_sprite


def worker_segmentation(args, mode):
    try:
        if mode == 'kmeans':
            color, labels_reshaped, color_index = args
            mask = labels_reshaped == color_index
            progress_message = f"KMeans: Processed color index {color_index}"
        elif mode == 'rounding':
            rounded_data, color, i = args
            mask = np.all(rounded_data[:, :, :3] == color, axis=-1)
            progress_message = f"Rounding: Processed segment {i+1}"
        else:
            raise ValueError("Invalid mode")

        return tuple(color), mask, progress_message
    except Exception as e:
        return None, None, f"Error in worker: {traceback.format_exc()}"

def segment_image_by_color(image_data, number_of_colors, round_factor=10):
    """
    Segment the image by quantizing colors using KMeans clustering or rounding color values.

    Args:
        image_data (numpy.ndarray): The pixel data of the original image as a NumPy array.
        number_of_colors (int): The number of colors to segment the image into.
        round_factor (int): The factor to round color values to reduce color space.

    Returns:
        dict: A dictionary with keys as color (r, g, b) and values as masks of the segmented parts.
    """

    if number_of_colors != 0:
        
        # Reshape image data for clustering
        pixels = image_data.reshape(-1, 3)
        unique_colors_count = len(np.unique(pixels, axis=0))
        number_of_colors = min(number_of_colors, unique_colors_count)

        # Perform KMeans clustering
        kmeans = KMeans(n_clusters=number_of_colors, n_init=10, random_state=0).fit(pixels)
        labels = kmeans.labels_
        quantized_colors = kmeans.cluster_centers_.astype(int)

        # Initialize segmented masks
        segmented_masks = {tuple(color): np.zeros(image_data.shape[:2], dtype=bool) for color in quantized_colors}

        labels_reshaped = labels.reshape(image_data.shape[:2])
        args = [(color, labels_reshaped, idx) for idx, color in enumerate(quantized_colors)]
        mode = 'kmeans'
    else:
        # Rounding the colors
        rounded_data = (image_data // round_factor) * round_factor
        unique_colors = np.unique(rounded_data.reshape(-1, 3), axis=0)
        args = [(rounded_data, color, i) for i, color in enumerate(unique_colors)]
        mode = 'rounding'

    # Prepare arguments for starmap
    starmap_args = [(arg, mode) for arg in args]

    # Start multiprocessing
    with Pool() as pool:
        results = pool.starmap(worker_segmentation, starmap_args)

    segmented_masks = {}
    for color, mask, message in results:
        if color is not None and mask is not None:
            segmented_masks[color] = mask
        print(message)  # Print progress messages or errors

    return segmented_masks



def process_color_segment(color, mask, output_folder, image_data, min_size, merge_distance, alpha_threshold):
    print(f"Processing color segment: {color}")
    color_segment_folder = os.path.join(output_folder, f"{color[0]:02x}{color[1]:02x}{color[2]:02x}")
    os.makedirs(color_segment_folder, exist_ok=True)

    # Apply mask to alpha channel
    masked_image_data = np.copy(image_data)
    masked_image_data[:, :, 3] = np.where(mask, image_data[:, :, 3], 0)

    split_sprite(image_data=masked_image_data, output_folder=color_segment_folder, min_size=min_size, merge_distance=merge_distance, alpha_threshold=alpha_threshold)

def split_sprite_by_color(image_path, output_folder, min_size=100, merge_distance=2, alpha_threshold=0, number_of_colors=0, number_of_processes=multiprocessing.cpu_count()-2):
    """
    Splits an image into separate components based on color segments and saves each as a new image.

    Args:
        image_path (str): The path to the source image.
        output_folder (str): The directory where the split images will be saved.
        min_size (int, optional): The minimum pixel count for a component to be saved. Defaults to 100.
        merge_distance (int): Distance threshold to merge nearby components. Defaults to 2.
        alpha_threshold (int, optional): The alpha value threshold to consider a pixel as part of a component. Defaults to 0.
    """
    print(f"Loading an image from {image_path}\n")
    with Image.open(image_path) as image:
        if image.mode in ['P', 'L']:
            image = image.convert('RGBA')
        image_data = np.array(image)

    # Segment image by color
    segmented_masks = segment_image_by_color(image_data[:, :, :3], number_of_colors)

    # Parallel processing of each color segment
    with Pool(processes=number_of_processes) as pool:
        pool.starmap(process_color_segment, [(color, mask, output_folder, image_data, min_size, merge_distance, alpha_threshold) for color, mask in segmented_masks.items()])
    
    print("All color segments have been processed.")
