import tkinter as tk
import multiprocessing
import threading

from tkinter import filedialog
from ImageSplitter import split_sprite_by_color
from DataHandler import *


MAX_CORES = multiprocessing.cpu_count()


def run_splitter(image_path, output_folder, min_size, alpha_threshold, number_of_processes):
    # Clear last threads
    operation_completed.clear()
    
    # Run main script
    try:
        split_sprite_by_color(image_path, output_folder, min_size, alpha_threshold, number_of_processes)
    finally:
        operation_completed.set()

    #split_sprite_by_color(image_path, output_folder, min_size, alpha_threshold, number_of_processes)
    pass

def select_file():
    file_path = filedialog.askopenfilename()
    if file_path:
        entry_file_path.delete(0, tk.END)
        entry_file_path.insert(0, file_path)
        save_config({"last_file_path": file_path, "last_output_folder": entry_output_folder.get()})

def select_output_folder():
    folder_path = filedialog.askdirectory()
    if folder_path:
        entry_output_folder.delete(0, tk.END)
        entry_output_folder.insert(0, folder_path)
        save_config({"last_file_path": entry_file_path.get(), "last_output_folder": folder_path})


def start_processing():
    # Disable the start button to prevent multiple clicks
    start_button.config(state='disabled')
    status_label.config(text='Processing...')
    
    image_path = entry_file_path.get()
    output_folder = entry_output_folder.get()
    min_size = int(entry_min_size.get())
    alpha_threshold = int(entry_alpha_threshold.get())
    number_of_processes = int(entry_number_of_processes.get())
        
    # Ensuring number_of_processes does not exceed the available CPU cores
    if number_of_processes > MAX_CORES:
        number_of_processes = MAX_CORES

    operation_thread = threading.Thread(
        target=run_splitter, 
        args=(image_path, output_folder, min_size, alpha_threshold, number_of_processes)
    )
    operation_thread.start()

    # Check is thread is completed
    check_thread_completion()


def check_thread_completion():
    if operation_completed.is_set():
        # If process is completed, then update UI
        status_label.config(text='All processes have been completed.')
        start_button.config(state='normal')
    else:
        # Recheck after time
        root.after(100, check_thread_completion)


if __name__ == '__main__':
    # Run the Tkinter event loop
    root = tk.Tk()
    root.title("Image Splitter")

    # Habdle thread ending
    operation_completed = threading.Event()
    

    # Load saved configuration
    saved_config = load_config()
    default_file_path = saved_config.get('last_file_path', '')
    default_output_folder = saved_config.get('last_output_folder', '')

    # File path selection
    tk.Label(root, text="Image file:").grid(row=0, column=0, sticky=tk.W)
    entry_file_path = tk.Entry(root, width=50)
    entry_file_path.grid(row=0, column=1)
    entry_file_path.insert(0, default_file_path)
    tk.Button(root, text="Browse", command=select_file).grid(row=0, column=2)

    # Output folder selection
    tk.Label(root, text="Output folder:").grid(row=1, column=0, sticky=tk.W)
    entry_output_folder = tk.Entry(root, width=50)
    entry_output_folder.grid(row=1, column=1)
    entry_output_folder.insert(0, default_output_folder)
    tk.Button(root, text="Browse", command=select_output_folder).grid(row=1, column=2)

    # Label to the UI for status messages
    status_label = tk.Label(root, text='')
    status_label.grid(row=6, column=0, columnspan=3)

    # Parameters
    tk.Label(root, text="Min size:").grid(row=2, column=0, sticky=tk.W)
    entry_min_size = tk.Entry(root)
    entry_min_size.insert(0, "100")
    entry_min_size.grid(row=2, column=1)

    tk.Label(root, text="Alpha threshold:").grid(row=3, column=0, sticky=tk.W)
    entry_alpha_threshold = tk.Entry(root)
    entry_alpha_threshold.insert(0, "188")
    entry_alpha_threshold.grid(row=3, column=1)

    tk.Label(root, text="Number of processes: (Max " + str(MAX_CORES) + ")").grid(row=4, column=0, sticky=tk.W)
    entry_number_of_processes = tk.Entry(root)
    entry_number_of_processes.insert(0, str(MAX_CORES))
    entry_number_of_processes.grid(row=4, column=1)

    # Set the command for the button to start processing
    start_button = tk.Button(root, text="Start Processing", command=start_processing)
    start_button.grid(row=5, column=0, columnspan=3)

    # Start the Tkinter event loop
    root.mainloop()
