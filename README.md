# Optimized-route
# Route Optimization System Using Graph Algorithms

## Overview
This project implements a route optimization system using the Floyd-Warshall algorithm to find the most efficient routes between multiple locations. The system represents locations as a graph where edges denote paths and weights represent distances or travel time.

## Features
- Implementation of the Floyd-Warshall algorithm for all-pairs shortest paths
- Comparison with other path-finding algorithms (Dijkstra, A*)
- Integration with OpenStreetMap API for real geographic data
- Visualization of routes and graphs using NetworkX and Matplotlib
- User-friendly GUI interface built with Tkinter
- Time complexity analysis of implemented algorithms

## Project Structure
- `main.py`: Entry point for the application
- `algorithms/`: Contains implementations of path-finding algorithms
- `data_handler/`: Modules for managing location data and API integration
- `visualization/`: Components for graph and route visualization
- `ui/`: Tkinter-based user interface
- `analysis/`: Algorithm performance analysis and comparisons

## Technologies Used
- Python 3.x
- NetworkX for graph representation
- Matplotlib for visualization
- Tkinter for GUI
- OSMnx for OpenStreetMap integration
- NumPy for numerical operations

## Installation
```
pip install -r requirements.txt
```

## Usage
Run the main application:
```
python main.py
```

## Design and Analysis of Algorithms Concepts
- Graph representation and traversal
- Floyd-Warshall algorithm implementation and analysis
- Time complexity comparison between different path-finding algorithms
- Space complexity considerations
- Algorithm optimization techniques
