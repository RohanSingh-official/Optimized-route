#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OpenStreetMap Integration Module

This module provides functions for fetching and processing geographic data
from OpenStreetMap using the OSMnx library.
"""

import osmnx as ox
import networkx as nx
import numpy as np
from geopy.geocoders import Nominatim
from sklearn.cluster import KMeans

# Configure OSMnx
# In OSMnx 2.0+, the config() method is replaced with settings object
ox.settings.use_cache = True
ox.settings.log_console = False

def geocode_location(location_name):
    """
    Geocode a location name to get its coordinates.
    
    Args:
        location_name (str): Name of the location to geocode
        
    Returns:
        tuple: (latitude, longitude) or None if geocoding fails
    """
    try:
        geolocator = Nominatim(user_agent="route_optimizer_app")
        location = geolocator.geocode(location_name)
        
        if location:
            return (location.latitude, location.longitude)
        return None
    except Exception as e:
        print(f"Geocoding error: {str(e)}")
        return None

def fetch_osm_graph(location, distance=1000, network_type="drive"):
    """
    Fetch a graph from OpenStreetMap for a given location.
    
    Args:
        location (str or tuple): Location name or (latitude, longitude) coordinates
        distance (int): Distance in meters to fetch around the location
        network_type (str): Type of network to fetch (drive, walk, bike, all)
        
    Returns:
        networkx.Graph: Graph representation of the road network
    """
    try:
        # If location is a string, geocode it
        if isinstance(location, str):
            coords = geocode_location(location)
            if not coords:
                raise ValueError(f"Could not geocode location: {location}")
        else:
            coords = location
            
        # Fetch graph from OSM
        # In OSMnx 2.0+, parameters have changed
        G = ox.graph_from_point(
            coords,
            dist=distance,
            dist_type='network',  # In OSMnx 2.0+, dist_type is required
            network_type=network_type,
            simplify=True
        )
        
        # Convert to undirected graph for Floyd-Warshall algorithm
        if G.is_directed():
            G = G.to_undirected()
        
        # Get largest connected component
        largest_cc = max(nx.connected_components(G), key=len)
        G = G.subgraph(largest_cc).copy()
        
        return G
    except Exception as e:
        print(f"Error fetching OSM graph: {str(e)}")
        raise

def simplify_graph(G, max_nodes=50):
    """
    Simplify a graph by reducing the number of nodes using clustering.
    
    Args:
        G (networkx.Graph): Input graph
        max_nodes (int): Maximum number of nodes in the simplified graph
        
    Returns:
        networkx.Graph: Simplified graph
    """
    if len(G.nodes) <= max_nodes:
        return G
    
    try:
        # Extract node coordinates
        coords = np.array([(data['y'], data['x']) for _, data in G.nodes(data=True)])
        
        # Apply k-means clustering
        kmeans = KMeans(n_clusters=max_nodes, random_state=0).fit(coords)
        
        # Create a new graph with cluster centers
        simplified_G = nx.Graph()
        
        # Add nodes (cluster centers)
        for i, center in enumerate(kmeans.cluster_centers_):
            simplified_G.add_node(f"Node {i}", y=center[0], x=center[1])
        
        # Add edges between nearby clusters
        for i in range(len(kmeans.cluster_centers_)):
            for j in range(i+1, len(kmeans.cluster_centers_)):
                # Calculate Euclidean distance
                dist = np.linalg.norm(kmeans.cluster_centers_[i] - kmeans.cluster_centers_[j])
                if dist < 0.01:  # Add edge if clusters are close
                    simplified_G.add_edge(f"Node {i}", f"Node {j}", weight=dist*100000)  # Convert to meters
        
        return simplified_G
    except Exception as e:
        print(f"Error simplifying graph: {str(e)}")
        return G

def get_node_coordinates(G):
    """
    Extract node coordinates from a graph.
    
    Args:
        G (networkx.Graph): Input graph
        
    Returns:
        dict: Dictionary mapping node IDs to (x, y) coordinates
    """
    return {node: (data['x'], data['y']) for node, data in G.nodes(data=True) if 'x' in data and 'y' in data}

def calculate_path_length(G, path):
    """
    Calculate the total length of a path in a graph.
    
    Args:
        G (networkx.Graph): Input graph
        path (list): List of nodes in the path
        
    Returns:
        float: Total path length
    """
    if not path or len(path) < 2:
        return 0.0
    
    total_length = 0.0
    for i in range(len(path) - 1):
        u, v = path[i], path[i+1]
        if G.has_edge(u, v) and 'weight' in G[u][v]:
            total_length += G[u][v]['weight']
    
    return total_length