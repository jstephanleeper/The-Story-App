import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, simpledialog, Scale, HORIZONTAL, Toplevel
import tkinter.messagebox
import os
from PIL import Image, ImageTk

class StoryboardExtractor:
    def __init__(self, root):
        self.root = root
        self.root.title("The Story App - Storyboard Panel Extractor")
        self.root.geometry("1200x800")
        
        # Define theme colors
        self.BROWN = "#8B4513"
        self.LIGHT_BROWN = "#D2B48C"
        
        self.image_path = None
        self.original_image = None
        self.adjusted_image = None
        self.panels = []
        self.processed_panels = []
        
        # Variables for manual selection
        self.selection_mode = False
        self.current_points = []
        self.selection_image = None
        
        # Variables for image upscaling
        self.default_upscale_width = 7000  # New default upscale width
        self.upscale_width = self.default_upscale_width  # Current upscale width
        
        # Variable for panel resolution setting
        self.resolution_setting = tk.StringVar(value="1080 tall")  # Default resolution setting
        
        # Export settings with default values
        self.last_base_name = "panel_"
        self.last_export_dir = ""  # Initialize as empty string, not None
        self.export_numbering_mode = tk.StringVar(value="overwrite")
        self.remember_export_settings = tk.BooleanVar(value=False)
        self.use_custom_start_number = tk.BooleanVar(value=False)
        self.custom_start_number = tk.IntVar(value=1)
        
        # Remember last load directory
        self.last_load_dir = ""
        
        # Recent files list (limit to 10 files)
        self.recent_files = []
        self.max_recent_files = 10
        
        # Create UI with new styling
        self.create_ui()
        
    def create_ui(self):
        # Create header frame for logo and title
        header_frame = tk.Frame(self.root, bg="white")
        header_frame.pack(fill="x", padx=20, pady=10)
        
        # Logo handling
        logo_loaded = False
        
        # Check for logo in multiple possible locations
        possible_logo_paths = [
            "logo.png",                                      # Same directory
            os.path.join(os.path.dirname(__file__), "logo.png"),  # Script directory
            os.path.abspath("logo.png")                      # Absolute path
        ]
        
        logo_label = None
        
        print("Searching for logo file...")
        for path in possible_logo_paths:
            try:
                if os.path.exists(path):
                    print(f"Found logo at: {path}")
                    
                    # Load and resize logo
                    logo_img = Image.open(path)
                    logo_img = logo_img.resize((50, 50), Image.LANCZOS)
                    logo_tk = ImageTk.PhotoImage(logo_img)
                    
                    # Create and place the logo
                    logo_label = tk.Label(header_frame, image=logo_tk, bg="white")
                    logo_label.image = logo_tk  # Keep reference
                    logo_label.pack(side="left", padx=(0, 10))
                    
                    # Set window icon
                    self.root.iconphoto(True, logo_tk)
                    
                    logo_loaded = True
                    print("Logo loaded successfully")
                    break
            except Exception as e:
                print(f"Error loading logo from {path}: {e}")
        
        if not logo_loaded:
            print("No logo file found or loaded. Searched paths:")
            for path in possible_logo_paths:
                print(f"  - {path}")
                
        # App title
        title_label = tk.Label(
            header_frame, 
            text="The Story App - Storyboard Panel Extractor", 
            font=('Arial', 18, 'bold'), 
            fg=self.BROWN,
            bg="white"
        )
        title_label.pack(side="left")
        
        # Frame for buttons
        button_frame = tk.Frame(self.root, bg="white")
        button_frame.pack(pady=10)
        
        # Load Image button with recent files menu
        load_frame = tk.Frame(button_frame, bg="white")
        load_frame.pack(side=tk.LEFT, padx=5)
        
        load_button = tk.Button(
            load_frame, 
            text="1. Load Image", 
            command=self.load_image,
            bg=self.LIGHT_BROWN,
            fg="black",
            font=("Arial", 11, "bold"),
            padx=10,
            pady=5
        )
        load_button.pack()
        
        # Create a menu for recent files
        self.recent_menu = tk.Menu(self.root, tearoff=0)
        self.recent_menu.add_command(label="No recent files", state=tk.DISABLED)
        
        # Add right-click event to the load button
        load_button.bind("<Button-3>", self.show_recent_files_menu)
        
        # Other buttons
        adjust_button = tk.Button(
            button_frame, 
            text="2. Adjust Image", 
            command=self.show_adjust_panel,
            bg=self.LIGHT_BROWN,
            fg="black",
            font=("Arial", 11, "bold"),
            padx=10,
            pady=5
        )
        adjust_button.pack(side=tk.LEFT, padx=5)
        
        detect_button = tk.Button(
            button_frame, 
            text="3. Detect Panels", 
            command=self.detect_panels,
            bg=self.LIGHT_BROWN,
            fg="black",
            font=("Arial", 11, "bold"),
            padx=10,
            pady=5
        )
        detect_button.pack(side=tk.LEFT, padx=5)
        
        export_button = tk.Button(
            button_frame, 
            text="4. Convert & Export", 
            command=self.convert_and_export_panels,
            bg=self.LIGHT_BROWN,
            fg="black",
            font=("Arial", 11, "bold"),
            padx=10,
            pady=5
        )
        export_button.pack(side=tk.LEFT, padx=5)
        
        # Clear Image button (without number) at the end
        clear_button = tk.Button(
            button_frame, 
            text="Clear Image", 
            command=self.clear_image,
            bg="#ffcccc",
            fg="black",
            font=("Arial", 11, "bold"),
            padx=10,
            pady=5
        )
        clear_button.pack(side=tk.LEFT, padx=5)
        
        # Main display area with improved style
        self.display_frame = tk.Frame(self.root, bd=1, relief="solid", bg="white")
        self.display_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 20))
        
        # Image display label
        self.image_label = tk.Label(self.display_frame, bg="white", text="No image loaded")
        self.image_label.pack(fill=tk.BOTH, expand=True)
        
        # Panel preview frame (initially hidden)
        self.preview_frame = tk.Frame(self.root, bg="white")
        self.preview_frame.pack(fill=tk.X, pady=10, padx=10)
        self.preview_frame.pack_forget()  # Hide initially
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Load an image to begin")
        status_bar = tk.Label(
            self.root, 
            textvariable=self.status_var,
            bd=1,
            relief="sunken",
            anchor="w",
            padx=10,
            pady=5
        )
        status_bar.pack(side="bottom", fill="x")
    
    def show_recent_files_menu(self, event):
        """Show the recent files menu at the mouse position"""
        # Update the menu first
        self.recent_menu.delete(0, tk.END)
        
        if not self.recent_files:
            self.recent_menu.add_command(label="No recent files", state=tk.DISABLED)
        else:
            for i, path in enumerate(self.recent_files):
                # Display only the filename, not the full path
                filename = os.path.basename(path)
                # Create a lambda that captures the current path
                self.recent_menu.add_command(
                    label=f"{i+1}. {filename}", 
                    command=lambda p=path: self.load_specific_image(p)
                )
        
        # Add a separator and a clear list option
        if self.recent_files:
            self.recent_menu.add_separator()
            self.recent_menu.add_command(label="Clear Recent Files", command=self.clear_recent_files)
        
        # Show the menu at the mouse position
        try:
            self.recent_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.recent_menu.grab_release()
    
    def clear_recent_files(self):
        """Clear the recent files list"""
        self.recent_files = []
        self.status_var.set("Recent files list cleared")
    
    def add_to_recent_files(self, file_path):
        """Add a file to the recent files list"""
        if not file_path or not os.path.exists(file_path):
            return
            
        # Remove if already in the list to avoid duplicates
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
            
        # Add to the beginning of the list
        self.recent_files.insert(0, file_path)
        
        # Trim list if too long
        if len(self.recent_files) > self.max_recent_files:
            self.recent_files = self.recent_files[:self.max_recent_files]
    
    def load_specific_image(self, file_path):
        """Load a specific image from the recent files list"""
        if not file_path or not os.path.exists(file_path):
            self.status_var.set(f"File not found: {file_path}")
            # Remove from recent files if it doesn't exist
            if file_path in self.recent_files:
                self.recent_files.remove(file_path)
            return
            
        # Set the path and trigger the normal load process
        self.image_path = file_path
        
        try:
            # Load the image
            original_img = cv2.imread(self.image_path)
            if original_img is None:
                self.status_var.set("Failed to load image")
                return
                
            # Move to the top of recent files
            self.add_to_recent_files(file_path)
            
            # Prompt for upscale width
            self.prompt_upscale_width()
            
            # Continue with normal loading process
            height, width = original_img.shape[:2]
            new_height = int(height * (self.upscale_width / width))
            
            self.original_image = cv2.resize(
                original_img, 
                (self.upscale_width, new_height), 
                interpolation=cv2.INTER_CUBIC
            )
            
            self.adjusted_image = self.original_image.copy()
            self.panels = []
            self.processed_panels = []
            
            # Recreate display frame
            for widget in self.display_frame.winfo_children():
                try:
                    widget.destroy()
                except tk.TclError:
                    pass
                    
            self.image_label = tk.Label(self.display_frame, bg="white")
            self.image_label.pack(fill=tk.BOTH, expand=True)
            
            self.display_image(self.original_image)
            self.status_var.set(f"Loaded and upscaled image: {os.path.basename(self.image_path)}")
            
            # Hide panel preview frame if it was visible
            self.preview_frame.pack_forget()
            
        except Exception as e:
            print(f"Error loading specific image: {e}")
            self.status_var.set(f"Error loading image: {e}")
    
    def prompt_upscale_width(self):
        """Prompt the user to enter a custom upscale width with a reset option"""
        # Create a custom dialog
        dialog = Toplevel(self.root)
        dialog.title("Upscale Image")
        dialog.geometry("300x150")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()  # Make dialog modal
        
        # Add a label
        tk.Label(dialog, text="Enter upscale width in pixels:", pady=10).pack()
        
        # Entry field with default value
        width_var = tk.StringVar(value=str(self.upscale_width))
        entry = tk.Entry(dialog, textvariable=width_var, width=10)
        entry.pack(pady=5)
        entry.select_range(0, tk.END)
        entry.focus_set()
        
        # Result variable
        result = [self.upscale_width]  # Using a list to store the result
        
        # Button functions
        def on_ok():
            try:
                width = int(width_var.get())
                if width < 100:
                    tk.messagebox.showerror("Invalid Width", "Width must be at least 100 pixels.")
                    return
                result[0] = width
                dialog.destroy()
            except ValueError:
                tk.messagebox.showerror("Invalid Input", "Please enter a valid number.")
        
        def on_reset():
            width_var.set(str(self.default_upscale_width))
            entry.select_range(0, tk.END)
            entry.focus_set()
        
        def on_cancel():
            dialog.destroy()
        
        # Button frame
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)
        
        # Buttons with styled appearance
        tk.Button(button_frame, text="OK", command=on_ok, width=8, 
                 bg="#f0f0f0", fg="black", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Reset to Default", command=on_reset, width=15, 
                 bg="#f0f0f0", fg="black", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=on_cancel, width=8,
                 bg="#f0f0f0", fg="black", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        
        # Handle Enter key
        dialog.bind("<Return>", lambda event: on_ok())
        
        # Wait for dialog to close
        self.root.wait_window(dialog)
        
        # Set the upscale width
        self.upscale_width = result[0]
    
    def clear_image(self):
        """Completely clears the current image and resets the application state"""
        # Reset all variables
        self.image_path = None
        self.original_image = None
        self.adjusted_image = None
        self.panels = []
        self.processed_panels = []
        self.selection_image = None
        self.selection_mode = False
        
        # Clear any mouse bindings
        self.image_label.unbind("<Button-1>")
        
        # Remove any selection controls if present
        if hasattr(self, 'selection_frame') and self.selection_frame.winfo_exists():
            self.selection_frame.destroy()
        
        # Recreate the display frame to avoid Tkinter errors
        for widget in self.display_frame.winfo_children():
            try:
                widget.destroy()
            except tk.TclError:
                pass  # Ignore errors from already destroyed widgets
        
        # Create a new image label with no image
        self.image_label = tk.Label(self.display_frame, text="No image loaded", bg="white")
        self.image_label.pack(fill=tk.BOTH, expand=True)
        
        # Hide panel preview frame if it was visible
        self.preview_frame.pack_forget()
                
        # Update status
        self.status_var.set("Image cleared. Click 'Load Image' to begin.")
    
    def load_image(self):
        try:
            # Use the last load directory as the initial directory if available
            initial_dir = self.last_load_dir if self.last_load_dir else None
            
            self.image_path = filedialog.askopenfilename(
                title="Select Storyboard Image",
                filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")],
                initialdir=initial_dir
            )
            
            if not self.image_path:
                return
            
            # Remember the directory for next time - store only the directory path
            self.last_load_dir = os.path.dirname(self.image_path)
            print(f"Remembered last load directory: {self.last_load_dir}")
            
            # Add to recent files list
            self.add_to_recent_files(self.image_path)
                
            # Load the image
            original_img = cv2.imread(self.image_path)
            if original_img is None:
                self.status_var.set("Failed to load image")
                return
            
            # Prompt for upscale width
            self.prompt_upscale_width()
            
            # Upscale the image to the specified width
            height, width = original_img.shape[:2]
            new_height = int(height * (self.upscale_width / width))
            
            # Upscale using INTER_CUBIC for better quality
            self.original_image = cv2.resize(
                original_img, 
                (self.upscale_width, new_height), 
                interpolation=cv2.INTER_CUBIC
            )
            
            self.status_var.set(f"Image upscaled to {self.upscale_width}x{new_height}")
                
            self.adjusted_image = self.original_image.copy()
            
            # Clear any previous display state
            self.panels = []
            self.processed_panels = []
            
            # Recreate the display frame to avoid errors
            for widget in self.display_frame.winfo_children():
                try:
                    widget.destroy()
                except tk.TclError:
                    pass  # Ignore errors from already destroyed widgets
            
            # Create a new image label
            self.image_label = tk.Label(self.display_frame, bg="white")
            self.image_label.pack(fill=tk.BOTH, expand=True)
            
            # Hide panel preview frame if it was visible
            self.preview_frame.pack_forget()
            
            # Display the image
            self.display_image(self.original_image)
            self.status_var.set(f"Loaded and upscaled image: {os.path.basename(self.image_path)}")
        except Exception as e:
            print(f"Error during image loading: {e}")
            self.status_var.set("Error loading image. Please try again.")
    
    def display_image(self, img):
        try:
            # Convert BGR to RGB
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Get display frame dimensions
            frame_width = self.display_frame.winfo_width()
            frame_height = self.display_frame.winfo_height()
            
            if frame_width <= 1 or frame_height <= 1:  # Not yet realized
                frame_width, frame_height = 800, 600
            
            # Resize image to fit the frame
            img_height, img_width = rgb_img.shape[:2]
            scale = min(frame_width/img_width, frame_height/img_height)
            
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            resized_img = cv2.resize(rgb_img, (new_width, new_height))
            
            # Convert to PhotoImage
            pil_img = Image.fromarray(resized_img)
            tk_img = ImageTk.PhotoImage(pil_img)
            
            # Make sure label exists and is managed by Tkinter
            if hasattr(self, 'image_label') and self.image_label.winfo_exists():
                # Update label
                self.image_label.config(image=tk_img)
                self.image_label.image = tk_img  # Keep a reference
            else:
                # Recreate the label if it doesn't exist
                self.image_label = tk.Label(self.display_frame, bg="white")
                self.image_label.pack(fill=tk.BOTH, expand=True)
                self.image_label.config(image=tk_img)
                self.image_label.image = tk_img  # Keep a reference
        except Exception as e:
            print(f"Error displaying image: {e}")
            # Attempt recovery
            try:
                self.image_label = tk.Label(self.display_frame, bg="white")
                self.image_label.pack(fill=tk.BOTH, expand=True)
                self.status_var.set("Display error. Try resetting the image.")
            except:
                pass
    
    def show_adjust_panel(self):
        if self.original_image is None:
            self.status_var.set("Please load an image first")
            return
        
        # Create a simple adjustment window - now with more height
        adjust_window = Toplevel(self.root)
        adjust_window.title("Adjust Image")
        adjust_window.geometry("700x700")  # Increased height to fit all controls
        
        # Create frame for preview
        preview_frame = tk.Frame(adjust_window)
        preview_frame.pack(pady=10)
        
        # Create a label for the preview image
        preview_label = tk.Label(preview_frame)
        preview_label.pack()
        
        # Variables for sliders
        brightness_var = tk.IntVar(value=0)
        contrast_var = tk.DoubleVar(value=1.0)
        saturation_var = tk.DoubleVar(value=1.0)
        
        # Function to update preview
        def update_preview():
            # Get values
            brightness = brightness_var.get()
            contrast = contrast_var.get()
            saturation = saturation_var.get()
            
            # Create a copy to work with
            temp_img = self.original_image.copy()
            
            # Apply saturation
            hsv = cv2.cvtColor(temp_img, cv2.COLOR_BGR2HSV).astype(np.float32)
            hsv[:, :, 1] = hsv[:, :, 1] * saturation
            hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
            temp_img = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
            
            # Apply brightness and contrast
            temp_img = cv2.convertScaleAbs(temp_img, alpha=contrast, beta=brightness)
            
            # Convert to RGB for display
            rgb_img = cv2.cvtColor(temp_img, cv2.COLOR_BGR2RGB)
            
            # Resize for preview (smaller for the dialog)
            h, w = rgb_img.shape[:2]
            preview_width = 600
            preview_height = int(h * (preview_width / w))
            
            resized = cv2.resize(rgb_img, (preview_width, preview_height))
            
            # Convert to PhotoImage
            pil_img = Image.fromarray(resized)
            tk_img = ImageTk.PhotoImage(pil_img)
            
            # Update preview label
            preview_label.config(image=tk_img)
            preview_label.image = tk_img  # Keep reference
        
        # Sliders frame
        sliders_frame = tk.Frame(adjust_window)
        sliders_frame.pack(pady=10, fill=tk.X, padx=20)
        
        # Brightness slider
        tk.Label(sliders_frame, text="Brightness:").pack(anchor=tk.W)
        brightness_slider = Scale(sliders_frame, from_=-100, to=100, orient=HORIZONTAL, 
                    variable=brightness_var, length=600)
        brightness_slider.pack(fill=tk.X)
        brightness_slider.bind("<ButtonRelease-1>", lambda e: update_preview())
        
        # Contrast slider
        tk.Label(sliders_frame, text="Contrast:").pack(anchor=tk.W)
        contrast_slider = Scale(sliders_frame, from_=0.5, to=2.0, orient=HORIZONTAL, 
                    resolution=0.1, variable=contrast_var, length=600)
        contrast_slider.pack(fill=tk.X)
        contrast_slider.bind("<ButtonRelease-1>", lambda e: update_preview())
        
        # Saturation slider
        tk.Label(sliders_frame, text="Saturation:").pack(anchor=tk.W)
        saturation_slider = Scale(sliders_frame, from_=0.0, to=2.0, orient=HORIZONTAL, 
                    resolution=0.1, variable=saturation_var, length=600)
        saturation_slider.pack(fill=tk.X)
        saturation_slider.bind("<ButtonRelease-1>", lambda e: update_preview())
        
        # Buttons frame
        button_frame = tk.Frame(adjust_window)
        button_frame.pack(pady=20)
        
        # Apply button
        def apply_adjustments():
            # Get values
            brightness = brightness_var.get()
            contrast = contrast_var.get()
            saturation = saturation_var.get()
            
            # Apply adjustments to the main image
            temp_img = self.original_image.copy()
            
            # Apply saturation
            hsv = cv2.cvtColor(temp_img, cv2.COLOR_BGR2HSV).astype(np.float32)
            hsv[:, :, 1] = hsv[:, :, 1] * saturation
            hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
            temp_img = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
            
            # Apply brightness and contrast
            self.adjusted_image = cv2.convertScaleAbs(temp_img, alpha=contrast, beta=brightness)
            
            # Display the adjusted image in main window
            self.display_image(self.adjusted_image)
            self.status_var.set("Image adjusted. Proceed to detect panels.")
            adjust_window.destroy()
        
        # Reset button
        def reset_sliders():
            brightness_var.set(0)
            contrast_var.set(1.0)
            saturation_var.set(1.0)
            update_preview()
            
        # Add buttons with styling
        tk.Button(button_frame, text="Apply", command=apply_adjustments, width=10,
                 bg="#f0f0f0", fg="black", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Reset", command=reset_sliders, width=10,
                 bg="#f0f0f0", fg="black", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Cancel", command=adjust_window.destroy, width=10,
                 bg="#f0f0f0", fg="black", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=10)
        
        # Show initial preview
        update_preview()
    
    def detect_panels(self):
        if self.adjusted_image is None:
            self.status_var.set("Please load and adjust an image first")
            return
        
        # First, ensure we clean up any existing selection mode
        self.selection_mode = False
        self.image_label.unbind("<Button-1>")
        
        # Remove any existing selection controls before creating new ones
        if hasattr(self, 'selection_frame') and self.selection_frame.winfo_exists():
            self.selection_frame.destroy()
        
        # Clear previous panels
        self.panels = []
        self.current_points = []
        
        # Make a copy of the image for drawing
        self.selection_image = self.adjusted_image.copy()
        
        # Clear previous content and recreate display area
        for widget in self.display_frame.winfo_children():
            try:
                widget.destroy()
            except tk.TclError:
                pass
                
        # Create a new image label
        self.image_label = tk.Label(self.display_frame, bg="white")
        self.image_label.pack(fill=tk.BOTH, expand=True)
        
        # Display the image for selection
        self.display_image(self.selection_image)
        self.status_var.set("Preparing panel detection mode...")
        
        # Force the UI to update and stabilize
        self.root.update_idletasks()
        
        # Add panel management buttons
        self.add_selection_controls()
        
        # Give the UI time to render completely
        self.root.after(300)  # 300ms delay
        self.root.update()
        
        # Display the image again to ensure it's positioned correctly
        self.display_image(self.selection_image)
        
        # Another forced update and delay
        self.root.update_idletasks()
        self.root.after(200)  # 200ms delay
        self.root.update()
        
        # Now that the image is stable, enable selection mode
        self.selection_mode = True
        
        # Setup mouse callbacks
        self.image_label.bind("<Button-1>", self.on_click)
        self.image_label.bind("<Button-3>", lambda event: self.finish_selection())  # Right-click to finish selection
        
        # Add instructional text with emphasis on CLOCKWISE selection
        self.status_var.set("Click on corners CLOCKWISE to detect panel: top-left, top-right, bottom-right, bottom-left. Right-click when done.")
    
    def add_selection_controls(self):
        # Create a frame for panel selection controls with improved styling
        self.selection_frame = tk.Frame(self.root, bg=self.LIGHT_BROWN)
        self.selection_frame.pack(before=self.display_frame, fill=tk.X, padx=10, pady=5)
        
        # Instructions label with emphasis on CLOCKWISE selection
        instruction_label = tk.Label(
            self.selection_frame, 
            text="Click on corners CLOCKWISE to detect panel: top-left → top-right → bottom-right → bottom-left",
            font=("Arial", 10, "bold"),
            bg=self.LIGHT_BROWN,
            fg=self.BROWN
        )
        instruction_label.pack(pady=(5, 10))
        
        # Panel selection controls - left side
        buttons_frame = tk.Frame(self.selection_frame, bg=self.LIGHT_BROWN)
        buttons_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Add control buttons with styling
        tk.Button(
            buttons_frame, 
            text="Reset Current Selection", 
            command=self.reset_selection,
            bg="#f0f0f0",
            fg="black",
            font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            buttons_frame, 
            text="Delete Last Panel", 
            command=self.delete_last_panel,
            bg="#f0f0f0",
            fg="black",
            font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            buttons_frame, 
            text="Clear All Panels", 
            command=self.clear_all_panels,
            bg="#ffaaaa",
            fg="black",
            font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT, padx=5)
        
        # Removed "Finish Selection" button as requested
        
        # Resolution settings - right side
        resolution_frame = tk.Frame(self.selection_frame, bg=self.LIGHT_BROWN)
        resolution_frame.pack(side=tk.RIGHT, padx=10)
        
        tk.Label(resolution_frame, text="Resolution Setting:", 
                bg=self.LIGHT_BROWN, fg=self.BROWN).pack(side=tk.LEFT, padx=5)
        
        # Radio buttons for resolution options
        tk.Radiobutton(resolution_frame, text="1080 tall (Default/Pan)", 
                      variable=self.resolution_setting, value="1080 tall",
                      bg=self.LIGHT_BROWN).pack(side=tk.LEFT)
        
        tk.Radiobutton(resolution_frame, text="1920 wide (Crane)", 
                      variable=self.resolution_setting, value="1920 wide",
                      bg=self.LIGHT_BROWN).pack(side=tk.LEFT)
        
        tk.Radiobutton(resolution_frame, text="Custom", 
                      variable=self.resolution_setting, value="auto",
                      bg=self.LIGHT_BROWN).pack(side=tk.LEFT)
    
    def on_click(self, event):
        if not self.selection_mode:
            return
            
        # Get display frame dimensions
        frame_width = self.display_frame.winfo_width()
        frame_height = self.display_frame.winfo_height()
        
        # Get image dimensions
        img_height, img_width = self.adjusted_image.shape[:2]
        
        # Calculate scale
        scale = min(frame_width/img_width, frame_height/img_height)
        
        # Calculate offset if the image is centered
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        offset_x = (frame_width - new_width) // 2
        offset_y = (frame_height - new_height) // 2
        
        # Calculate actual position in original image
        x = int((event.x - offset_x) / scale)
        y = int((event.y - offset_y) / scale)
        
        # Ensure coordinates are within image bounds
        x = max(0, min(x, img_width - 1))
        y = max(0, min(y, img_height - 1))
        
        # Add the point to current selection
        self.current_points.append((x, y))
        
        # If we have 4 points, add a panel
        if len(self.current_points) == 4:
            self.add_panel()
        else:
            # Otherwise, just update the display
            self.draw_current_selection()
            
            # Update status message to guide the user with CLOCKWISE emphasis
            corner_names = ["top-left", "top-right", "bottom-right", "bottom-left"]
            next_corner = len(self.current_points)
            if next_corner < 4:
                self.status_var.set(f"Now click on the {corner_names[next_corner]} corner of the panel (CLOCKWISE selection)")
    
    def draw_current_selection(self):
        # Make a copy of the working image
        display_img = self.selection_image.copy()
        
        # Draw existing panels
        for i, panel in enumerate(self.panels):
            cv2.drawContours(display_img, [panel['box']], 0, (0, 255, 0), 2)
            x, y = panel['box'][0]
            # Use much larger font size (150% larger) and bolder
            cv2.putText(display_img, str(i+1), (x+10, y+40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 7.5, (0, 0, 255), 8)
        
        # Draw current points
        for i, point in enumerate(self.current_points):
            cv2.circle(display_img, point, 8, (0, 0, 255), -1)
            cv2.putText(display_img, str(i+1), (point[0]+15, point[1]+15), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 2)
        
        # Draw lines between points
        if len(self.current_points) >= 2:
            for i in range(len(self.current_points) - 1):
                cv2.line(display_img, self.current_points[i], self.current_points[i+1], 
                         (255, 0, 0), 2)
                
            # If 3 or more points, connect to form a polygon
            if len(self.current_points) >= 3:
                cv2.line(display_img, self.current_points[-1], self.current_points[0], 
                         (255, 0, 0), 2)
        
        # Display the updated image
        self.display_image(display_img)
    
    def add_panel(self):
        # Convert points to numpy array
        box = np.array(self.current_points, dtype=np.int32)
        
        # Add the panel
        self.panels.append({
            'box': box,
            'index': len(self.panels)
        })
        
        # Update the selection image with the new panel
        self.selection_image = self.adjusted_image.copy()
        for i, panel in enumerate(self.panels):
            cv2.drawContours(self.selection_image, [panel['box']], 0, (0, 255, 0), 2)
            x, y = panel['box'][0]
            # Use much larger font size (300% larger) and bolder
            cv2.putText(self.selection_image, str(i+1), (x+10, y+40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 7.5, (0, 0, 255), 8)
        
        # Reset current points
        self.current_points = []
        
        # Display the updated image
        self.display_image(self.selection_image)
        
        self.status_var.set(f"Panel {len(self.panels)} added. Click CLOCKWISE to define the next panel or click 'Finish Selection' when done.")
    
    def complete_panel(self):
        # Force complete the current panel if we have at least 3 points
        if len(self.current_points) >= 3:
            # If less than 4 points, duplicate the last point
            while len(self.current_points) < 4:
                self.current_points.append(self.current_points[-1])
                
            self.add_panel()
        else:
            self.status_var.set("Need at least 3 points to complete a panel.")
    
    def reset_selection(self):
        # Clear current points
        self.current_points = []
        
        # Redraw the image
        self.display_image(self.selection_image)
        
        self.status_var.set("Current selection reset. Click CLOCKWISE to start defining a new panel.")
    
    def clear_all_panels(self):
        """Clear all panel selections but keep the image loaded"""
        if not self.panels:
            self.status_var.set("No panels to clear.")
            return
            
        # Confirm with the user
        if not tk.messagebox.askyesno("Clear All Panels", 
                                    "Are you sure you want to clear all panels?"):
            return
            
        # Clear all panels
        self.panels = []
        self.current_points = []
        
        # Reset the selection image to the adjusted image
        self.selection_image = self.adjusted_image.copy()
        
        # Display the updated image
        self.display_image(self.selection_image)
        
        self.status_var.set("All panels cleared. Click CLOCKWISE to start defining new panels.")
    
    def delete_last_panel(self):
        if self.panels:
            # Remove the last panel
            self.panels.pop()
            
            # Update the selection image
            self.selection_image = self.adjusted_image.copy()
            for i, panel in enumerate(self.panels):
                cv2.drawContours(self.selection_image, [panel['box']], 0, (0, 255, 0), 2)
                x, y = panel['box'][0]
                # Use much larger font size (150% larger) and bolder
                cv2.putText(self.selection_image, str(i+1), (x+10, y+40), 
                           cv2.FONT_HERSHEY_SIMPLEX, 3.75, (0, 0, 255), 4)
            
            # Display the updated image
            self.display_image(self.selection_image)
            
            self.status_var.set(f"Last panel deleted. {len(self.panels)} panels remaining.")
    
    def finish_selection(self):
        # Complete the current panel if there are points
        if self.current_points:
            self.complete_panel()
        
        # End selection mode
        self.selection_mode = False
        
        # Remove the mouse callback
        self.image_label.unbind("<Button-1>")
        
        # Remove the selection controls
        if hasattr(self, 'selection_frame'):
            self.selection_frame.destroy()
        
        # Get the current resolution setting
        resolution_mode = self.resolution_setting.get()
        
        if self.panels:
            self.status_var.set(f"Selection complete. {len(self.panels)} panels defined with {resolution_mode} resolution. Click 'Convert & Export' to process.")
        else:
            self.status_var.set("No panels were defined. Click 'Detect Panels' to try again.")
    
    def update_panel_previews(self):
        """Create and display thumbnails of all panels"""
        # Clear previous thumbnails
        for widget in self.preview_frame.winfo_children():
            widget.destroy()
            
        # Skip if no processed panels
        if not self.processed_panels:
            self.preview_frame.pack_forget()
            return
            
        # Configure the preview frame with styling
        self.preview_frame.pack(fill=tk.X, pady=10, after=self.display_frame)
        self.preview_frame.configure(bg="white", bd=1, relief="solid")
        
        # Create a label for the previews section
        tk.Label(
            self.preview_frame, 
            text="Panel Previews:", 
            font=("Arial", 12, "bold"),
            bg="white",
            fg=self.BROWN
        ).pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        # Create a frame for the thumbnails
        thumbs_frame = tk.Frame(self.preview_frame, bg="white")
        thumbs_frame.pack(fill=tk.X, pady=5, padx=10)
        
        # Calculate thumbnail size (max 120px height)
        max_height = 120
        
        # Create thumbnails for each panel
        for i, panel in enumerate(self.processed_panels):
            # Create frame for this thumbnail
            thumb_frame = tk.Frame(
                thumbs_frame, 
                bd=2, 
                relief=tk.GROOVE, 
                padx=5, 
                pady=5,
                bg=self.LIGHT_BROWN
            )
            thumb_frame.pack(side=tk.LEFT, padx=5, pady=5)
            
            # Calculate thumbnail size
            h, w = panel.shape[:2]
            scale = max_height / h
            thumb_width = int(w * scale)
            thumb_height = max_height
            
            # Resize to thumbnail size
            thumb = cv2.resize(panel, (thumb_width, thumb_height))
            
            # Convert to tkinter image
            rgb_thumb = cv2.cvtColor(thumb, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_thumb)
            tk_img = ImageTk.PhotoImage(pil_img)
            
            # Create image label
            img_label = tk.Label(thumb_frame, image=tk_img)
            img_label.image = tk_img  # Keep reference
            img_label.pack()
            
            # Add panel number label with styling
            tk.Label(
                thumb_frame, 
                text=f"Panel {i+1}",
                bg=self.LIGHT_BROWN,
                fg=self.BROWN,
                font=("Arial", 9, "bold")
            ).pack()
            
            # Store the index to use in the event handler
            img_label.panel_index = i
            
            # Add click event to highlight corresponding panel in main view
            img_label.bind("<Button-1>", self.highlight_panel)
    
    def highlight_panel(self, event):
        """Highlight the selected panel in the main view"""
        # Get the panel index from the clicked label
        panel_index = event.widget.panel_index
        
        if panel_index < len(self.panels):
            # Create a copy of the adjusted image for highlighting
            display_img = self.adjusted_image.copy()
            
            # Draw all panels
            for i, panel in enumerate(self.panels):
                # Determine color - highlighted panel in red, others in green
                color = (0, 0, 255) if i == panel_index else (0, 255, 0)
                thickness = 8 if i == panel_index else 4
                
                cv2.drawContours(display_img, [panel['box']], 0, color, thickness)
                x, y = panel['box'][0]
                cv2.putText(display_img, str(i+1), (x+10, y+40), 
                           cv2.FONT_HERSHEY_SIMPLEX, 7.5, color, 8)
            
            # Display the image with highlighted panel
            self.display_image(display_img)
            self.status_var.set(f"Panel {panel_index+1} highlighted")
    
    def show_export_dialog(self):
        """Show an enhanced export dialog with additional options"""
        if not self.panels:
            self.status_var.set("Please detect panels first")
            return None, None, None, 1
        
        # Create dialog with styling
        dialog = Toplevel(self.root)
        dialog.title("Export Panels")
        dialog.geometry("500x400")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()  # Make dialog modal
        
        # Debug print to check current values
        print(f"Current settings: base_name={self.last_base_name}, export_dir={self.last_export_dir}")
        
        # Use the directory of the original image as default if no last export directory
        if not self.last_export_dir and self.image_path:
            self.last_export_dir = os.path.dirname(self.image_path)
            print(f"Using image path as default for export: {self.last_export_dir}")
            
        # Make sure export dir is a string
        if self.last_export_dir is None:
            self.last_export_dir = ""
        
        # Results storage
        result = {
            "base_name": self.last_base_name,
            "directory": self.last_export_dir,
            "numbering_mode": self.export_numbering_mode.get(),
            "use_custom_start": self.use_custom_start_number.get(),
            "start_number": self.custom_start_number.get(),
            "proceed": False
        }
        
        # Main frame with styling
        main_frame = tk.Frame(dialog, padx=20, pady=20, bg=self.LIGHT_BROWN)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title label
        tk.Label(
            main_frame, 
            text="Export Panel Settings",
            font=("Arial", 12, "bold"),
            bg=self.LIGHT_BROWN,
            fg=self.BROWN
        ).pack(pady=(0, 15))
        
        # Base name section
        name_frame = tk.Frame(main_frame, bg=self.LIGHT_BROWN)
        name_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(name_frame, text="Base name for files:", width=18, anchor=tk.W,
               bg=self.LIGHT_BROWN, fg=self.BROWN).pack(side=tk.LEFT)
        
        name_var = tk.StringVar(value=self.last_base_name)
        name_entry = tk.Entry(name_frame, textvariable=name_var, width=30)
        name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        name_entry.select_range(0, tk.END)
        name_entry.focus_set()
        
        # Directory section
        dir_frame = tk.Frame(main_frame, bg=self.LIGHT_BROWN)
        dir_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(dir_frame, text="Save to directory:", width=18, anchor=tk.W,
               bg=self.LIGHT_BROWN, fg=self.BROWN).pack(side=tk.LEFT)
        
        dir_var = tk.StringVar(value=self.last_export_dir)
        dir_entry = tk.Entry(dir_frame, textvariable=dir_var, width=30)
        dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        def browse_directory():
            directory = filedialog.askdirectory(
                title="Select Directory to Save Panels", 
                initialdir=dir_var.get() if dir_var.get() else None
            )
            if directory:
                dir_var.set(directory)
        
        tk.Button(dir_frame, text="Browse...", command=browse_directory,
                 bg=self.BROWN, fg="white").pack(side=tk.LEFT)
        
        # Custom start number section with checkbox to enable/disable
        start_num_frame = tk.Frame(main_frame, bg=self.LIGHT_BROWN)
        start_num_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Spinbox container that will be shown/hidden
        start_num_container = tk.Frame(start_num_frame, bg=self.LIGHT_BROWN)
        
        # Checkbox to enable custom start number
        def toggle_custom_start():
            if self.use_custom_start_number.get():
                start_num_container.pack(side=tk.LEFT)
            else:
                start_num_container.pack_forget()
                
        custom_start_cb = tk.Checkbutton(
            start_num_frame, 
            text="Custom start number:", 
            variable=self.use_custom_start_number,
            command=toggle_custom_start,
            anchor=tk.W,
            bg=self.LIGHT_BROWN,
            fg=self.BROWN
        )
        custom_start_cb.pack(side=tk.LEFT, padx=(0, 5))
        
        # Spinbox for the custom start number
        tk.Spinbox(
            start_num_container, 
            from_=1, 
            to=999, 
            textvariable=self.custom_start_number, 
            width=6
        ).pack(side=tk.LEFT)
        
        # Initialize visibility based on current setting
        if self.use_custom_start_number.get():
            start_num_container.pack(side=tk.LEFT)
        
        # Numbering options
        numbering_frame = tk.Frame(main_frame, bg=self.LIGHT_BROWN)
        numbering_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(numbering_frame, text="Numbering mode:", width=18, anchor=tk.W,
               bg=self.LIGHT_BROWN, fg=self.BROWN).pack(side=tk.LEFT)
        
        # Radio buttons for numbering options
        tk.Radiobutton(numbering_frame, text="Overwrite/Replace", 
                      variable=self.export_numbering_mode, value="overwrite",
                      bg=self.LIGHT_BROWN).pack(side=tk.LEFT, padx=(0, 10))
        tk.Radiobutton(numbering_frame, text="Continue Sequence", 
                      variable=self.export_numbering_mode, value="continue",
                      bg=self.LIGHT_BROWN).pack(side=tk.LEFT)
        
        # Remember settings checkbox with default value from previous state
        remember_frame = tk.Frame(main_frame, bg=self.LIGHT_BROWN)
        remember_frame.pack(fill=tk.X, pady=(0, 20))
        
        remember_cb = tk.Checkbutton(
            remember_frame, 
            text="Remember these settings", 
            variable=self.remember_export_settings,
            bg=self.LIGHT_BROWN
        )
        remember_cb.pack(side=tk.LEFT)
        
        # Make sure the checkbox reflects the current variable state
        if self.remember_export_settings.get():
            remember_cb.select()
        else:
            remember_cb.deselect()
        
        # Status and info
        status_text = f"Ready to export {len(self.panels)} panels.\nResolution: {self.resolution_setting.get()}"
        tk.Label(main_frame, text=status_text, justify=tk.LEFT,
               bg=self.LIGHT_BROWN, fg=self.BROWN).pack(fill=tk.X, pady=(0, 15))
        
        # Button functions
        def on_run():
            # Get the values from the dialog
            base_name_value = name_var.get()
            directory_value = dir_var.get()
            numbering_mode_value = self.export_numbering_mode.get()
            use_custom_start = self.use_custom_start_number.get()
            start_number_value = self.custom_start_number.get() if use_custom_start else 1
            
            # Validate values
            if not base_name_value.strip():
                tk.messagebox.showerror("Invalid Name", "Please enter a base name for files.")
                return
                
            if not directory_value.strip() or not os.path.isdir(directory_value):
                tk.messagebox.showerror("Invalid Directory", "Please select a valid directory.")
                return
            
            # Save values to result
            result["base_name"] = base_name_value
            result["directory"] = directory_value
            result["numbering_mode"] = numbering_mode_value
            result["use_custom_start"] = use_custom_start
            result["start_number"] = start_number_value
            result["proceed"] = True
            
            # Save settings if remember is checked
            if self.remember_export_settings.get():
                self.last_base_name = base_name_value
                self.last_export_dir = directory_value
                # Print debug info to confirm values are saved
                print(f"Saving settings: base_name={self.last_base_name}, dir={self.last_export_dir}")
            
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        # Button frame
        button_frame = tk.Frame(main_frame, bg=self.LIGHT_BROWN)
        button_frame.pack(fill=tk.X)
        
        tk.Button(button_frame, text="Run", command=on_run, width=10, 
                 bg="#ccffcc", fg="black", font=("Arial", 11, "bold")).pack(side=tk.RIGHT, padx=(5, 0))
        tk.Button(button_frame, text="Cancel", command=on_cancel, width=10,
                 bg="#f0f0f0", fg="black", font=("Arial", 11)).pack(side=tk.RIGHT)
        
        # Handle Enter key
        dialog.bind("<Return>", lambda event: on_run())
        dialog.bind("<Escape>", lambda event: on_cancel())
        
        # Wait for dialog to close
        self.root.wait_window(dialog)
        
        if result["proceed"]:
            return (result["base_name"], result["directory"], 
                   result["numbering_mode"], result["start_number"])
        else:
            return None, None, None, 1
            
    def convert_and_export_panels(self):
        """Combined function to convert panels and export them in one step"""
        if not self.panels:
            self.status_var.set("Please detect panels first")
            return
            
        # First finish the selection process (previously done by "Finish Selection" button)
        # Complete the current panel if there are points
        if self.selection_mode and self.current_points:
            self.complete_panel()
        
        # End selection mode
        self.selection_mode = False
        
        # Remove the mouse callback
        self.image_label.unbind("<Button-1>")
        
        # Remove the selection controls
        if hasattr(self, 'selection_frame') and self.selection_frame.winfo_exists():
            self.selection_frame.destroy()
        
        # Process panels first (converting them to perfect rectangles)
        self.status_var.set("Converting panels to perfect rectangles...")
        self.root.update_idletasks()  # Update UI to show status
        
        # Process all panels
        self.processed_panels = []
        
        for panel in self.panels:
            # Get the four corners
            src_points = panel['box'].astype(np.float32)
            
            # Sort corners: top-left, top-right, bottom-right, bottom-left
            def sort_corners(pts):
                # Calculate center
                center = np.mean(pts, axis=0)
                
                # Function to calculate angle from center
                def get_angle(point):
                    return np.arctan2(point[1] - center[1], point[0] - center[0])
                
                # Sort corners by angle
                sorted_pts = sorted(pts, key=lambda p: get_angle(p))
                
                # Rearrange to start from top-left (smallest sum of coords)
                top_left_idx = np.argmin([p[0] + p[1] for p in sorted_pts])
                sorted_pts = np.roll(sorted_pts, -top_left_idx, axis=0)
                
                return sorted_pts
            
            src_points = sort_corners(src_points)
            
            # Calculate width and height while maintaining the original panel dimensions
            # Calculate average width and height from the source points
            width = int((np.linalg.norm(src_points[1] - src_points[0]) + 
                         np.linalg.norm(src_points[3] - src_points[2])) / 2)
            height = int((np.linalg.norm(src_points[2] - src_points[1]) + 
                          np.linalg.norm(src_points[0] - src_points[3])) / 2)
            
            # Round height up to the nearest 100 pixels
            height = int(np.ceil(height / 100.0) * 100)
            
            # Define destination points for a perfect rectangle
            dst_points = np.array([
                [0, 0],               # top-left
                [width-1, 0],         # top-right
                [width-1, height-1],  # bottom-right
                [0, height-1]         # bottom-left
            ], dtype=np.float32)
            
            # Calculate perspective transform
            M = cv2.getPerspectiveTransform(src_points, dst_points)
            
            # Apply transform to create perfect rectangle while maintaining resolution
            warped = cv2.warpPerspective(self.adjusted_image, M, (width, height))
            
            # Apply resolution setting if needed
            resolution_mode = self.resolution_setting.get()
            if resolution_mode != "auto":
                panel_height, panel_width = warped.shape[:2]
                
                if resolution_mode == "1080 tall":
                    # Scale to 1080px height
                    scale_factor = 1080 / panel_height
                    new_width = int(panel_width * scale_factor)
                    warped = cv2.resize(warped, (new_width, 1080), interpolation=cv2.INTER_CUBIC)
                    
                elif resolution_mode == "1920 wide":
                    # Scale to 1920px width
                    scale_factor = 1920 / panel_width
                    new_height = int(panel_height * scale_factor)
                    warped = cv2.resize(warped, (1920, new_height), interpolation=cv2.INTER_CUBIC)
            
            # Store processed panel
            self.processed_panels.append(warped)
        
        # Update panel previews
        self.update_panel_previews()
        
        # Show enhanced export dialog
        base_name, directory, numbering_mode, start_number = self.show_export_dialog()
        
        if not base_name or not directory:
            self.status_var.set("Export cancelled.")
            return
        
        # Export panels
        self.status_var.set("Exporting panels...")
        self.root.update_idletasks()  # Update UI to show status
        
        # Use the explicit start number from the dialog if in overwrite mode
        # For continue mode, find the highest existing number
        if numbering_mode == "overwrite":
            start_number = start_number  # Use the value from the dialog
        else:  # continue mode
            # Get all files matching the base name pattern
            existing_files = [f for f in os.listdir(directory) 
                             if f.startswith(base_name) and f.endswith(".jpg")]
            
            # Extract numbers from existing files
            existing_numbers = []
            for filename in existing_files:
                # Try to extract number from filename (e.g., panel_001.jpg -> 1)
                number_part = filename[len(base_name):-4]  # Remove base_name and .jpg
                try:
                    existing_numbers.append(int(number_part))
                except ValueError:
                    # If conversion fails, just skip this file
                    pass
            
            # Set start number to one more than the highest existing number
            if existing_numbers:
                start_number = max(existing_numbers) + 1
            # Otherwise use the value from the dialog
        
        for i, panel in enumerate(self.processed_panels):
            # Format filename with padded number (starting from the determined number)
            panel_number = start_number + i
            filename = f"{base_name}{panel_number:03d}.jpg"
            filepath = os.path.join(directory, filename)
            
            # Save the image
            cv2.imwrite(filepath, panel, [cv2.IMWRITE_JPEG_QUALITY, 95])
        
        end_number = start_number + len(self.processed_panels) - 1
        
        # Get current resolution setting
        resolution_mode = self.resolution_setting.get()
        
        # Update status message with export details and resolution
        if numbering_mode == "continue":
            self.status_var.set(f"Exported {len(self.processed_panels)} panels to {directory} with {resolution_mode} resolution (panels {start_number:03d}-{end_number:03d})")
        else:
            self.status_var.set(f"Exported {len(self.processed_panels)} panels to {directory} with {resolution_mode} resolution")
        
        # Display the original image with panel outlines to show we're done
        display_img = self.adjusted_image.copy()
        for i, panel in enumerate(self.panels):
            cv2.drawContours(display_img, [panel['box']], 0, (0, 255, 0), 2)
            x, y = panel['box'][0]
            cv2.putText(display_img, str(i+1), (x+10, y+40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 3.75, (0, 0, 255), 4)
                       
        self.display_image(display_img)

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = StoryboardExtractor(root)
    
    # Print working directory info for logo debugging
    print(f"Current working directory: {os.getcwd()}")
    
    # Start the application
    root.mainloop()
