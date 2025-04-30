#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Route Optimization System Using Graph Algorithms
Main application entry point
"""

import os
import sys

# Add project directories to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import application modules
from ui.app import RouteOptimizerApp

def main():
    """Main entry point for the application"""
    app = RouteOptimizerApp()
    app.run()

if __name__ == "__main__":
    main()