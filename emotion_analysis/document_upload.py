import os
import tkinter as tk
from tkinter import filedialog, Label, Button, Frame
from PIL import Image, ImageTk
import cv2

class DocumentUploadUI:
    def __init__(self, callback=None):
        """Create a document upload UI window"""
        self.callback = callback
        self.selected_file = None
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("Medical Document Upload")
        self.root.geometry("600x400")
        
        # Create main frame
        main_frame = Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create title
        title = Label(main_frame, text="Do you have any medical documents to upload?", 
                     font=("Arial", 16, "bold"))
        title.pack(pady=10)
        
        # Create instructions
        instructions = Label(main_frame, 
                            text="Uploading a medical document will help provide better context for this conversation.\n"
                                "Supported formats: PDF, JPG, PNG, TIFF",
                            font=("Arial", 11))
        instructions.pack(pady=10)
        
        # Create button frame
        button_frame = Frame(main_frame)
        button_frame.pack(pady=20)
        
        # Add upload button
        upload_btn = Button(button_frame, text="Select Document", 
                           command=self.browse_file, padx=10, pady=5,
                           bg="#4CAF50", fg="white", font=("Arial", 12))
        upload_btn.pack(side=tk.LEFT, padx=10)
        
        # Add skip button
        skip_btn = Button(button_frame, text="Skip Upload", 
                         command=self.skip_upload, padx=10, pady=5,
                         font=("Arial", 12))
        skip_btn.pack(side=tk.LEFT, padx=10)
        
        # File name display
        self.filename_label = Label(main_frame, text="No file selected", font=("Arial", 10))
        self.filename_label.pack(pady=10)
        
        # Preview frame
        self.preview_frame = Frame(main_frame)
        self.preview_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Run the window
        self.root.mainloop()
    
    def browse_file(self):
        """Open file dialog to select a document"""
        filetypes = [
            ("All supported files", "*.pdf;*.jpg;*.jpeg;*.png;*.tiff"),
            ("PDF files", "*.pdf"),
            ("Image files", "*.jpg;*.jpeg;*.png;*.tiff")
        ]
        
        filename = filedialog.askopenfilename(title="Select a document", 
                                             filetypes=filetypes)
        
        if filename:
            self.selected_file = filename
            self.filename_label.config(text=os.path.basename(filename))
            
            # Show preview if possible
            self.show_preview(filename)
            
            # Add submit button
            submit_btn = Button(self.preview_frame, text="Upload & Continue", 
                               command=self.submit, padx=10, pady=5,
                               bg="#2196F3", fg="white", font=("Arial", 12))
            submit_btn.pack(pady=10)
    
    def show_preview(self, filename):
        """Show a preview of the selected file"""
        # Clear previous preview
        for widget in self.preview_frame.winfo_children():
            widget.destroy()
        
        # Handle different file types
        ext = os.path.splitext(filename)[1].lower()
        
        if ext == '.pdf':
            preview_label = Label(self.preview_frame, text="PDF selected - Preview not available")
            preview_label.pack(pady=10)
        elif ext in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
            try:
                # Load and resize image for preview
                img = cv2.imread(filename)
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                height, width = img.shape[:2]
                
                # Calculate new size to fit in preview frame
                max_size = 200
                if height > width:
                    new_height = max_size
                    new_width = int(width * (max_size / height))
                else:
                    new_width = max_size
                    new_height = int(height * (max_size / width))
                
                img = cv2.resize(img, (new_width, new_height))
                
                # Convert to PhotoImage and display
                img = Image.fromarray(img)
                img = ImageTk.PhotoImage(img)
                
                panel = Label(self.preview_frame, image=img)
                panel.image = img  # Keep a reference to prevent garbage collection
                panel.pack(pady=10)
            except Exception as e:
                preview_label = Label(self.preview_frame, text=f"Error loading preview: {e}")
                preview_label.pack(pady=10)
    
    def submit(self):
        """Submit the selected file and close the window"""
        if self.callback and self.selected_file:
            self.callback(self.selected_file)
        self.root.destroy()
    
    def skip_upload(self):
        """Skip the upload process and close the window"""
        if self.callback:
            self.callback(None)
        self.root.destroy()