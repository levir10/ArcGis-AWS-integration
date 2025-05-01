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
        root = tk.Tk()
        root.title("Testing Exodigo ArcGIS GUI")
        root.geometry("300x180")
        root.resizable(True, True)

        tk.Label(root, text="Click the button below:").pack(pady=10)

        entry = tk.Entry(root)
        entry.pack(pady=5)

        def on_submit():
            val = entry.get()
            messagebox.showinfo("Input Value", f"You entered: {val}")

        def run_aws_login():
            try:
                session = boto3.Session(profile_name="prod")
                sts = session.client("sts")
                identity = sts.get_caller_identity()
                messagebox.showinfo("AWS Login", f"Logged in as:\n{identity['Arn']}")
            except (NoCredentialsError, BotoCoreError) as e:
                messagebox.showerror("AWS Login Failed", f"Error: {str(e)}")

        def on_login():
            threading.Thread(target=run_aws_login, daemon=True).start()

        tk.Button(root, text="Submit", command=on_submit).pack(pady=5)
        tk.Button(root, text="Exodigo Login", command=on_login).pack(pady=5)

        root.mainloop()

    def postExecute(self, parameters):
        return
