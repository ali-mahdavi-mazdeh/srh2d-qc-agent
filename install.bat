@echo off
REM install.bat - Creates the environment from the .yml file

REM Check if Conda is available

REM Create the environment from environment.yml
echo Creating the environment...
conda env create -f environment.yml

REM Notify user
echo Environment creation complete. To activate the environment, run activate_env.bat.
pause