#!/usr/bin/env python3
"""
Faculty Conference Travel System - Entry Point
This file serves as the entry point for running the application.
"""

import os
import sys
import streamlit.cli as stcli

if __name__ == "__main__":
    # Add the current directory to path
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    # Run the Streamlit app
    sys.argv = ["streamlit", "run", "app/main.py"]
    stcli.main()