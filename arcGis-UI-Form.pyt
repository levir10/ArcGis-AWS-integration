import arcpy
import tkinter as tk
from tkinter import messagebox
import threading
import boto3
from botocore.exceptions import BotoCoreError, NoCredentialsError
import subprocess


class Toolbox:
    def __init__(self):
        self.label = "Toolbox"
        self.alias = "toolbox"
        self.tools = [Tool]

class Tool:
    def __init__(self):
        self.label = "Tool"
        self.description = ""

    def getParameterInfo(self):
        text_param = arcpy.Parameter(
            displayName="Enter a name",
            name="name",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )

        dropdown_param = arcpy.Parameter(
            displayName="Choose an option",
            name="dropdown",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        dropdown_param.filter.type = "ValueList"
        dropdown_param.filter.list = ["Option A", "Option B", "Option C"]
        dropdown_param.value = "Option A"

        return [text_param, dropdown_param]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        threading.Thread(target=self.launch_gui, daemon=True).start()

    def launch_gui(self):
        # Create a simple GUI using Tkinter
        root = tk.Tk()
        root.title("Testing Exodigo ArcGIS GUI")  # Add a title to the window
        root.geometry("400x300")  # Set the window size
        root.resizable(True, True)  # Make the window resizable

        # Add a label to the window
        tk.Label(root, text="Select an option:").pack(pady=10)

        # Create a dropdown menu
        dropdown_var = tk.StringVar(root)
        dropdown_var.set("Loading...")  # Temporary value while loading
        dropdown = tk.OptionMenu(root, dropdown_var, "Loading...")
        dropdown.pack(pady=5)

        # Add a login button
        login_button = tk.Button(root, text="Exodigo Login")
        login_button.pack(side=tk.BOTTOM, pady=10)

        def populate_dropdown():
            try:
                # Fetch S3 bucket contents and populate the dropdown menu
                try:
                    session = boto3.Session(profile_name="prod")
                    s3 = session.client("s3")
                except BotoCoreError as e:
                    if "SSO token" in str(e):
                        messagebox.showerror("AWS SSO Token Missing", "SSO token is missing. Please log in using Exodigo Login.")
                        dropdown_var.set("Please log in first")
                        
                        return
                    raise
                bucket_name = "cdks3lambdasqsec2stack-playgroundorleviuploadbucke-at4u9pqvxnsr"
                response = s3.list_objects_v2(Bucket=bucket_name)
                file_names = [obj["Key"] for obj in response.get("Contents", [])]

                # Update the dropdown menu with fetched file names
                if file_names:
                    dropdown_var.set(file_names[0])
                    menu = dropdown["menu"]
                    menu.delete(0, "end")
                    for file_name in file_names:
                        menu.add_command(label=file_name, command=lambda value=file_name: dropdown_var.set(value))
                    login_button.pack_forget()  # Hide the login button
                else:
                    dropdown_var.set("No files found")
            except (NoCredentialsError, BotoCoreError) as e:
                dropdown_var.set("Please log in first")  # Default value
                
                if "SSO session" in str(e):
                    messagebox.showerror("AWS Login Failed", "SSO session expired. Please confirm your identity in the opened browser window.")
                else:
                    messagebox.showerror("AWS Login Failed", f"Error: {str(e)}")

        def run_sso_login():
            try:
                subprocess.run(["aws", "sso", "login", "--profile", "prod"], check=True)
                messagebox.showinfo("SSO Login", "SSO login successful. Please try logging in again.")
                populate_dropdown()  # Retry populating the dropdown after login
            except subprocess.CalledProcessError as e:
                messagebox.showerror("SSO Login Failed", f"Error: {str(e)}")

        def on_login():
            threading.Thread(target=run_sso_login, daemon=True).start()

        login_button.config(command=on_login)

        # Populate the dropdown initially
        threading.Thread(target=populate_dropdown, daemon=True).start()
        

        root.mainloop()

    def postExecute(self, parameters):
        return
