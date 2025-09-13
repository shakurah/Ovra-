# ARTISTING Project Scripts Documentation

This directory contains various shell scripts used for setting up, deploying, and managing the ARTISTING project. Each script serves a specific purpose to streamline development and deployment processes.

## Scripts Overview

1. **setup_backend.sh**: 
   - This script is responsible for setting up the backend environment. It installs necessary dependencies, configures the database, and prepares the Django application for development or production.

2. **setup_frontend.sh**: 
   - This script sets up the frontend environment. It installs required packages, configures the frontend application, and ensures that all assets are ready for development or production.

3. **deploy.sh**: 
   - This script handles the deployment of the ARTISTING application. It automates the process of building and deploying both the backend and frontend applications to the specified environment.

## Usage

To use any of the scripts, navigate to the `scripts` directory in your terminal and run the desired script. For example:

```bash
bash setup_backend.sh
```

Ensure that you have the necessary permissions to execute these scripts and that your environment is properly configured.

## Notes

- Make sure to review each script for specific configurations that may be required for your local or production environment.
- These scripts are designed to be modular and can be modified to fit the evolving needs of the ARTISTING project.

For further details on the overall project structure and components, refer to the main `README.md` file located in the root directory of the ARTISTING project.