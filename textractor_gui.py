import sys
import os
import time
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PyPDF2 import PdfReader, PdfWriter
# import docx
import openpyxl
from pptx import Presentation

SUPPORTED_DOC_TYPES = ('.pdf', '.ps', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf', '.odt', '.ods', '.odp')

class TextPredictionGUI:
    def __init__(self, tkroot, input_data):
        self.input_data = input_data
        self.root = tkroot
        self.root.title("Text Categorization")
        self.categories = []
        self.library = ""

        # Dictionary to track checkbox states
        self.check_states = {}

        # Initialize style for theme switching
        self.style = ttk.Style()

        self.data = {}
        self.get_data()

        # Create widgets
        self.create_widgets()

        # Bind the right click event
        self.bind_right_click()

    def get_data(self):
        with open(self.input_data, "r", encoding='utf-8') as f:
            self.data = json.load(f)


    def create_widgets(self):
        # Define UI layout
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill="both", expand=True)
        main_frame.columnconfigure(0, weight=1)

        # ===== Listbox for Supported File Suffixes =====
        self.suffixes_label = ttk.Label(main_frame, text="Supported File Suffixes:")
        self.suffixes_label.grid(row=0, column=0, sticky="w")

        self.suffixes_var = tk.StringVar(value=", ".join(SUPPORTED_DOC_TYPES))
        self.suffixes_entry = ttk.Entry(main_frame, textvariable=self.suffixes_var, width=50)
        self.suffixes_entry.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        # Add a button to switch themes
        self.theme_button = ttk.Button(main_frame, text="Switch Theme", command=self.switch_theme)
        self.theme_button.grid(row=1, column=2, padx=10, pady=10, sticky="ew")

        # ===== Select Directory for Training =====
        self.train_dir_label = ttk.Label(main_frame, text="Library:")
        self.train_dir_label.grid(row=2, column=0, sticky="w")

        self.train_dir_var = tk.StringVar()
        self.train_dir_entry = ttk.Entry(main_frame, textvariable=self.train_dir_var, state="readonly")
        self.train_dir_entry.grid(row=3, column=0, padx=10, pady=5, sticky="ew")

        self.train_dir_button = ttk.Button(main_frame, text="Select Folder", command=self.select_train_directory)
        self.train_dir_button.grid(row=3, column=1, padx=5)

        self.train_button = ttk.Button(main_frame, text="Train Model", command=self.train_model)
        self.train_button.grid(row=3, column=2, pady=10, sticky="w")

        # ===== Select Directory for Prediction =====
        self.pred_dir_label = ttk.Label(main_frame, text="New Docs:")
        self.pred_dir_label.grid(row=4, column=0, sticky="w")

        self.pred_dir_var = tk.StringVar()
        self.pred_dir_entry = ttk.Entry(main_frame, textvariable=self.pred_dir_var, width=50, state="readonly")
        self.pred_dir_entry.grid(row=5, column=0, padx=10, pady=5, sticky="ew")

        self.pred_dir_button = ttk.Button(main_frame, text="Select Folder", command=self.select_pred_directory)
        self.pred_dir_button.grid(row=5, column=1, padx=5)

        self.start_button = ttk.Button(main_frame, text="Categorize", command=self.start_process)
        self.start_button.grid(row=5, column=2, pady=10)

        # ===== Treeview with Unicode Checkboxes =====

        self.tree = ttk.Treeview(main_frame, columns=("Check", "Category", "File", "Text"), show="headings")
        self.tree.heading("Check", text="✓", anchor="center")
        self.tree.heading("Category", text="Category")
        self.tree.heading("File", text="File")
        self.tree.heading("Text", text="Sample Text")

        self.tree.column("Check", width=30, minwidth=30, stretch=tk.NO, anchor="center")
        self.tree.column("Category", width=100, minwidth=100, stretch=tk.NO)
        self.tree.column("File", width=150)
        self.tree.column("Text", width=300)

        self.insert_data()
        self.tree.bind("<Button-1>", self.on_checkbox_click)
        self.tree.grid(row=6, column=0, columnspan=3, pady=10, sticky="nsew")

        # Make the treeview widget expand with window resizing
        main_frame.rowconfigure(6, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)


        self.move_button = ttk.Button(main_frame, text="Apply Labels", command=self.label_files)
        self.move_button.grid(row=7, column=0, pady=10, sticky="w")

        self.quit_button = ttk.Button(main_frame, text="Quit", command=self.quit)
        self.quit_button.grid(row=7, column=2, pady=10)

    def insert_data(self):
        """ Insert rows into Treeview with Unicode checkboxes """

        for i, item in enumerate(self.data):
            self.check_states[i] = False  # Default unchecked
            checkbox_text = "☐"  # Empty checkbox
            self.tree.insert("", "end", iid=i, values=(checkbox_text, item["classifier"], item["id"], item["txt"]))

    def on_checkbox_click(self, event):
        """ Toggle checkboxes when clicked """
        col = self.tree.identify_column(event.x)
        row_id = self.tree.identify_row(event.y)
        if col == "#1" and row_id:
            row_id = int(row_id)
            self.check_states[row_id] = not self.check_states[row_id]
            new_checkbox = "✓" if self.check_states[row_id] else "☐"
            self.tree.item(row_id, values=(new_checkbox, *self.tree.item(row_id)["values"][1:]))

    def on_right_click(self, event):
        if not self.categories:
            messagebox.showerror("Error", "Please select a library directory")
            return

        row_id = self.tree.identify_row(event.y)
        if row_id:
            row_id = int(row_id)
            self.show_category_dialog(row_id)

    def show_category_dialog(self, row_id):
        """ Show a dialog to select category for the given row """
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Category")

        tk.Label(dialog, text="Select Category:").pack(pady=10)

        category_var = tk.StringVar(value=self.tree.item(row_id)["values"][1])
        category_menu = ttk.Combobox(dialog, textvariable=category_var, values=self.categories)
        category_menu.pack(pady=10)

        def on_select():
            new_category = category_var.get()
            self.tree.item(row_id, values=(self.tree.item(row_id)["values"][0], new_category, *self.tree.item(row_id)["values"][2:]))
            dialog.destroy()

        select_button = ttk.Button(dialog, text="Select", command=on_select)
        select_button.pack(pady=10)

        dialog.transient(self.root)
        time.sleep(0.1)  # Add a short delay
        dialog.grab_set()
        self.root.wait_window(dialog)

    def bind_right_click(self):
        """ Bind right click to show category dialog """
        self.tree.bind("<Button-3>", self.on_right_click)

    def select_train_directory(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.train_dir_var.set(folder_selected)
        self.library = folder_selected
        self.categories = [d for d in os.listdir(folder_selected) if os.path.isdir(os.path.join(folder_selected, d))]
        # sort the categories
        self.categories.sort()

    def select_pred_directory(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.pred_dir_var.set(folder_selected)

    def train_model(self):
        print("Training model on directory:", self.train_dir_var.get())

    def start_process(self):
        print("Starting process on directory:", self.pred_dir_var.get())

    def label_files(self):

        # show the list of selected files
        for i, checked in self.check_states.items():
            if checked:
                row_data = self.tree.item(i)['values']
                # Add exif tags to documents
                file_path = row_data[2]
                category = row_data[1]

                # Add exif tags to PDF and other document types
                if file_path.lower().endswith('.pdf'):

                    reader = PdfReader(file_path)
                    writer = PdfWriter()

                    # Get the existing metadata
                    metadata = reader.metadata

                    # Get the existing keywords
                    if '/Keywords' in metadata:
                        keywords = metadata['/Keywords'].split(', ')
                    else:
                        keywords = []

                    # Add the new keyword if it doesn't already exist
                    if category not in keywords:
                        keywords.append(category)

                    # Ensure the list of keywords is unique
                    keywords = list(set(keywords))

                    # Update the metadata with the new keywords
                    writer.add_metadata({
                        '/Keywords': ', '.join(keywords)
                    })

                    # Write the updated PDF to a new file
                    with open(file_path, 'wb') as f:
                        writer.write(f)


                elif file_path.lower().endswith(('.doc', '.docx')):
                    pass

                    # doc = docx.Document(file_path)
                    # core_properties = doc.core_properties
                    # core_properties.category = category
                    # doc.save(file_path)

                elif file_path.lower().endswith(('.xls', '.xlsx')):

                    wb = openpyxl.load_workbook(file_path)
                    wb.properties.category = category
                    wb.save(file_path)

                elif file_path.lower().endswith(('.ppt', '.pptx')):

                    prs = Presentation(file_path)
                    prs.core_properties.category = category
                    prs.save(file_path)

                elif file_path.lower().endswith('.txt'):
                    with open(file_path, 'a', encoding='utf-8') as txt_file:
                        txt_file.write(f"\nCategory: {category}")



    def switch_theme(self):
        current_theme = self.style.theme_use()
        if current_theme == "default":
            self.set_dark_theme()
        else:
            self.set_theme("default")

    def set_theme(self, theme_name):
        """ Set the theme for the application """
        self.style.theme_use(theme_name)

    def set_dark_theme(self):
        self.style.theme_create("dark", parent="alt", settings={
            "TLabel": {
                "configure": {"foreground": "#CCCCCC", "background": "#1F1F1F"}
            },
            "TButton": {
                "configure": {"foreground": "#CCCCCC", "background": "#1F1F1F"}
            },
            "TEntry": {
                "configure": {"foreground": "#CCCCCC", "background": "#1F1F1F"}
            },
            "Treeview": {
                "configure": {
                    "fieldbackground": "#1F1F1F",
                    "background": "#1F1F1F",
                    "foreground": "#CCCCCC"
                },
                "map": {
                    "background": [("selected", "#1F1F1F")],
                    "foreground": [("selected", "#CCCCCC")]
                }
            }
        })
        self.set_theme("dark")

    def quit(self):
        self.root.quit()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = TextPredictionGUI(root, sys.argv[1])
    root.mainloop()
