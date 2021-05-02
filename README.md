An implementation of VIDMAG in Python with GUI
==============================

This code is a replication of the algorithm presented in "Eulerian video magnification for revealing subtle changes in the world",
with a GUI to modify parameters.

Project Organization
------------

    ├── LICENSE
    ├── README.md          
    ├── data
    │   ├── processed      <- Processed videos (magnified videos).
    │   └── raw            <- Original videos
    │
    ├── references         
    │
    ├── requirements.txt   
    │
    ├── setup.py           
    ├── src                <- Source code for use in this project.
        ├── __init__.py    <- Makes src a Python module
        │
        ├── gui           <- Scripts for GUI
        |   └── images    <- Icons for the gui
        |   └── __init__.py 
        |   └── constants.py  <-- Default parameters, saving directories
        |   └── gui.py
        |   └── helpers.py
        │
        └── processing       <- Scripts to magnify videos
            └── __init__.py
            └── processing.py

--------

<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
