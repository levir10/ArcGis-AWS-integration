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
import requests
from requests_aws4auth import AWS4Auth
import urllib.request
from dotenv import load_dotenv
import os
import zipfile
import time


# Always load .env from script directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"), override=True)
 #Load the .env file. the overrid -  ensures env file values override existing ones
# Configure logging to log messages to a file
log_path = os.path.join(os.path.dirname(__file__), "log.txt")
logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
# Flags to indicate if the conversion is done
activate_main_thread = threading.Event()
place_layers_on_map_flag = threading.Event()
upload_files_flag = threading.Event()
#use environment variables to get the values of the following variables
APPSYNC_API_URL = os.environ.get("APPSYNC_API_URL")
AWS_REGION = os.environ.get("AWS_REGION")
AWS_PROFILE = os.environ.get("AWS_PROFILE", "default")
BUCKET_NAME_SITES = os.environ.get("BUCKET_NAME_SITES", "exodb-sites-files")
BUCKET_NAME_USER_LAYERS = os.environ.get("BUCKET_NAME_USER_LAYERS", "exodigo-sites-user-layers")
# Configure logging to log messages to a file

site_dict = {}  # {site_name: s3_ref}
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

        return [dropdown_param]

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
        logging.info("Execution started.")
        threading.Thread(target=self.launch_gui, daemon=True).start()
        logging.info("this log is from the main thread")
        iteration=0
        while True:
            logging.info(f"Waiting for main thread: activation number: {iteration}")
            self.wait_and_run_main_thread()

        
    def wait_and_run_main_thread(self, timeout=600):
        logging.info("Waiting for main thread activation...")
        is_set = activate_main_thread.wait(timeout=timeout)
        if not is_set:
            logging.error("Timeout: No main thread action triggered.")
            return

        # Now check which action to perform
        if place_layers_on_map_flag.is_set():
            self.add_features_to_map()
            place_layers_on_map_flag.clear()
            logging.info("Ran add_features_to_map from main thread.")

        elif upload_files_flag.is_set():
            self.export_features_to_geojson()
            upload_files_flag.clear()
            logging.info("Ran export_features_to_geojson from main thread.")

        activate_main_thread.clear()  # Reset for next use


    def add_features_to_map(self):
        logging.info(f"Run the map placement on the main thread!!!!!!!!!!!.")
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        m = aprx.activeMap
        logging.info("has map object")
        with open("C:/temp_arcgis_geojson/geojson_outputs.txt", "r") as f:
            for line in f:
                fc_path = line.strip()
                if arcpy.Exists(fc_path):
                    m.addDataFromPath(fc_path)
    def export_features_to_geojson(self):
        logging.info("Exporting template features to GeoJSON...")
        #Feature types from the exodigo template
        feature_types = [
            "Lines", "OH_Poles", "OH_Lines", "QC_Polygons", "Excavations",
            "Scanned_area", "Unscanned_area", "Site_Classification", "Manholes", "Elements"
        ]
        project_folder = os.getcwd()  # Or use your project folder logic
        for feature in feature_types:
            out_json = os.path.join(project_folder, f"{feature}_FeaturesToJSON.geojson")
            try:
                arcpy.conversion.FeaturesToJSON(
                    in_features=feature,
                    out_json_file=out_json,
                    format_json="FORMATTED",
                    include_z_values="Z_VALUES",
                    include_m_values="NO_M_VALUES",
                    geoJSON="GEOJSON",
                    outputToWGS84="WGS84",
                    use_field_alias="USE_FIELD_NAME"
                )
                logging.info(f"Exported {feature} to {out_json}")
            except Exception as e:
                logging.error(f"Failed to export {feature}: {e}")

    def launch_gui(self):
        """Launch the main GUI application."""
        logging.info("Launching GUI.")
        # Set the appearance and theme for the customtkinter GUI

        script_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(script_dir, "exodigo-logo-32x32.png")
        if os.path.exists(image_path):
            logging.info(f"Image file exists at: {os.path.abspath(image_path)}")
        else:
            logging.error(f"Image file not found at: {os.path.abspath(image_path)}")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")#set the color theme to dark-blue

        # Create the main application window
        root = ctk.CTk()
        root.title("Exodigo ArcGis Integrator")
        root.geometry("400x300")
        root.resizable(False, False)
        # Set custom window icon
        icon_path = os.path.join(script_dir, "exodigo-logo-32x32.ico")
        root.wm_iconbitmap(icon_path)

        #====================================================================================================================#
        #dropdown menu for getting s3 bucket files
        #====================================================================================================================#
        # Add a label to the GUI
        
        label_main = ctk.CTkLabel(root, text="Select a site:", font=ctk.CTkFont(size=16, weight="bold"))
        label_main.pack(pady=10)
        
        # Add a label for the filter entry
        filter_label = ctk.CTkLabel(root, text="Type here to filter site names", font=ctk.CTkFont(size=12, weight="normal"))
        filter_label.place(x=10, y=50)  # Set the x and y coordinates for the label

        # Add a filter entry above the ComboBox
        filter_var = ctk.StringVar()
        filter_entry = ctk.CTkEntry(root, textvariable=filter_var, width=300)
        filter_entry.place(x=10, y=80)  # Align the filter entry with the label

        # Create a dropdown menu with a default "Loading..." value
        combo_var = ctk.StringVar(value="Loading...")
        combo = ctk.CTkComboBox(root, variable=combo_var, values=["Loading..."], width=300)
        combo.place(x=10, y=120)  # Align the dropdown menu with the label and filter entry
        #====================================================================================================================#
        #dropdown menu for getting s3 bucket files
        #====================================================================================================================#
    

        # Load the image (make sure the path is correct and file exists)
        image_path = "exodigo-logo-32x32.png"
        image = ctk.CTkImage(light_image=Image.open(image_path), size=(32, 32))
        # Add a login button with image
        login_button = ctk.CTkButton(
            root,
            text="Exodigo Login",
            image=image,
            compound="left",  # Image to the left of the text; use "top", "right", "bottom" as needed
            corner_radius=20,
            fg_color="#1f6aa5",
            hover_color="#144870"
        )
        login_button.pack(side="bottom", pady=20)

        # Create a download button (initially hidden - once site combobox is populated - it will be seen)
        download_button = ctk.CTkButton(
            root,
            text="Download Site File",
            corner_radius=6,
                fg_color="#219ebc",
            hover_color="#06d6a0",
            command=lambda: on_site_selected()
        )
        download_button.place(x=10, y=160)  # Align with the left side of the combobox and place below it
        download_button.pack_forget()  # Hide initiall

        #create a n "upload for inspection" button
        upload_button = ctk.CTkButton(
            root,
            text="Upload for Inspection",
            corner_radius=6,
            fg_color="#219ebc",
            hover_color="#06d6a0",
            command=lambda: upload_for_inspection()
        )

        upload_button.place(x=10, y=200)  # Align with the left side of the combobox and place below it



        def run_sso_login():
            """Run the AWS SSO login process."""
            logging.info("Running SSO login.")
            try:
                # Execute the AWS SSO login command
                subprocess.run(["aws", "sso", "login", "--profile", AWS_PROFILE], check=True)
                logging.info("SSO login successful.")
                messagebox.showinfo("SSO Login", "SSO login successful. Please try logging in again.")
                # populate_dropdown()  # Re-populate the dropdown after successful login
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
        # threading.Thread(target=populate_dropdown, daemon=True).start()
    #=====================================================================================================================#
        #dropdown menu for getting site names
    #=====================================================================================================================#
        def fetch_sites():
            """Fetch site list from AppSync GraphQL API using IAM auth and update site_dict."""
            global site_dict
            logging.info("Fetching site list from GraphQL API (IAM auth).")
            query = """
            query MyQuery {
                searchLocations(limit: 3000) {
                    nextToken
                    items {
                        country
                        id
                        region
                        state
                        sites {
                            items {
                                name
                                s3_ref
                            }
                        }
                    }
                }
            }
            """
            session = boto3.Session(profile_name=AWS_PROFILE)
            credentials = session.get_credentials().get_frozen_credentials()
            awsauth = AWS4Auth(
                credentials.access_key,
                credentials.secret_key,
                AWS_REGION,
                "appsync",
                session_token=credentials.token
            )
            headers = {"Content-Type": "application/json"}
            try:
                response = requests.post(
                    APPSYNC_API_URL,
                    json={"query": query},
                    headers=headers,
                    auth=awsauth,
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()
                items = data.get("data", {}).get("searchLocations", {}).get("items", [])
                site_dict.clear()
                for item in items:
                    sites = item.get("sites", {}).get("items", [])
                    for site in sites:
                        name = site.get("name")
                        s3_ref = site.get("s3_ref")
                        if name and s3_ref:
                            site_dict[name] = s3_ref
                if not site_dict:
                    site_dict["No site names found"] = None
            except Exception as e:
                logging.error(f"Failed to fetch sites: {e}")
                site_dict.clear()
                site_dict["Failed to load sites"] = None

        def sites_selector():
            """Update the dropdown menu with the filtered site names."""
            filter_text = filter_var.get().lower()
            site_names = list(site_dict.keys())
            if site_names:
                filtered = [name for name in site_names if filter_text in name.lower()]
                if filtered:
                    combo_var.set(filtered[0])
                    combo.configure(values=filtered)
                    download_button.pack(side="left", padx=10, pady=0)  # Show download button

                else:
                    combo_var.set("No sites found")
                    combo.configure(values=["No sites found"])
                    download_button.pack_forget()
            else:
                combo_var.set("No sites found")
                combo.configure(values=["No sites found"])
                download_button.pack_forget()
            login_button.pack_forget()

        def fetch_and_render_sites():
            fetch_sites()
            root.after(0, sites_selector)
        # Add this after creating filter_entry
        def on_filter_change(*args):
            sites_selector()

        filter_var.trace_add("write", on_filter_change)

        #=============================================================================================================#
        #get site files from s3 bucket
        #=============================================================================================================#
        
        def download_site_zip(s3_ref):
            """Download the site_export.geojson.zip file from S3 using boto3 (for private files)."""
            bucket_name = BUCKET_NAME_USER_LAYERS
            object_key = f"download/{s3_ref}/{s3_ref}.site_export.geojson.zip"
            local_filename = f"{s3_ref}.site_export.geojson.zip"
            try:
                session = boto3.Session(profile_name=AWS_PROFILE)
                s3 = session.client("s3")
                logging.info(f"Downloading file from s3://{bucket_name}/{object_key}")
                s3.download_file(bucket_name, object_key, local_filename)
                logging.info(f"File downloaded successfully: {local_filename}")
                messagebox.showinfo("Download Successful", f"File downloaded: {local_filename}")
            except Exception as e:
                logging.error(f"Failed to download file: {e}")
                messagebox.showerror("Download Failed", f"Error: {str(e)}")



        # After download_site_zip, add:
        def unzip_site_file(zip_path, extract_to):
            """Unzip the downloaded site zip file to the specified folder."""
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_to)
                logging.info(f"Unzipped {zip_path} to {extract_to}")
                return True
            except Exception as e:
                logging.error(f"Failed to unzip file: {e}")
                messagebox.showerror("Unzip Failed", f"Error: {str(e)}")
                return False
        
        
        #run json to feature command for each geojson file in the unzipped folder
        def json_to_feature_for_folder(unzipped_folder, gdb_path):
            """Loop through subfolders and run JSONToFeatures for each geojson file, then add to map."""
            logging.info(f"Processing folder: {unzipped_folder} to get json files")
             # Ensure the temp folder that will contain the .gdb file paths exists
            temp_folder = "C:/temp_arcgis_geojson"
            if not os.path.exists(temp_folder):
                os.makedirs(temp_folder)
                logging.info(f"Created folder: {temp_folder}")
            
            # Add the file path to a "geojson_outputs.txt" file for future reference
            output_file = os.path.join(temp_folder, "geojson_outputs.txt")
            if os.path.exists(output_file):
                os.remove(output_file)  # Delete the existing file
            for subfolder in os.listdir(unzipped_folder):
                subfolder_path = os.path.join(unzipped_folder, subfolder)
                if os.path.isdir(subfolder_path):
                    for filename in os.listdir(subfolder_path):
                        if filename.endswith(".geojson"):
                            file_path = os.path.join(subfolder_path, filename)
                            # Determine geometry type
                            if "MultiPoint" in filename:
                                geometry_type = "MULTIPOINT"
                            elif "Point" in filename:
                                geometry_type = "POINT"
                            elif "Polygon" in filename:
                                geometry_type = "POLYGON"
                            elif "LineString" in filename:
                                geometry_type = "POLYLINE"
                            else:
                                logging.warning(f"Unknown geometry type for {filename}, skipping.")
                                continue
                            # Output feature class name (remove .geojson and illegal chars)
                            out_name = os.path.splitext(filename)[0].replace(".", "_").replace("-", "_")
                            out_features = os.path.join(gdb_path, out_name)
                            try:
                                if arcpy.Exists(out_features):
                                    arcpy.Delete_management(out_features)
                                arcpy.conversion.JSONToFeatures(
                                    in_json_file=file_path,
                                    out_features=out_features,
                                    geometry_type=geometry_type
                                )
                                logging.info(f"Converted {file_path} to {out_features} ({geometry_type})")
                                with open(output_file, "a") as f:
                                    f.write(f"{out_features}\n")
                                logging.info(f"Added {out_features} to {output_file}")
                            except Exception as e:
                                logging.error(f"Failed to convert {file_path}: {e}")
                
            messagebox.showinfo("Files Successfully added", "All files were successfully added to the project's Database.")       
            response = messagebox.askyesno("Add to Map", "Conversion complete. Add layers to the map?")
            if response:
                #set flag to true and notify the main thread to stop waiting- and run the add_to_map function
                activate_main_thread.set()
                place_layers_on_map_flag.set()
                logging.info(f"Flag was set to true")
                download_button.configure(state="normal")  # Re-enable the download button
                
  



        # triggered when user clicks on the downloiad button
        def on_site_selected():
            """Handle the event when a user presses the download button and site is selected from the dropdown."""
            #make the download_button unresponsive until the download is done
            download_button.configure(state="disabled")
            selected_site_name = combo_var.get()
            s3_ref = site_dict.get(selected_site_name)
            if s3_ref:
                def process():
                    zip_filename = f"{s3_ref}.site_export.geojson.zip"
                    unzip_folder = os.path.join(os.getcwd(), f"{s3_ref}.site_export.geojson")
                    gdb_path = None
                    # Download and unzip in background thread
                    download_site_zip(s3_ref)
                    if unzip_site_file(zip_filename, unzip_folder):
                        # Find or create .gdb
                        gdbs = [f for f in os.listdir(os.getcwd()) if f.endswith(".gdb")]
                        template_gdbs = [f for f in gdbs if "template_v" in f.lower()]
                        if template_gdbs:
                            gdb_path = os.path.join(os.getcwd(), template_gdbs[0])
                            logging.info(f"Using template FileGDB: {gdb_path}")
                        elif gdbs:
                            gdb_path = os.path.join(os.getcwd(), gdbs[0])
                            logging.info(f"Using existing FileGDB: {gdb_path}")
                        else:
                            gdb_path = os.path.join(os.getcwd(), f"{selected_site_name}.gdb")
                            arcpy.management.CreateFileGDB(os.getcwd(), f"{selected_site_name}.gdb")
                            logging.info(f"Created new FileGDB: {gdb_path}")
                        # Now run arcpy conversion in the main thread
                        def run_conversion():
                            json_to_feature_for_folder(unzip_folder, gdb_path)
                            messagebox.showinfo("Success", f"All GeoJSON files converted to {gdb_path}")
                        root.after(0, run_conversion)
                threading.Thread(target=process, daemon=True).start()
            else:
                messagebox.showerror("Error", "Could not find s3_ref for the selected site.")


        def upload_for_inspection():
            """Handle the event when a user presses the upload button.
            This function will upload the selected site to the S3 bucket for inspection."""
            # Implement the upload logic here
            activate_main_thread.set()
            upload_files_flag.set()
            logging.info("Upload for inspection button clicked.")
            
            
            




        # After login_button.configure(command=on_login)
        threading.Thread(target=fetch_and_render_sites, daemon=True).start()
        # Start the main event loop for the GUI
        root.mainloop()
    def postExecute(self, parameters):
        # Log the completion of execution
        logging.info("Execution completed.")
        return
