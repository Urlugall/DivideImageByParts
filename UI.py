import tkinter as tk
import multiprocessing
import threading
import logging

from tkinter import filedialog
from ImageSplitter import split_sprite_by_color
from DataHandler import *


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MAX_CORES = multiprocessing.cpu_count()


class ImageSplitterApp:
    def __init__(self, root):
        self.root = root
        root.title("Image Splitter")
        self.load_config()  # Load the config before creating widgets
        self.create_widgets()

    def create_widgets(self):
        # File path selection
        tk.Label(self.root, text="Image file:").grid(row=0, column=0, sticky=tk.W)
        self.entry_file_path = tk.Entry(self.root, width=50)
        self.entry_file_path.grid(row=0, column=1)
        self.entry_file_path.insert(0, self.default_file_path)
        self.input_browse_button = tk.Button(self.root, text="Browse", command=self.select_file)
        self.input_browse_button.grid(row=0, column=2)

        # Output folder selection
        tk.Label(root, text="Output folder:").grid(row=1, column=0, sticky=tk.W)
        self.entry_output_folder = tk.Entry(root, width=50)
        self.entry_output_folder.grid(row=1, column=1)
        self.entry_output_folder.insert(0, self.default_output_folder)
        self.output_browse_button = tk.Button(root, text="Browse", command=self.select_output_folder)
        self.output_browse_button.grid(row=1, column=2)

        # Parameters
        tk.Label(root, text="Min size of piece:").grid(row=2, column=0, sticky=tk.W)
        self.entry_min_size = tk.Entry(root)
        self.entry_min_size.insert(0, "100")
        self.entry_min_size.grid(row=2, column=1)

        tk.Label(root, text="Distance to merge adjacent pices:").grid(row=3, column=0, sticky=tk.W)
        self.entry_merge_distance = tk.Entry(root)
        self.entry_merge_distance.insert(0, "2")
        self.entry_merge_distance.grid(row=3, column=1)

        tk.Label(root, text="Alpha threshold:").grid(row=4, column=0, sticky=tk.W)
        self.entry_alpha_threshold = tk.Entry(root)
        self.entry_alpha_threshold.insert(0, "188")
        self.entry_alpha_threshold.grid(row=4, column=1)

        tk.Label(root, text="Number of image's colors (0 - autodetect):").grid(row=5, column=0, sticky=tk.W)
        self.entry_number_of_colors = tk.Entry(root)
        self.entry_number_of_colors.insert(0, "0")
        self.entry_number_of_colors.grid(row=5, column=1)

        tk.Label(root, text="Number of processes: (Max " + str(MAX_CORES) + ")").grid(row=6, column=0, sticky=tk.W)
        self.entry_number_of_processes = tk.Entry(root)
        self.entry_number_of_processes.insert(0, str(MAX_CORES-2))
        self.entry_number_of_processes.grid(row=6, column=1)

        # Set the command for the button to start processing
        self.start_button = tk.Button(root, text="Start Processing", command=self.start_processing)
        self.start_button.grid(row=7, column=0, columnspan=3)

        # Label to the UI for status messages
        self.status_label = tk.Label(root, text='')
        self.status_label.grid(row=8, column=0, columnspan=3)

    def load_config(self):
        # Load saved configuration
        saved_config = load_config()
        self.default_file_path = saved_config.get('last_file_path', '')
        self.default_output_folder = saved_config.get('last_output_folder', '')

    def select_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.entry_file_path.delete(0, tk.END)
            self.entry_file_path.insert(0, file_path)
            save_config({"last_file_path": file_path, "last_output_folder": self.entry_output_folder.get()})

    def select_output_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.entry_output_folder.delete(0, tk.END)
            self.entry_output_folder.insert(0, folder_path)
            save_config({"last_file_path": self.entry_file_path.get(), "last_output_folder": folder_path})


    def start_processing(self):
        # Disable the start button to prevent multiple clicks
        self.start_button.config(state='disabled')
        self.input_browse_button.config(state='disabled')
        self.output_browse_button.config(state='disabled')
        self.status_label.config(text='Processing...')

        image_path = self.entry_file_path.get()
        output_folder = self.entry_output_folder.get()
        min_size = int(self.entry_min_size.get())
        merge_distance = int(self.entry_merge_distance.get())
        alpha_threshold = int(self.entry_alpha_threshold.get())
        number_of_colors = int(self.entry_number_of_colors.get())
        number_of_processes = int(self.entry_number_of_processes.get())

        # Ensuring number_of_processes does not exceed the available CPU cores
        if number_of_processes > MAX_CORES:
            number_of_processes = MAX_CORES

        operation_thread = threading.Thread(
            target=self.run_splitter,
            args=(image_path, output_folder, min_size, merge_distance, alpha_threshold, number_of_colors, number_of_processes)
        )
        operation_thread.start()

    def run_splitter(self, image_path, output_folder, min_size, merge_distance, alpha_threshold, number_of_colors, number_of_processes):
        try:
            split_sprite_by_color(image_path, output_folder, min_size, merge_distance, alpha_threshold, number_of_colors, number_of_processes)
        except Exception as e:
            logging.error(f"Error during splitting: {e}")
        finally:
            self.root.after(0, self.on_splitter_finish)


    def on_splitter_finish(self):
        # When all processes were completed
        self.status_label.config(text='All processes have been completed.')
        self.start_button.config(state='normal')
        self.input_browse_button.config(state='normal')
        self.output_browse_button.config(state='normal')




if __name__ == '__main__':
    root = tk.Tk()
    app = ImageSplitterApp(root)
    # Start the Tkinter event loop
    root.mainloop()