"""
Logistics Optimization Package

This package provides a wrapper around Google OR-Tools for solving
Vehicle Routing Problems (VRP) with:
- Pickup and delivery constraints
- Vehicle capacity limits
- Maximum distance constraints
- Priority-based routing
- Multiple vehicle support

USAGE:
    from optimization import run_example_optimization
    result = run_example_optimization()

For API reference, see the docstrings in each module.
"""

from .models import (
    Location,
    Vehicle,
    Order,
    DistanceMatrix,
    RouteStop,
    VehicleRoute,
    OptimizationResult,
    NodeType
)

from .ortools_wrapper import (
    LogisticsOptimizer,
    calculate_euclidean_distance,
    calculate_haversine_distance,
    create_distance_matrix
)

from .example_usage import run_example_optimization, run_simple_test

__all__ = [
    # Data models
    "Location",
    "Vehicle",
    "Order",
    "DistanceMatrix",
    "RouteStop",
    "VehicleRoute",
    "OptimizationResult",
    "NodeType",
    
    # Optimizer
    "LogisticsOptimizer",
    "calculate_euclidean_distance",
    "calculate_haversine_distance",
    "create_distance_matrix",
    
    # Examples
    "run_example_optimization",
    "run_simple_test",
]
