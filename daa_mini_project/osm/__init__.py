#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OpenStreetMap integration package

This package provides integration with OpenStreetMap API for fetching
geographic data and creating graph representations of road networks.
"""

from .integration import fetch_osm_graph, geocode_location, simplify_graph

__all__ = ['fetch_osm_graph', 'geocode_location', 'simplify_graph']