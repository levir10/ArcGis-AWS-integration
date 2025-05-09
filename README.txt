How to run? 
===========

set up conda environment
========================
1. Run python command prompt AS ADMIN!
2. clone conda environment of ArcGIS (so that we can add to it) by: 
	conda create --<name-of-env> --clone arcgispro-py3
3.check if new environment was created successfully:
	conda info --envs   ( or:  conda env list)
4. to activate our new env: 
	conda activate <env-name>
5. make sure pip is upgraded: 
	python -m pip install --upgrade pip

6.now to install new python dependencies ( that conda doesn't have) use: 
	python -m pip install --force-reinstall <dependency-name> 
example: 
	python -m pip install --force-reinstall tkinter

7. to list all the dependencies - cd to the env folder. for example:
	cd C:\Program Files\ArcGIS\Pro\bin\Python\envs\<youe-env>
	
        conda list 

8. open ArcGIS pro ( if its already open - CLOSE IT! AND REOPEN)
9. go to --> project-->package manager --> at the right dropdowm , look for your new env


Run the script:
===============
1. open new ArcGIS project (you can use the template, or not) 
2. go to the toolbox ( on the right "Catalog" pane, right click on the toolboxes - " add Toolbox" 
3. choose the .pyt file named "arcGis-UI-Form.pyt" 
4. MAKE SURE the following files are in the project's folder as well 
( you can right click on the .atbx file in the Toolbox--> "Show in file explorer" and add the following files: )

	.end
	exodigo-logo-32x32.png
	exodigo-logo-32x32.ico
	arcGis-UI-Form.pyt


5. double click the arcGis-UI-Form.pyt file--> and than double click the Tool 
6. click "Run" button on the opened geoprocessing pane. 
7. on the opened costomtkinter gui that will open - click login 
8. reopen the gui if needed.. ( close gui and the geoprocessing tool and try to run the tool again. if needed - reopen arcgis. )
9. use the gui by selecting a site, and download or upload files..





