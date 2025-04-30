#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Route Optimizer Application

This module implements the GUI for the route optimization system using Tkinter.
It integrates with the Floyd-Warshall algorithm and OpenStreetMap API.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import networkx as nx
import numpy as np
import pandas as pd
import threading
import time

# Import OSM integration
import osmnx as ox
from geopy.geocoders import Nominatim
import requests

# Add parent directory to path for relative imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import algorithm modules
from algorithms.floyd_warshall import FloydWarshall, compare_with_networkx, analyze_time_complexity

# Configure OSMnx
# In OSMnx 2.0+, the config() method is replaced with settings object
ox.settings.use_cache = True
ox.settings.log_console = False

class RouteOptimizerApp:
    """
    Main application class for the Route Optimizer GUI.
    """
    
    def __init__(self):
        """
        Initialize the application.
        """
        self.root = tk.Tk()
        self.root.title("Route Optimizer - Floyd-Warshall Algorithm")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Set application icon if available
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass
        
        # Initialize variables
        self.graph = None
        self.locations = []
        self.floyd_warshall = FloydWarshall()
        self.geolocator = Nominatim(user_agent="route_optimizer_app")
        self.current_path = []
        
        # Create UI components
        self._create_menu()
        self._create_main_frame()
        
        # Configure style
        self._configure_style()
    
    def _configure_style(self):
        """
        Configure the application style.
        """
        style = ttk.Style()
        style.configure("TButton", padding=6, relief="flat", background="#ccc")
        style.configure("TLabel", padding=6)
        style.configure("TFrame", background="#f0f0f0")
        
        # Configure colors
        self.root.configure(background="#f0f0f0")
    
    def _create_menu(self):
        """
        Create the application menu.
        """
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New Graph", command=self._new_graph)
        file_menu.add_command(label="Load Sample Data", command=self._load_sample_data)
        file_menu.add_command(label="Load from OSM", command=self._load_from_osm)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Analysis menu
        analysis_menu = tk.Menu(menubar, tearoff=0)
        analysis_menu.add_command(label="Algorithm Comparison", command=self._show_algorithm_comparison)
        analysis_menu.add_command(label="Time Complexity Analysis", command=self._show_time_complexity)
        menubar.add_cascade(label="Analysis", menu=analysis_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def _create_main_frame(self):
        """
        Create the main application frame.
        """
        # Main container with two panels
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Controls
        left_frame = ttk.Frame(main_container, padding="10")
        main_container.add(left_frame, weight=1)
        
        # Right panel - Visualization
        right_frame = ttk.Frame(main_container, padding="10")
        main_container.add(right_frame, weight=3)
        
        # Setup left panel (controls)
        self._setup_control_panel(left_frame)
        
        # Setup right panel (visualization)
        self._setup_visualization_panel(right_frame)
    
    def _setup_control_panel(self, parent):
        """
        Setup the control panel with input fields and buttons.
        
        Args:
            parent: Parent frame
        """
        # Locations frame
        locations_frame = ttk.LabelFrame(parent, text="Locations", padding="10")
        locations_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Location entry
        location_entry_frame = ttk.Frame(locations_frame)
        location_entry_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(location_entry_frame, text="Location:").pack(side=tk.LEFT, padx=5)
        self.location_entry = ttk.Entry(location_entry_frame, width=30)
        self.location_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Add location button
        add_btn = ttk.Button(location_entry_frame, text="Add", command=self._add_location)
        add_btn.pack(side=tk.LEFT, padx=5)
        
        # Locations list
        list_frame = ttk.Frame(locations_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.locations_listbox = tk.Listbox(list_frame, height=10, 
                                           yscrollcommand=scrollbar.set)
        self.locations_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.locations_listbox.yview)
        
        # Buttons for location management
        btn_frame = ttk.Frame(locations_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Remove", 
                  command=self._remove_location).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear All", 
                  command=self._clear_locations).pack(side=tk.LEFT, padx=5)
        
        # Route calculation frame
        route_frame = ttk.LabelFrame(parent, text="Route Calculation", padding="10")
        route_frame.pack(fill=tk.X, pady=10)
        
        # Source and destination selection
        ttk.Label(route_frame, text="Source:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.source_var = tk.StringVar()
        self.source_combo = ttk.Combobox(route_frame, textvariable=self.source_var, state="readonly")
        self.source_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        
        ttk.Label(route_frame, text="Destination:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.dest_var = tk.StringVar()
        self.dest_combo = ttk.Combobox(route_frame, textvariable=self.dest_var, state="readonly")
        self.dest_combo.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        
        # Calculate button
        calc_btn = ttk.Button(route_frame, text="Calculate Route", command=self._calculate_route)
        calc_btn.grid(row=2, column=0, columnspan=2, pady=10)
        
        # Results frame
        results_frame = ttk.LabelFrame(parent, text="Results", padding="10")
        results_frame.pack(fill=tk.X, pady=5)
        
        # Distance and time display
        ttk.Label(results_frame, text="Distance:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.distance_var = tk.StringVar(value="-")
        ttk.Label(results_frame, textvariable=self.distance_var).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(results_frame, text="Computation Time:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.time_var = tk.StringVar(value="-")
        ttk.Label(results_frame, textvariable=self.time_var).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Path display
        ttk.Label(results_frame, text="Path:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W+tk.N)
        self.path_var = tk.StringVar(value="-")
        path_label = ttk.Label(results_frame, textvariable=self.path_var, wraplength=200)
        path_label.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
    
    def _setup_visualization_panel(self, parent):
        """
        Setup the visualization panel with matplotlib figure.
        
        Args:
            parent: Parent frame
        """
        # Create matplotlib figure
        self.fig = plt.Figure(figsize=(8, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("Route Visualization")
        self.ax.text(0.5, 0.5, "No graph loaded", ha="center", va="center", fontsize=12)
        self.ax.axis("off")
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add toolbar
        from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        toolbar.update()
    
    def _add_location(self):
        """
        Add a location to the list.
        """
        location = self.location_entry.get().strip()
        if not location:
            messagebox.showwarning("Input Error", "Please enter a location name.")
            return
        
        if location in self.locations:
            messagebox.showwarning("Input Error", f"Location '{location}' already exists.")
            return
        
        self.locations.append(location)
        self.locations_listbox.insert(tk.END, location)
        self.location_entry.delete(0, tk.END)
        
        # Update comboboxes
        self._update_location_combos()
    
    def _remove_location(self):
        """
        Remove the selected location from the list.
        """
        selection = self.locations_listbox.curselection()
        if not selection:
            messagebox.showwarning("Selection Error", "Please select a location to remove.")
            return
        
        index = selection[0]
        location = self.locations[index]
        del self.locations[index]
        self.locations_listbox.delete(index)
        
        # Update comboboxes
        self._update_location_combos()
    
    def _clear_locations(self):
        """
        Clear all locations from the list.
        """
        self.locations = []
        self.locations_listbox.delete(0, tk.END)
        
        # Update comboboxes
        self._update_location_combos()
    
    def _update_location_combos(self):
        """
        Update the source and destination comboboxes.
        """
        self.source_combo['values'] = self.locations
        self.dest_combo['values'] = self.locations
        
        if self.locations:
            self.source_combo.current(0)
            self.dest_combo.current(min(1, len(self.locations) - 1))
    
    def _new_graph(self):
        """
        Create a new empty graph.
        """
        self.graph = nx.Graph()
        self._clear_locations()
        self._update_graph_visualization()
        messagebox.showinfo("New Graph", "Created a new empty graph.")
    
    def _load_sample_data(self):
        """
        Load sample data for demonstration.
        """
        # Create a sample graph
        self.graph = nx.Graph()
        
        # Sample cities
        cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", 
                 "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"]
        
        # Add nodes
        for city in cities:
            self.graph.add_node(city)
        
        # Add edges with distances (in miles)
        edges = [
            ("New York", "Chicago", 800),
            ("New York", "Philadelphia", 100),
            ("Los Angeles", "San Diego", 120),
            ("Los Angeles", "San Jose", 340),
            ("Los Angeles", "Phoenix", 370),
            ("Chicago", "Houston", 940),
            ("Chicago", "Dallas", 800),
            ("Houston", "San Antonio", 200),
            ("Houston", "Dallas", 240),
            ("Phoenix", "San Diego", 350),
            ("Philadelphia", "Chicago", 740),
            ("San Antonio", "Dallas", 270),
            ("San Antonio", "Phoenix", 870),
            ("San Diego", "San Jose", 460),
            ("Dallas", "Phoenix", 890)
        ]
        
        for u, v, d in edges:
            self.graph.add_edge(u, v, weight=d)
        
        # Update locations
        self._clear_locations()
        for city in cities:
            self.locations.append(city)
            self.locations_listbox.insert(tk.END, city)
        
        # Update comboboxes
        self._update_location_combos()
        
        # Update visualization
        self._update_graph_visualization()
        
        messagebox.showinfo("Sample Data", "Loaded sample data with 10 US cities.")
    
    def _load_from_osm(self):
        """
        Load graph data from OpenStreetMap.
        """
        # Create dialog for OSM data loading
        osm_dialog = tk.Toplevel(self.root)
        osm_dialog.title("Load from OpenStreetMap")
        osm_dialog.geometry("400x300")
        osm_dialog.transient(self.root)
        osm_dialog.grab_set()
        
        # Place dialog in center of parent window
        osm_dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - osm_dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - osm_dialog.winfo_height()) // 2
        osm_dialog.geometry(f"+{x}+{y}")
        
        # Create form
        ttk.Label(osm_dialog, text="Location:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        location_entry = ttk.Entry(osm_dialog, width=30)
        location_entry.grid(row=0, column=1, padx=10, pady=10, sticky=tk.W+tk.E)
        location_entry.insert(0, "New York, USA")
        
        ttk.Label(osm_dialog, text="Network Type:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        network_var = tk.StringVar(value="drive")
        network_combo = ttk.Combobox(osm_dialog, textvariable=network_var, state="readonly")
        network_combo['values'] = ["drive", "walk", "bike", "all"]
        network_combo.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W+tk.E)
        
        ttk.Label(osm_dialog, text="Distance (meters):").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        distance_var = tk.StringVar(value="1000")
        distance_entry = ttk.Entry(osm_dialog, textvariable=distance_var, width=10)
        distance_entry.grid(row=2, column=1, padx=10, pady=10, sticky=tk.W)
        
        # Status label
        status_var = tk.StringVar()
        status_label = ttk.Label(osm_dialog, textvariable=status_var, wraplength=380)
        status_label.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky=tk.W+tk.E)
        
        # Progress bar
        progress = ttk.Progressbar(osm_dialog, mode="indeterminate")
        progress.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky=tk.W+tk.E)
        
        def fetch_osm_data():
            """
            Fetch OSM data in a separate thread.
            """
            location = location_entry.get().strip()
            network_type = network_var.get()
            try:
                distance = int(distance_var.get())
            except ValueError:
                status_var.set("Error: Distance must be a number.")
                progress.stop()
                return
            
            if not location:
                status_var.set("Error: Please enter a location.")
                progress.stop()
                return
            
            try:
                # Start progress bar
                progress.start()
                status_var.set(f"Fetching data for {location}...")
                osm_dialog.update_idletasks()
                
                # Import the OSM integration module
                from osm.integration import fetch_osm_graph, simplify_graph
                
                # Fetch graph from OSM using our integration module
                status_var.set(f"Fetching OSM graph for {location}...")
                osm_dialog.update_idletasks()
                G = fetch_osm_graph(location, distance=distance, network_type=network_type)
                
                # Simplify graph for visualization if needed
                if len(G.nodes) > 50:
                    status_var.set("Simplifying graph (too many nodes)...")
                    osm_dialog.update_idletasks()
                    G = simplify_graph(G, max_nodes=50)
                
                # Update the main graph
                self.graph = G
                
                # Update locations
                self._clear_locations()
                for node in G.nodes():
                    node_name = str(node)
                    self.locations.append(node_name)
                    self.locations_listbox.insert(tk.END, node_name)
                
                # Update comboboxes
                self._update_location_combos()
                
                # Update visualization
                self._update_graph_visualization()
                
                status_var.set(f"Successfully loaded graph with {len(G.nodes)} nodes and {len(G.edges)} edges.")
                osm_dialog.after(1000, osm_dialog.destroy)
                
            except Exception as e:
                status_var.set(f"Error: {str(e)}")
            finally:
                progress.stop()
        
        # Buttons
        button_frame = ttk.Frame(osm_dialog)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Load", command=lambda: threading.Thread(target=fetch_osm_data).start()).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancel", command=osm_dialog.destroy).pack(side=tk.LEFT, padx=10)
    
    def _calculate_route(self):
        """
        Calculate the shortest route between selected source and destination.
        """
        if not self.graph:
            messagebox.showwarning("No Graph", "Please load or create a graph first.")
            return
        
        source = self.source_var.get()
        destination = self.dest_var.get()
        
        if not source or not destination:
            messagebox.showwarning("Selection Error", "Please select source and destination.")
            return
        
        if source == destination:
            messagebox.showwarning("Selection Error", "Source and destination must be different.")
            return
        
        try:
            # Run Floyd-Warshall algorithm
            start_time = time.time()
            dist_dict, pred_dict = self.floyd_warshall.run(self.graph)
            execution_time = time.time() - start_time
            
            # Reconstruct path
            path = self.floyd_warshall.reconstruct_path(source, destination, pred_dict)
            
            if not path:
                messagebox.showwarning("No Path", f"No path exists between {source} and {destination}.")
                return
            
            # Calculate total distance
            total_distance = dist_dict[source][destination]
            
            # Update results
            self.distance_var.set(f"{total_distance:.2f} units")
            self.time_var.set(f"{execution_time*1000:.2f} ms")
            self.path_var.set(" → ".join(path))
            
            # Store current path for visualization
            self.current_path = path
            
            # Update visualization
            self._update_graph_visualization(path)
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def _update_graph_visualization(self, path=None):
        """
        Update the graph visualization.
        
        Args:
            path (list, optional): Path to highlight
        """
        if not self.graph:
            return
        
        # Clear the figure
        self.ax.clear()
        
        # Draw the graph
        if hasattr(self.graph.nodes(), "data") and 'x' in next(iter(self.graph.nodes(data=True)))[1]:
            # If graph has geographic coordinates
            pos = {node: (data['x'], data['y']) for node, data in self.graph.nodes(data=True)}
        else:
            # Use spring layout
            pos = nx.spring_layout(self.graph, seed=42)
        
        # Draw nodes
        nx.draw_networkx_nodes(self.graph, pos, node_color='lightblue', 
                              node_size=300, ax=self.ax)
        
        # Draw edges
        nx.draw_networkx_edges(self.graph, pos, width=1.0, alpha=0.5, ax=self.ax)
        
        # Draw labels if not too many nodes
        if len(self.graph.nodes) <= 50:
            nx.draw_networkx_labels(self.graph, pos, font_size=8, ax=self.ax)
        
        # Draw edge labels if not too many edges
        if len(self.graph.edges) <= 50:
            edge_labels = nx.get_edge_attributes(self.graph, 'weight')
            nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=edge_labels, 
                                        font_size=7, ax=self.ax)
        
        # Highlight path if provided
        if path:
            # Create path edges
            path_edges = [(path[i], path[i+1]) for i in range(len(path)-1)]
            
            # Highlight nodes in path
            nx.draw_networkx_nodes(self.graph, pos, nodelist=path, 
                                  node_color='red', node_size=300, ax=self.ax)
            
            # Highlight edges in path
            nx.draw_networkx_edges(self.graph, pos, edgelist=path_edges, 
                                  width=2.5, edge_color='red', ax=self.ax)
            
            # Set title with path information
            if len(path_edges) > 0:
                try:
                    path_length = sum(self.graph[u][v]['weight'] for u, v in path_edges)
                    self.ax.set_title(f"Shortest Path: {path[0]} to {path[-1]} (Length: {path_length:.2f})")
                except:
                    self.ax.set_title(f"Shortest Path: {path[0]} to {path[-1]}")
            else:
                self.ax.set_title(f"Path: {path[0]}")
        else:
            self.ax.set_title(f"Graph: {len(self.graph.nodes)} nodes, {len(self.graph.edges)} edges")
        
        self.ax.axis('off')
        self.canvas.draw()
    
    def _show_algorithm_comparison(self):
        """
        Show a comparison of different algorithms.
        """
        if not self.graph or len(self.graph.nodes) < 2:
            messagebox.showwarning("No Graph", "Please load a graph with at least 2 nodes first.")
            return
        
        # Create dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Algorithm Comparison")
        dialog.geometry("800x600")
        dialog.transient(self.root)
        
        # Create frame for algorithm selection
        selection_frame = ttk.Frame(dialog, padding="10")
        selection_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(selection_frame, text="Source:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        source_var = tk.StringVar()
        source_combo = ttk.Combobox(selection_frame, textvariable=source_var, values=self.locations, state="readonly")
        source_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        if self.locations:
            source_combo.current(0)
        
        ttk.Label(selection_frame, text="Destination:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        dest_var = tk.StringVar()
        dest_combo = ttk.Combobox(selection_frame, textvariable=dest_var, values=self.locations, state="readonly")
        dest_combo.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        if len(self.locations) > 1:
            dest_combo.current(1)
        
        # Button to run comparison
        ttk.Button(selection_frame, text="Compare Algorithms", 
                  command=lambda: self._run_comparison(dialog, source_var.get(), dest_var.get())
                 ).grid(row=2, column=0, columnspan=2, pady=10)
        
        # Create frame for results
        results_frame = ttk.Frame(dialog, padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create notebook for results
        notebook = ttk.Notebook(results_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab for table
        table_frame = ttk.Frame(notebook)
        notebook.add(table_frame, text="Results Table")
        
        # Tab for chart
        chart_frame = ttk.Frame(notebook)
        notebook.add(chart_frame, text="Performance Chart")
        
        # Create matplotlib figure for chart
        fig = plt.Figure(figsize=(6, 4), dpi=100)
        ax = fig.add_subplot(111)
        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Create table
        columns = ("Algorithm", "Distance", "Time (ms)", "Path Length")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        # Set column headings
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor="center")
        
        tree.pack(fill=tk.BOTH, expand=True)
        
        # Store references for the comparison function
        dialog.tree = tree
        dialog.fig = fig
        dialog.ax = ax
        dialog.canvas = canvas
        
    def _run_comparison(self, dialog, source, destination):
        """
        Run algorithm comparison and update results.
        
        Args:
            dialog: The dialog window
            source: Source node
            destination: Destination node
        """
        if not source or not destination:
            messagebox.showwarning("Selection Error", "Please select source and destination.")
            return
        
        if source == destination:
            messagebox.showwarning("Selection Error", "Source and destination must be different.")
            return
        
        try:
            # Run comparison
            results = compare_with_networkx(self.graph, source, destination)
            
            # Clear existing data
            for item in dialog.tree.get_children():
                dialog.tree.delete(item)
            
            # Add data to table
            for algo, data in results.items():
                dialog.tree.insert("", tk.END, values=(
                    algo.capitalize(),
                    f"{data['distance']:.2f}",
                    f"{data['time']*1000:.2f}",
                    len(data['path'])
                ))
            
            # Update chart
            dialog.ax.clear()
            algorithms = list(results.keys())
            times = [results[algo]['time']*1000 for algo in algorithms]  # Convert to ms
            
            # Create bar chart
            bars = dialog.ax.bar([algo.capitalize() for algo in algorithms], times, color=['blue', 'green', 'red'])
            
            # Add labels
            for bar in bars:
                height = bar.get_height()
                dialog.ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                       f"{height:.2f}", ha='center', va='bottom', fontsize=9)
            
            dialog.ax.set_ylabel('Time (ms)')
            dialog.ax.set_title('Algorithm Performance Comparison')
            dialog.fig.tight_layout()
            dialog.canvas.draw()
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def _show_time_complexity(self):
        """
        Show time complexity analysis of different algorithms.
        """
        # Create dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Time Complexity Analysis")
        dialog.geometry("800x600")
        dialog.transient(self.root)
        
        # Create frame for controls
        control_frame = ttk.Frame(dialog, padding="10")
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Graph size range
        ttk.Label(control_frame, text="Graph Sizes:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        size_var = tk.StringVar(value="10,20,30,40,50")
        size_entry = ttk.Entry(control_frame, textvariable=size_var, width=30)
        size_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        
        # Density
        ttk.Label(control_frame, text="Edge Density (0-1):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        density_var = tk.StringVar(value="0.3")
        density_entry = ttk.Entry(control_frame, textvariable=density_var, width=10)
        density_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Progress indicator
        progress_var = tk.StringVar()
        progress_label = ttk.Label(control_frame, textvariable=progress_var)
        progress_label.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
        
        # Create matplotlib figure
        fig = plt.Figure(figsize=(6, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.set_title("Algorithm Time Complexity")
        ax.set_xlabel("Graph Size (nodes)")
        ax.set_ylabel("Time (seconds)")
        
        canvas = FigureCanvasTkAgg(fig, master=dialog)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        def run_analysis():
            try:
                # Parse sizes
                sizes = [int(s.strip()) for s in size_var.get().split(',')]
                density = float(density_var.get())
                
                if not sizes:
                    messagebox.showwarning("Input Error", "Please enter valid graph sizes.")
                    return
                
                if not 0 < density < 1:
                    messagebox.showwarning("Input Error", "Density must be between 0 and 1.")
                    return
                
                # Run analysis in a separate thread
                def analysis_thread():
                    try:
                        progress_var.set("Running analysis...")
                        results = analyze_time_complexity(sizes, density)
                        
                        # Plot results
                        ax.clear()
                        ax.plot(results['sizes'], results['floyd_warshall'], 'o-', label='Floyd-Warshall')
                        ax.plot(results['sizes'], results['dijkstra_all'], 's-', label='Dijkstra (all pairs)')
                        ax.plot(results['sizes'], results['bellman_ford_all'], '^-', label='Bellman-Ford (all pairs)')
                        
                        ax.legend()
                        ax.set_title("Algorithm Time Complexity")
                        ax.set_xlabel("Graph Size (nodes)")
                        ax.set_ylabel("Time (seconds)")
                        ax.grid(True, linestyle='--', alpha=0.7)
                        
                        fig.tight_layout()
                        canvas.draw()
                        
                        progress_var.set("Analysis complete.")
                    except Exception as e:
                        progress_var.set(f"Error: {str(e)}")
                
                threading.Thread(target=analysis_thread).start()
                
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}")
        
        # Button to run analysis
        ttk.Button(control_frame, text="Run Analysis", command=run_analysis).grid(row=3, column=0, columnspan=2, pady=10)
    
    def _show_about(self):
        """
        Show about dialog.
        """
        about_text = """
        Route Optimization System Using Graph Algorithms
        
        This application implements the Floyd-Warshall algorithm for finding
        the shortest paths between all pairs of vertices in a graph.
        
        Features:
        - Floyd-Warshall algorithm implementation
        - Integration with OpenStreetMap
        - Comparison with Dijkstra and A* algorithms
        - Time complexity analysis
        
        Developed as a mini-project for Design and Analysis of Algorithms (21CSC204J)
        """
        
        messagebox.showinfo("About", about_text)
    
    def run(self):
        """
        Run the application.
        """
        self.root.mainloop()