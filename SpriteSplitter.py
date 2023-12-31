import numpy as np
import os

from PIL import Image
from collections import deque
from scipy.spatial import KDTree



def distance_between_components(comp1, comp2):
    """
    Calculate the minimum distance between two components.

    Args:
        comp1, comp2 (list): Lists of (x, y) tuples representing the components.

    Returns:
        float: The minimum distance between the two components.
    """
    tree1 = KDTree(comp1)
    tree2 = KDTree(comp2)
    return tree1.query(tree2.data)[0].min()


def find_nearest_component(small_component, large_components):
    """
    Find the nearest large component to a given small component.

    Args:
        small_component (list): A list of (x, y) tuples representing the small component.
        large_components (list): A list of large components, each being a list of (x, y) tuples.

    Returns:
        int: The index of the nearest large component in 'large_components'.
    """
    min_distance = float('inf')
    nearest_index = -1

    for i, large_component in enumerate(large_components):
        distance = distance_between_components(small_component, large_component)
        if distance < min_distance:
            min_distance = distance
            nearest_index = i

    return nearest_index
    

def find_connected_component(img, start, visited, alpha_threshold):
    """
    Find a connected component starting from a given point 'start'.

    Args:
        img (np.ndarray): Image as a NumPy array where each element is a pixel.
        start (tuple): The (x, y) coordinates of the starting point to search for the component.
        visited (set): Set of already visited points (x, y) to avoid repeated processing.
        alpha_threshold (int): The alpha threshold value above which pixels are considered part of the component.

    Returns:
        list: A list of (x, y) coordinates of the pixels that make up the associated component.
    """

    # Use deque to work with the stack more efficiently
    stack = deque([start])
    component = []

    while stack:
        x, y = stack.pop()
        if (x, y) in visited:
            continue

        visited.add((x, y))
        component.append((x, y))
        

        # Check neighbor pixels
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < img.shape[1] and 0 <= ny < img.shape[0]:
                    if img[ny, nx, 3] > alpha_threshold:
                        stack.append((nx, ny))

    return component


def save_component_as_image(component, original_image_size, image_data, output_path):
    """
    Save the specified component of an image as a separate image file.

    Args:
        component (list of tuples): A list of pixel coordinates (x, y) that make up the component.
        original_image_size (tuple): The size (width, height) of the original image.
        image_data (numpy.ndarray): The pixel data of the original image as a NumPy array.
        output_path (str): The file path where the new image will be saved.
    """
    component_image = Image.new('RGBA', original_image_size, color=(0, 0, 0, 0))
    component_pixels = np.array(component_image)

    # Optimize pixel copying using NumPy
    for x, y in component:
        component_pixels[y, x] = (255, 255, 255, image_data[y, x][3]) if image_data[y, x][3] > 0 else image_data[y, x]
    
    # Saving a component to a file
    Image.fromarray(component_pixels).save(output_path)
    print(f"{output_path} saved")



def split_sprite(image_data, output_folder : str, min_size, merge_distance, alpha_threshold):
    """
    Splits an image into separate components (sprites) and saves each as a new image.

    Args:
        image_data (numpy.ndarray): The pixel data of the image's sprite as a NumPy array.
        output_folder (str): The directory where the split images will be saved.
        min_size (int, optional): The minimum pixel count for a component to be saved.
        merge_distance (int): Distance threshold to merge nearby components.
        alpha_threshold (int, optional): The alpha value threshold to consider a pixel as part of a component.
    """
 
    # Create a mask for pixels where the alpha channel is above the threshold
    alpha_mask = image_data[:,:,3] > alpha_threshold

    visited = set()
    large_components = []
    small_components = []

    for y in range(alpha_mask.shape[0]):
        for x in range(alpha_mask.shape[1]):
            if alpha_mask[y, x] and (x, y) not in visited:
                #print(f"Processing a component at position: {x}, {y}")
                component = find_connected_component(image_data, (x, y), visited, alpha_threshold)
                #info = f"Found component with size of {len(component)} pixels"
                if len(component) >= min_size:
                    large_components.append(component)
                    #print(f"{info} - large\n")
                else:
                    small_components.append(component)
                    #print(f"{info} - small\n")

    #print(f"Processing completed. Found {len(large_components)} large and {len(small_components)} small components")
    
    #if len(small_components) > 0:
    #    print("Merging small...")

    # Merge small components into nearest large components
    for small_component in small_components:
        nearest_index = find_nearest_component(small_component, large_components)
        if nearest_index != -1:
            large_components[nearest_index].extend(small_component)
        else:
            large_components.append(small_component)
            #print("There were no large components")

    # Merging close components
    i = 0
    while i < len(large_components):
        j = i + 1
        while j < len(large_components):
            if distance_between_components(large_components[i], large_components[j]) <= merge_distance:
                large_components[i].extend(large_components.pop(j))
            else:
                j += 1
        i += 1

    original_image_size = image_data.shape[:2]

    # Save each componet
    for i, (component) in enumerate(large_components, 1):
        output_path = os.path.join(output_folder, f'sprite_{i}.png')
        save_component_as_image(component, original_image_size, image_data, output_path)

    print(f"Processing completed\n")
    pass