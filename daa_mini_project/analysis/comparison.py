#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Algorithm Comparison Module

This module provides functions for comparing different path-finding algorithms
and visualizing their performance characteristics.
"""

import time
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import pandas as pd

# Import our implementation
from algorithms.floyd_warshall import FloydWarshall

def compare_algorithms(graph, source, target, weight='weight'):
    """
    Compare different path-finding algorithms on the same graph.
    
    Args:
        graph (networkx.Graph): The input graph
        source: Source node
        target: Target node
        weight (str): Edge attribute used as weight
        
    Returns:
        pandas.DataFrame: Comparison results
    """
    results = {}
    
    # Floyd-Warshall (our implementation)
    fw = FloydWarshall()
    start_time = time.time()
    dist_dict, pred_dict = fw.run(graph, weight=weight)
    fw_time = time.time() - start_time
    fw_path = fw.reconstruct_path(source, target, pred_dict)
    fw_distance = dist_dict[source][target]
    
    # Dijkstra's algorithm (NetworkX)
    start_time = time.time()
    dijkstra_length = nx.dijkstra_path_length(graph, source, target, weight=weight)
    dijkstra_path = nx.dijkstra_path(graph, source, target, weight=weight)
    dijkstra_time = time.time() - start_time
    
    # A* algorithm (NetworkX)
    start_time = time.time()
    astar_path = nx.astar_path(graph, source, target, weight=weight)
    astar_length = nx.astar_path_length(graph, source, target, weight=weight)
    astar_time = time.time() - start_time
    
    # Store results
    results['floyd_warshall'] = {
        'algorithm': 'Floyd-Warshall',
        'distance': fw_distance,
        'path': fw_path,
        'time': fw_time,
        'path_length': len(fw_path)
    }
    
    results['dijkstra'] = {
        'algorithm': 'Dijkstra',
        'distance': dijkstra_length,
        'path': dijkstra_path,
        'time': dijkstra_time,
        'path_length': len(dijkstra_path)
    }
    
    results['astar'] = {
        'algorithm': 'A*',
        'distance': astar_length,
        'path': astar_path,
        'time': astar_time,
        'path_length': len(astar_path)
    }
    
    # Convert to DataFrame for easier analysis
    df = pd.DataFrame(results).T
    
    return df

def visualize_complexity(sizes, times, ax=None):
    """
    Visualize the time complexity of different algorithms.
    
    Args:
        sizes (list): List of graph sizes
        times (dict): Dictionary mapping algorithm names to lists of execution times
        ax (matplotlib.axes.Axes, optional): Matplotlib axes to plot on
        
    Returns:
        matplotlib.axes.Axes: The axes with the plot
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot each algorithm
    for algo, algo_times in times.items():
        if algo != 'sizes':  # Skip the sizes key
            ax.plot(sizes, algo_times, 'o-', label=algo.replace('_', ' ').title())
    
    # Add theoretical complexity curves for comparison
    n_values = np.array(sizes)
    
    # O(V^3) for Floyd-Warshall
    v3_values = n_values**3 / n_values[0]**3 * times['floyd_warshall'][0]
    ax.plot(n_values, v3_values, '--', label='O(V³)', alpha=0.5)
    
    # O(V^2 log V) for Dijkstra all pairs
    v2logv_values = n_values**2 * np.log(n_values) / (n_values[0]**2 * np.log(n_values[0])) * times['dijkstra_all'][0]
    ax.plot(n_values, v2logv_values, '--', label='O(V² log V)', alpha=0.5)
    
    # Add labels and legend
    ax.set_xlabel('Graph Size (nodes)')
    ax.set_ylabel('Execution Time (seconds)')
    ax.set_title('Algorithm Time Complexity Comparison')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Use log-log scale to better visualize complexity
    ax.set_xscale('log')
    ax.set_yscale('log')
    
    return ax

def visualize_comparison(results, ax=None):
    """
    Visualize algorithm comparison results.
    
    Args:
        results (pandas.DataFrame): Comparison results from compare_algorithms
        ax (matplotlib.axes.Axes, optional): Matplotlib axes to plot on
        
    Returns:
        matplotlib.axes.Axes: The axes with the plot
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
    
    # Extract algorithm names and execution times
    algorithms = results.index
    times = results['time'].values * 1000  # Convert to milliseconds
    
    # Create bar chart
    bars = ax.bar(algorithms, times, color=['blue', 'green', 'red'])
    
    # Add labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
               f"{height:.2f} ms", ha='center', va='bottom', fontsize=9)
    
    # Add labels and title
    ax.set_xlabel('Algorithm')
    ax.set_ylabel('Execution Time (ms)')
    ax.set_title('Algorithm Performance Comparison')
    ax.grid(True, axis='y', linestyle='--', alpha=0.7)
    
    return ax

def generate_random_graphs(sizes, density=0.3, weight_range=(1, 10)):
    """
    Generate random graphs of different sizes for testing.
    
    Args:
        sizes (list): List of graph sizes to generate
        density (float): Edge density (probability of edge creation)
        weight_range (tuple): Range for random edge weights
        
    Returns:
        dict: Dictionary mapping sizes to generated graphs
    """
    graphs = {}
    
    for n in sizes:
        # Generate random graph
        G = nx.gnp_random_graph(n, density, directed=False)
        
        # Add random weights
        for u, v in G.edges():
            G[u][v]['weight'] = np.random.uniform(*weight_range)
        
        # Ensure graph is connected
        if not nx.is_connected(G):
            # Get largest connected component
            largest_cc = max(nx.connected_components(G), key=len)
            G = G.subgraph(largest_cc).copy()
        
        graphs[n] = G
    
    return graphs