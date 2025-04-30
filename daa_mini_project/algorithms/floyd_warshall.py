#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Floyd-Warshall Algorithm Implementation

This module implements the Floyd-Warshall algorithm for finding shortest paths
in a weighted graph with positive or negative edge weights (but no negative cycles).

The algorithm computes the shortest path between all pairs of vertices in the graph.
Time Complexity: O(V^3) where V is the number of vertices
Space Complexity: O(V^2)
"""

import numpy as np
import networkx as nx
import time
import matplotlib.pyplot as plt

class FloydWarshall:
    """
    Implementation of the Floyd-Warshall algorithm for finding all-pairs shortest paths.
    """
    
    def __init__(self):
        """
        Initialize the Floyd-Warshall algorithm.
        """
        self.distances = None
        self.predecessors = None
        self.execution_time = None
    
    def run(self, graph, weight='weight'):
        """
        Run the Floyd-Warshall algorithm on the given graph.
        
        Args:
            graph (networkx.Graph): The input graph
            weight (str): Edge attribute used as weight
            
        Returns:
            tuple: (distances, predecessors) matrices
        """
        start_time = time.time()
        
        # Convert NetworkX graph to adjacency matrix
        nodes = list(graph.nodes())
        n = len(nodes)
        node_to_idx = {node: i for i, node in enumerate(nodes)}
        
        # Initialize distance and predecessor matrices
        inf = float('inf')
        dist = np.full((n, n), inf)
        pred = np.full((n, n), -1, dtype=int)
        
        # Set diagonal elements to 0
        np.fill_diagonal(dist, 0)
        
        # Initialize with direct edges
        for u, v, data in graph.edges(data=True):
            i, j = node_to_idx[u], node_to_idx[v]
            w = data.get(weight, 1.0)  # Default weight is 1.0
            dist[i, j] = w
            pred[i, j] = i
            
            # For undirected graphs, add the reverse edge
            if not graph.is_directed():
                dist[j, i] = w
                pred[j, i] = j
        
        # Floyd-Warshall algorithm
        for k in range(n):
            for i in range(n):
                for j in range(n):
                    if dist[i, j] > dist[i, k] + dist[k, j]:
                        dist[i, j] = dist[i, k] + dist[k, j]
                        pred[i, j] = pred[k, j]
        
        # Store results
        self.distances = dist
        self.predecessors = pred
        self.execution_time = time.time() - start_time
        
        # Convert matrices back to node-indexed dictionaries
        dist_dict = {}
        pred_dict = {}
        
        for i, u in enumerate(nodes):
            dist_dict[u] = {}
            pred_dict[u] = {}
            for j, v in enumerate(nodes):
                dist_dict[u][v] = dist[i, j]
                if pred[i, j] != -1:
                    pred_dict[u][v] = nodes[pred[i, j]]
                else:
                    pred_dict[u][v] = None
        
        return dist_dict, pred_dict
    
    def reconstruct_path(self, source, target, predecessors=None):
        """
        Reconstruct the shortest path from source to target using the predecessor matrix.
        
        Args:
            source: Source node
            target: Target node
            predecessors: Predecessor matrix (if None, use the stored one)
            
        Returns:
            list: The shortest path from source to target
        """
        if predecessors is None:
            predecessors = self.predecessors
            
        if isinstance(predecessors, np.ndarray):
            # If using numpy array, convert to node indices
            raise ValueError("Please provide node-indexed predecessor dictionary")
        
        if source == target:
            return [source]
            
        if predecessors[source][target] is None:
            return []  # No path exists
            
        path = [target]
        while path[0] != source:
            path.insert(0, predecessors[source][path[0]])
            
        return path
    
    def get_execution_time(self):
        """
        Get the execution time of the last run.
        
        Returns:
            float: Execution time in seconds
        """
        return self.execution_time
    
    def visualize_path(self, graph, path, ax=None):
        """
        Visualize the shortest path in the graph.
        
        Args:
            graph (networkx.Graph): The input graph
            path (list): The path to visualize
            ax (matplotlib.axes.Axes, optional): Matplotlib axes to plot on
            
        Returns:
            matplotlib.axes.Axes: The axes with the plot
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 8))
            
        # Create a subgraph with the path edges
        path_edges = [(path[i], path[i+1]) for i in range(len(path)-1)]
        path_graph = graph.edge_subgraph(path_edges)
        
        # Draw the full graph
        pos = nx.spring_layout(graph, seed=42)  # Consistent layout
        nx.draw_networkx_nodes(graph, pos, node_color='lightblue', node_size=500, ax=ax)
        nx.draw_networkx_edges(graph, pos, width=1.0, alpha=0.5, ax=ax)
        nx.draw_networkx_labels(graph, pos, ax=ax)
        
        # Highlight the path
        nx.draw_networkx_nodes(graph, pos, nodelist=path, node_color='red', node_size=500, ax=ax)
        nx.draw_networkx_edges(
            graph, pos, edgelist=path_edges, width=2.5, edge_color='red', ax=ax
        )
        
        # Add edge labels
        edge_labels = nx.get_edge_attributes(graph, 'weight')
        nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, ax=ax)
        
        ax.set_title(f"Shortest Path (Length: {sum(graph[u][v]['weight'] for u, v in path_edges)})")
        ax.axis('off')
        
        return ax


def compare_with_networkx(graph, source, target, weight='weight'):
    """
    Compare Floyd-Warshall implementation with NetworkX's built-in algorithms.
    
    Args:
        graph (networkx.Graph): The input graph
        source: Source node
        target: Target node
        weight (str): Edge attribute used as weight
        
    Returns:
        dict: Comparison results
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
        'distance': fw_distance,
        'path': fw_path,
        'time': fw_time
    }
    
    results['dijkstra'] = {
        'distance': dijkstra_length,
        'path': dijkstra_path,
        'time': dijkstra_time
    }
    
    results['astar'] = {
        'distance': astar_length,
        'path': astar_path,
        'time': astar_time
    }
    
    return results


def analyze_time_complexity(sizes, density=0.3, weight_range=(1, 10)):
    """
    Analyze time complexity of Floyd-Warshall vs. other algorithms for different graph sizes.
    
    Args:
        sizes (list): List of graph sizes to test
        density (float): Edge density (probability of edge creation)
        weight_range (tuple): Range for random edge weights
        
    Returns:
        dict: Time measurements for each algorithm and size
    """
    results = {'sizes': sizes, 'floyd_warshall': [], 'dijkstra_all': [], 'bellman_ford_all': []}
    
    for n in sizes:
        # Generate random graph
        G = nx.gnp_random_graph(n, density, directed=True)
        
        # Add random weights
        for u, v in G.edges():
            G[u][v]['weight'] = np.random.uniform(*weight_range)
        
        # Measure Floyd-Warshall
        fw = FloydWarshall()
        start_time = time.time()
        fw.run(G)
        fw_time = time.time() - start_time
        results['floyd_warshall'].append(fw_time)
        
        # Measure Dijkstra for all pairs
        start_time = time.time()
        for source in G.nodes():
            nx.single_source_dijkstra_path_length(G, source)
        dijkstra_time = time.time() - start_time
        results['dijkstra_all'].append(dijkstra_time)
        
        # Measure Bellman-Ford for all pairs
        start_time = time.time()
        for source in G.nodes():
            nx.single_source_bellman_ford_path_length(G, source)
        bf_time = time.time() - start_time
        results['bellman_ford_all'].append(bf_time)
    
    return results