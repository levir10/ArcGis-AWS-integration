import arcpy
import tkinter as tk
from PIL import Image
import customtkinter as ctk
from tkinter import messagebox
import os
import threading
import boto3
from botocore.exceptions import BotoCoreError, NoCredentialsError
import subprocess
import logging

# Configure logging to log messages to a file
log_path = os.path.join(os.path.dirname(__file__), "log.txt")
logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class Toolbox:
    def __init__(self):
        # Define the toolbox label, alias, and tools it contains
        self.label = "Toolbox"
        self.alias = "toolbox"
        self.tools = [Tool]

class Tool:
    def __init__(self):
        # Define the tool label and description
        self.label = "Tool"
        self.description = ""

    def getParameterInfo(self):
        # Define the input parameters for the tool
        text_param = arcpy.Parameter(
            displayName="Enter a name",  # Label for the parameter
            name="name",  # Internal name
            datatype="GPString",  # Data type
            parameterType="Required",  # Required input
            direction="Input"  # Input parameter
        )

        dropdown_param = arcpy.Parameter(
            displayName="Choose an option",  # Label for the parameter
            name="dropdown",  # Internal name
            datatype="GPString",  # Data type
            parameterType="Required",  # Required input
            direction="Input"  # Input parameter
        )
        # Define a list of options for the dropdown
        dropdown_param.filter.type = "ValueList"
        dropdown_param.filter.list = ["Option A", "Option B", "Option C"]
        dropdown_param.value = "Option A"  # Default value

        return [text_param, dropdown_param]

    def isLicensed(self):
        # Indicate that the tool is licensed to run
        return True

    def updateParameters(self, parameters):
        # Placeholder for updating parameters dynamically
        return

    def updateMessages(self, parameters):
        # Placeholder for updating messages dynamically
        return

    def execute(self, parameters, messages):
        # Log the start of execution and launch the GUI in a separate thread
        logging.info("Execution started.")
        threading.Thread(target=self.launch_gui, daemon=True).start()

    def launch_gui(self):
        """Launch the main GUI application."""
        logging.info("Launching GUI.")
        # Set the appearance and theme for the customtkinter GUI
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")#set the color theme to dark-blue

        # Create the main application window
        root = ctk.CTk()
        root.title("Exodigo ArcGis Integrator")
        root.geometry("400x300")
        root.resizable(True, True)
        # Set custom window icon
        root.wm_iconbitmap("exodigo-logo-32x32.ico") 
        # Add a label to the GUI
        label = ctk.CTkLabel(root, text="Select an option:", font=ctk.CTkFont(size=16, weight="bold"))
        label.pack(pady=15)
        
        # Create a dropdown menu with a default "Loading..." value
        dropdown_var = ctk.StringVar(value="Loading...")# Set default value
        dropdown = ctk.CTkOptionMenu(root, variable=dropdown_var, values=["Loading..."])#the dropdown object
        dropdown.pack(pady=10)

        # Add a login button to the GUI
        # Load the image (make sure the path is correct and file exists)
        image_path = "exodigo-logo-32x32.png"
        image = ctk.CTkImage(light_image=Image.open(image_path), size=(32, 32))
        # Add a login button with image
        login_button = ctk.CTkButton(
            root,
            text="Exodigo Login",
            image=image,
            compound="left",  # Image to the left of the text; use "top", "right", "bottom" as needed
            corner_radius=30,
            fg_color="#1f6aa5",
            hover_color="#144870"
        )
        login_button.pack(side="bottom", pady=20)

        def populate_dropdown():
            """Populate the dropdown menu with file names from an S3 bucket."""
            logging.info("Populating dropdown.")
            try:
                # Create a boto3 session using the "prod" profile
                try:
                    session = boto3.Session(profile_name="prod")
                    s3 = session.client("s3")
                except BotoCoreError as e:
                    logging.error(f"BotoCoreError: {e}")
                    # Handle missing SSO token error
                    if "SSO token" in str(e):
                        messagebox.showerror("AWS SSO Token Missing", "SSO token is missing. Please log in using Exodigo Login.")
                        dropdown_var.set("Please log in first")
                        dropdown.configure(values=["Please log in first"])
                        return
                    raise
                
                # Specify the S3 bucket name and list its contents
                bucket_name = "cdks3lambdasqsec2stack-playgroundorleviuploadbucke-at4u9pqvxnsr"
                response = s3.list_objects_v2(Bucket=bucket_name)
                file_names = [obj["Key"] for obj in response.get("Contents", [])]

                # Update the dropdown menu with the file names
                if file_names:
                    logging.info(f"Files found: {file_names}")
                    dropdown_var.set(file_names[0])
                    dropdown.configure(values=file_names)
                    login_button.pack_forget()  # Hide the login button if files are found
                else:
                    logging.warning("No files found in the bucket.")
                    dropdown_var.set("No files found")
                    dropdown.configure(values=["No files found"])
            except (NoCredentialsError, BotoCoreError) as e:
                logging.error(f"Error while populating dropdown: {e}")
                dropdown_var.set("Please log in first")
                dropdown.configure(values=["Please log in first"])
                # Show an error message if login fails
                if "SSO session" in str(e):
                    messagebox.showerror("AWS Login Failed", "SSO session expired. Please confirm your identity in the opened browser window.")
                else:
                    messagebox.showerror("AWS Login Failed", f"Error: {str(e)}")

        def run_sso_login():
            """Run the AWS SSO login process."""
            logging.info("Running SSO login.")
            try:
                # Execute the AWS SSO login command
                subprocess.run(["aws", "sso", "login", "--profile", "prod"], check=True)
                logging.info("SSO login successful.")
                messagebox.showinfo("SSO Login", "SSO login successful. Please try logging in again.")
                populate_dropdown()  # Re-populate the dropdown after successful login
            except subprocess.CalledProcessError as e:
                logging.error(f"SSO login failed: {e}")
                messagebox.showerror("SSO Login Failed", f"Error: {str(e)}")

        def on_login():
            """Handle the login button click event."""
            logging.info("Login button clicked.")
            # Run the SSO login process in a separate thread
            threading.Thread(target=run_sso_login, daemon=True).start()

        # Configure the login button to call the on_login function
        login_button.configure(command=on_login)
        
        # Populate the dropdown menu in a separate thread
        threading.Thread(target=populate_dropdown, daemon=True).start()
        
        # Start the main event loop for the GUI
        root.mainloop()
    def postExecute(self, parameters):
        # Log the completion of execution
        logging.info("Execution completed.")
        return
