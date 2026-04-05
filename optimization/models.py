"""
Data models for the logistics optimization problem.
These models represent the core entities in the routing problem.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class NodeType(Enum):
    """Types of nodes in the logistics network"""
    DEPOT = "depo"                    # Starting point for vehicles (warehouse)
    SUPPLIER = "postachalnyk"         # Where goods are picked up
    DELIVERY_POINT = "tochka_vygruzky" # Where goods are delivered
    HOTSPOT = "hotspot"               # Special locations (urgent, priority)


@dataclass
class Location:
    """Represents a physical location with coordinates"""
    id: int
    name: str
    x: float  # X coordinate (or longitude)
    y: float  # Y coordinate (or latitude)
    type: NodeType
    service_time_sec: float = 0.0
    time_window_start: Optional[float] = None
    time_window_end: Optional[float] = None
    
    def __post_init__(self):
        if not isinstance(self.type, NodeType):
            try:
                self.type = NodeType(self.type)
            except ValueError:
                valid = [nt.value for nt in NodeType]
                raise ValueError(
                    f"Location '{self.name}' (id={self.id}): invalid type '{self.type}'. "
                    f"Valid types: {valid}"
                )
        # Validate coordinates
        import math
        if math.isnan(self.x) or math.isnan(self.y):
            raise ValueError(
                f"Location '{self.name}' (id={self.id}): coordinates contain NaN "
                f"(x={self.x}, y={self.y})"
            )
        if math.isinf(self.x) or math.isinf(self.y):
            raise ValueError(
                f"Location '{self.name}' (id={self.id}): coordinates contain Inf "
                f"(x={self.x}, y={self.y})"
            )


@dataclass
class Order:
    """Represents a delivery order with volume requirements"""
    id: int
    from_location_id: int  # Supplier location
    to_location_id: int    # Delivery point location
    volume: float          # Volume of goods (cubic meters)
    weight: float = 0.0    # Weight of goods (kg)
    priority: int = 1      # Priority level (1=normal, 2=high, 3=urgent)
    time_window_start: Optional[float] = None  # Earliest delivery time
    time_window_end: Optional[float] = None    # Latest delivery time

    def __post_init__(self):
        if self.volume < 0:
            raise ValueError(
                f"Order {self.id}: volume cannot be negative (got {self.volume})"
            )
        if self.weight < 0:
            raise ValueError(
                f"Order {self.id}: weight cannot be negative (got {self.weight})"
            )
        if self.priority < 0:
            raise ValueError(
                f"Order {self.id}: priority cannot be negative (got {self.priority})"
            )


@dataclass
class Vehicle:
    """Represents a delivery vehicle with capacity constraints"""
    id: int
    depot_id: int          # Starting/ending depot
    capacity: float        # Maximum volume the vehicle can carry
    max_distance: float    # Maximum distance the vehicle can travel (km)
    weight_capacity: float = float('inf')  # Maximum weight (kg)
    start_depot_id: Optional[int] = None   # Where the vehicle shifts starts
    end_depot_id: Optional[int] = None     # Where the vehicle returns
    speed_kmh: float = 50.0  # Average speed for timing estimation
    cost_per_km: float = 1.0  # Operating cost per kilometer
    current_load: float = 0.0   # Current load (used during solving)
    current_distance: float = 0.0  # Current distance traveled

    def __post_init__(self):
        # Default start/end to single depot if not provided
        if self.start_depot_id is None:
            self.start_depot_id = self.depot_id
        if self.end_depot_id is None:
            self.end_depot_id = self.depot_id


@dataclass
class DistanceMatrix:
    """Stores pre-calculated distances between all locations"""
    locations: List[Location]
    matrix: List[List[float]]  # matrix[i][j] = distance from location i to j
    durations: List[List[float]] = field(default_factory=list) # Time in seconds from i to j
    
    def get_distance(self, from_id: int, to_id: int) -> float:
        """Get distance between two location IDs"""
        from_index = next(
            (i for i, loc in enumerate(self.locations) if loc.id == from_id),
            None
        )
        if from_index is None:
            known_ids = [loc.id for loc in self.locations]
            raise ValueError(
                f"Location ID {from_id} not found in distance matrix. "
                f"Known IDs: {known_ids}"
            )
        to_index = next(
            (i for i, loc in enumerate(self.locations) if loc.id == to_id),
            None
        )
        if to_index is None:
            known_ids = [loc.id for loc in self.locations]
            raise ValueError(
                f"Location ID {to_id} not found in distance matrix. "
                f"Known IDs: {known_ids}"
            )
        return self.matrix[from_index][to_index]

    def get_duration(self, from_id: int, to_id: int) -> float:
        """Get transit time (seconds) between two location IDs"""
        if not self.durations:
            return 0.0
            
        from_index = next((i for i, loc in enumerate(self.locations) if loc.id == from_id), None)
        to_index = next((i for i, loc in enumerate(self.locations) if loc.id == to_id), None)
        
        if from_index is not None and to_index is not None:
            return self.durations[from_index][to_index]
        return 0.0


@dataclass
class RouteStop:
    """A single stop in a vehicle's route"""
    location_id: int
    location_type: NodeType
    order_id: Optional[int]  # Order being fulfilled (if applicable)
    volume_loaded: float = 0.0    # Volume picked up at this stop
    volume_unloaded: float = 0.0  # Volume delivered at this stop
    weight_loaded: float = 0.0    # Weight picked up at this stop
    weight_unloaded: float = 0.0  # Weight delivered at this stop
    arrival_distance: float = 0.0  # Cumulative distance when arriving
    arrival_time: float = 0.0     # Expected arrival time at stop
    departure_time: float = 0.0   # Expected departure after service


