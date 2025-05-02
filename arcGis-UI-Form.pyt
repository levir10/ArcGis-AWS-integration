import arcpy
import tkinter as tk
from tkinter import messagebox
import threading
import boto3
from botocore.exceptions import BotoCoreError, NoCredentialsError

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

        # Create a dropdown menu but disable it initially
        dropdown_var = tk.StringVar(root)
        dropdown_var.set("Please log in first")  # Default value
        dropdown = tk.OptionMenu(root, dropdown_var, "Please log in first")
        dropdown.config(state="disabled")  # Disable the dropdown initially
        dropdown.pack(pady=5)

        def run_aws_login():
            try:
                session = boto3.Session(profile_name="prod")
                sts = session.client("sts")
                identity = sts.get_caller_identity()
                messagebox.showinfo("AWS Login", f"Logged in as:\n{identity['Arn']}")

                # Fetch S3 bucket contents after successful login
                bucket_name = "cdks3lambdasqsec2stack-playgroundorleviuploadbucke-at4u9pqvxnsr"
                s3 = session.client("s3")
                response = s3.list_objects_v2(Bucket=bucket_name)
                file_names = [obj["Key"] for obj in response.get("Contents", [])]

                # Update the dropdown menu with fetched file names
                dropdown_var.set(file_names[0] if file_names else "No files found")
                menu = dropdown["menu"]
                menu.delete(0, "end")
                for file_name in file_names:
                    menu.add_command(label=file_name, command=lambda value=file_name: dropdown_var.set(value))

                # Enable the dropdown
                dropdown.config(state="normal")

            except (NoCredentialsError, BotoCoreError) as e:
                messagebox.showerror("AWS Login Failed", f"Error: {str(e)}")

        def on_login():
            threading.Thread(target=run_aws_login, daemon=True).start()

        tk.Button(root, text="Exodigo Login", command=on_login).pack(side=tk.BOTTOM, pady=10)

        root.mainloop()

    def postExecute(self, parameters):
        return