@dataclass
class VehicleRoute:
    """Complete route for a single vehicle"""
    vehicle_id: int
    stops: List[RouteStop] = field(default_factory=list)
    total_distance: float = 0.0
    total_load: float = 0.0
    is_feasible: bool = True
    constraint_violations: List[str] = field(default_factory=list)
    
    def add_stop(self, stop: RouteStop):
        """Add a stop to the route"""
        self.stops.append(stop)
    
    def calculate_totals(self):
        """Calculate total distance and load for this route"""
        if len(self.stops) >= 2:
            self.total_distance = self.stops[-1].arrival_distance
        self.total_load = max(stop.volume_loaded for stop in self.stops) if self.stops else 0


@dataclass
class OptimizationResult:
    """Complete result of the optimization"""
    routes: List[VehicleRoute]
    total_distance: float
    total_vehicles_used: int
    is_feasible: bool
    unserved_orders: List[int]  # Orders that couldn't be served
    computation_time_ms: float
    constraint_violations: List[str] = field(default_factory=list)
    
    def summary(self) -> str:
        """Print a human-readable summary"""
        lines = [
            "=" * 60,
            "OPTIMIZATION RESULT SUMMARY",
            "=" * 60,
            f"Total Distance: {self.total_distance:.2f} km",
            f"Vehicles Used: {self.total_vehicles_used}",
            f"Feasible Solution: {'Yes' if self.is_feasible else 'No'}",
            f"Unserved Orders: {len(self.unserved_orders)}",
            f"Computation Time: {self.computation_time_ms:.2f} ms",
        ]
        
        if self.constraint_violations:
            lines.append("\nConstraint Violations:")
            for violation in self.constraint_violations:
                lines.append(f"  - {violation}")
        
        lines.append("\n" + "=" * 60)
        lines.append("VEHICLE ROUTES")
        lines.append("=" * 60)
        
        for route in self.routes:
            if route.stops:
                lines.append(f"\nVehicle {route.vehicle_id}:")
                lines.append(f"  Distance: {route.total_distance:.2f} km")
                lines.append(f"  Max Load: {route.total_load:.2f}")
                lines.append(f"  Stops: {len(route.stops)}")
                
                if route.constraint_violations:
                    lines.append(f"  VIOLATIONS: {', '.join(route.constraint_violations)}")
                
                lines.append("  Route:")
                for i, stop in enumerate(route.stops):
                    lines.append(
                        f"    {i+1}. {stop.location_type.value} "
                        f"(ID: {stop.location_id})"
                        f"{f' [Order #{stop.order_id}]' if stop.order_id else ''}"
                    )
        
        return "\n".join(lines)
