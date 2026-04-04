"""
Core OR-Tools wrapper for solving the Vehicle Routing Problem (VRP)
with capacity constraints and distance limits.

This module implements:
- Capacity constraints (vehicle volume limits)
- Distance constraints (maximum route length)
- Multiple vehicle types
- Priority-based delivery
- Pickup and delivery pairs
"""

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import time
from typing import List, Tuple, Optional
import math
import asyncio
import json
import urllib.request
import urllib.error

from .models import (
    Location, Vehicle, Order, DistanceMatrix, 
    VehicleRoute, RouteStop, OptimizationResult, NodeType
)


class LogisticsOptimizer:
    """
    Main wrapper class for Google OR-Tools routing solver.
    
    This class handles:
    1. Setting up the routing problem
    2. Adding capacity and distance constraints
    3. Solving the optimization
    4. Extracting and interpreting results
    """
    
    def __init__(
        self,
        locations: List[Location],
        vehicles: List[Vehicle],
        orders: List[Order],
        distance_matrix: DistanceMatrix
    ):
        """
        Initialize the optimizer with problem data.
        
        Args:
            locations: All locations (depots, suppliers, delivery points)
            vehicles: Available vehicles with their capacities
            orders: Orders to be fulfilled (supplier -> delivery)
            distance_matrix: Pre-calculated distances between locations
        """
        self.locations = locations
        self.vehicles = vehicles
        self.orders = orders
        self.distance_matrix = distance_matrix
        
        # Map location IDs to indices for OR-Tools
        self.location_id_to_index = {}
        for idx, loc in enumerate(locations):
            if loc.id in self.location_id_to_index:
                prev_idx = self.location_id_to_index[loc.id]
                raise ValueError(
                    f"Duplicate location ID {loc.id}: "
                    f"'{locations[prev_idx].name}' (index {prev_idx}) and "
                    f"'{loc.name}' (index {idx})"
                )
            self.location_id_to_index[loc.id] = idx
        
        # Validate that all order location references exist
        known_ids = set(self.location_id_to_index.keys())
        for order in orders:
            if order.from_location_id not in known_ids:
                raise ValueError(
                    f"Order {order.id}: from_location_id={order.from_location_id} "
                    f"not found in locations. Known IDs: {sorted(known_ids)}"
                )
            if order.to_location_id not in known_ids:
                raise ValueError(
                    f"Order {order.id}: to_location_id={order.to_location_id} "
                    f"not found in locations. Known IDs: {sorted(known_ids)}"
                )
        
        # Validate that all vehicle depot references exist
        for vehicle in vehicles:
            if vehicle.depot_id not in known_ids:
                raise ValueError(
                    f"Vehicle {vehicle.id}: depot_id={vehicle.depot_id} "
                    f"not found in locations. Known IDs: {sorted(known_ids)}"
                )
        
        # Create OR-Tools routing manager and model
        self.manager = None
        self.routing = None
        
    def _calculate_distance(self, from_index: int, to_index: int) -> float:
        """
        Calculate distance between two indices in the location list.
        This is the callback function OR-Tools uses for distance calculations.
        
        Args:
            from_index: Index of starting location
            to_index: Index of ending location
            
        Returns:
            Distance between the two locations
        """
        from_loc = self.locations[from_index]
        to_loc = self.locations[to_index]
        return self.distance_matrix.get_distance(from_loc.id, to_loc.id)
    
    def _create_distance_matrix_callback(self):
        """
        Create a callback function for OR-Tools that returns distances.
        OR-Tools requires distances as integers (multiply by 1000 for precision).
        """
        def distance_callback(from_index, to_index):
            # Convert from variable indices to location indices
            from_node = self.manager.IndexToNode(from_index)
            to_node = self.manager.IndexToNode(to_index)
            distance = self._calculate_distance(from_node, to_node)
            # Return as integer (meters) for OR-Tools
            return int(distance * 1000)
        
        return distance_callback
    
    def _setup_pickup_delivery_pairs(self, orders: List[Order]):
        """
        Set up pickup and delivery constraints.
        Each order requires: pickup at supplier -> delivery at delivery point.
        """
        for order in orders:
            pickup_index = self.location_id_to_index[order.from_location_id]
            delivery_index = self.location_id_to_index[order.to_location_id]

            pickup_node = self.manager.NodeToIndex(pickup_index)
            delivery_node = self.manager.NodeToIndex(delivery_index)

            # Enforce pickup before delivery
            self.routing.AddPickupAndDelivery(pickup_node, delivery_node)

            # Same vehicle must handle both pickup and delivery
            self.routing.solver().Add(
                self.routing.VehicleVar(pickup_node) ==
                self.routing.VehicleVar(delivery_node)
            )
    
    def _setup_capacity_constraints(self, order_demand: dict):
        """
        Set up vehicle capacity constraints.
        Ensures total volume loaded doesn't exceed vehicle capacity.
        
        Args:
            order_demand: Dict mapping location index to volume demand
        """
        capacity_dimension_name = "capacity"
        
        def demand_callback(from_index):
            from_node = self.manager.IndexToNode(from_index)
            return int(order_demand.get(from_node, 0) * 1000)  # Scale for precision
        
        demand_callback_index = self.routing.RegisterUnaryTransitCallback(demand_callback)
        
        # Use the method that takes a single callback with vehicle capacities
        self.routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # No slack (can't exceed capacity at any point)
            [int(v.capacity * 1000) for v in self.vehicles],  # Vehicle capacities
            True,  # Start cumul at zero
            capacity_dimension_name
        )
        
        # Get the capacity dimension
        capacity_dimension = self.routing.GetDimensionOrDie(capacity_dimension_name)
        
        # Try to minimize capacity usage
        capacity_dimension.SetGlobalSpanCostCoefficient(0)  # Don't penalize
    
    def _setup_distance_constraints(self, transit_callback_index: int):
        """
        Set up maximum distance constraints for each vehicle.
        Ensures no vehicle exceeds its maximum allowed distance.
        
        Args:
            transit_callback_index: The already-registered transit callback index
        """
        distance_dimension_name = "distance"
        
        # Use global max as upper bound, then constrain per-vehicle below
        global_max = int(max(v.max_distance for v in self.vehicles) * 1000)
        
        self.routing.AddDimension(
            transit_callback_index,
            0,          # No slack
            global_max, # Global upper bound
            True,       # Start cumul at zero
            distance_dimension_name
        )
        
        distance_dimension = self.routing.GetDimensionOrDie(distance_dimension_name)
        
        # Set per-vehicle max distance via end cumul bounds
        for vehicle_idx, vehicle in enumerate(self.vehicles):
            end_index = self.routing.End(vehicle_idx)
            distance_dimension.CumulVar(end_index).SetMax(
                int(vehicle.max_distance * 1000)
            )
        
        # Minimize total distance
        distance_dimension.SetGlobalSpanCostCoefficient(100)

    def _setup_weight_constraints(self, order_weight: dict):
        """
        Set up vehicle weight constraints.
        Ensures total weight loaded doesn't exceed vehicle weight capacity.
        """
        weight_dimension_name = "weight"
        
        def weight_callback(from_index):
            from_node = self.manager.IndexToNode(from_index)
            return int(order_weight.get(from_node, 0) * 1000)
            
        weight_callback_index = self.routing.RegisterUnaryTransitCallback(weight_callback)
        
        caps = []
        for v in self.vehicles:
            c = v.weight_capacity 
            # Or-Tools requires ints; if inf, assign a suitably large integer
            caps.append(int(c * 1000) if c != float('inf') else 2**60)
            
        self.routing.AddDimensionWithVehicleCapacity(
            weight_callback_index,
            0,  # No slack
            caps,
            True,  # Start cumul at zero
            weight_dimension_name
        )

    def _create_time_callback(self):
        """
        Create a time callback incorporating travel time and service time.
        If we don't have OSRM durations, estimate using transit distances.
        """
        def time_callback(from_index, to_index):
            from_node = self.manager.IndexToNode(from_index)
            to_node = self.manager.IndexToNode(to_index)
            
            # Service time
            service_time = int(self.locations[from_node].service_time_sec)
            
            # Travel time
            travel_time = int(self.distance_matrix.get_duration(
                self.locations[from_node].id, self.locations[to_node].id
            ))
            
            # Fallback to speed estimation if duration matrix is empty
            if travel_time == 0:
                dist_km = self._calculate_distance(from_node, to_node)
                # Fallback purely assuming 50 km/h: (km / 50.0) * 3600
                travel_time = int((dist_km / 50.0) * 3600)
                
            return travel_time + service_time
            
        return time_callback

    def _setup_time_windows(self):
        """Setup time bounds for locations or orders"""
        time_callback = self._create_time_callback()
        time_callback_index = self.routing.RegisterTransitCallback(time_callback)
        
        time_dimension_name = "Time"
        
        # Max 24 hours per route slack (waiting time), Max total time 1 week
        self.routing.AddDimension(
            time_callback_index,
            86400,  # allow waiting time
            86400 * 7, # large maximum time
            False, # start cumul NOT necessarily zero
            time_dimension_name
        )
        
        time_dimension = self.routing.GetDimensionOrDie(time_dimension_name)
        
        # Apply time windows to locations
        for location_idx, location in enumerate(self.locations):
            if location.time_window_start is None and location.time_window_end is None:
                continue
                
            index = self.manager.NodeToIndex(location_idx)
            if index == -1:
                continue
                
            start = int(location.time_window_start if location.time_window_start is not None else 0)
            end = int(location.time_window_end if location.time_window_end is not None else 86400 * 7)
            
            time_dimension.CumulVar(index).SetRange(start, end)
            
        # Apply strict delivery time windows to orders
        for order in self.orders:
            if order.time_window_start is not None or order.time_window_end is not None:
                delivery_index = self.manager.NodeToIndex(self.location_id_to_index[order.to_location_id])
                if delivery_index != -1:
                    start = int(order.time_window_start if order.time_window_start is not None else 0)
                    end = int(order.time_window_end if order.time_window_end is not None else 86400 * 7)
                    time_dimension.CumulVar(delivery_index).SetRange(start, end)
    
    def _setup_priority_costs(self, orders: List[Order]):
        """
        Set up priority-based routing costs.
        Higher priority orders get visited earlier.
        """
        # Add penalty for unserved high-priority orders
        for order in orders:
            delivery_index = self.location_id_to_index[order.to_location_id]
            delivery_node = self.manager.NodeToIndex(delivery_index)
            
            # Higher penalty for higher priority orders
            penalty = order.priority * 100000
            self.routing.AddDisjunction([delivery_node], penalty)
    
    def _extract_solution(self, solution) -> OptimizationResult:
        """
        Extract and format the solution from OR-Tools.
        
        Args:
            solution: OR-Tools solution object
            
        Returns:
            Formatted OptimizationResult
        """
        routes = []
        total_distance = 0.0
        total_vehicles_used = 0
        unserved_orders = []
        all_violations = []
        
        # Check each vehicle's route
        for vehicle_idx, vehicle in enumerate(self.vehicles):
            route = VehicleRoute(vehicle_id=vehicle.id)
            index = self.routing.Start(vehicle_idx)
            
            capacity_dimension = self.routing.GetDimensionOrDie("capacity")
            distance_dimension = self.routing.GetDimensionOrDie("distance")
            weight_dimension = self.routing.GetDimensionOrDie("weight")
            time_dimension = self.routing.GetDimensionOrDie("Time")
            
            route_distance = 0.0
            max_load = 0.0
            max_weight = 0.0
            
            while not self.routing.IsEnd(index):
                node_index = self.manager.IndexToNode(index)
                location = self.locations[node_index]
                
                # Get cumulative values
                load_var = capacity_dimension.CumulVar(index)
                load = solution.Value(load_var) / 1000.0
                max_load = max(max_load, load)
                
                distance_var = distance_dimension.CumulVar(index)
                distance = solution.Value(distance_var) / 1000.0
                
                # Time
                time_var = time_dimension.CumulVar(index)
                arrival_time = solution.Value(time_var)
                
                # Weight
                weight_var = weight_dimension.CumulVar(index)
                curr_wt = solution.Value(weight_var) / 1000.0
                max_weight = max(max_weight, curr_wt)

                # Determine if this is part of an order
                order_id = None
                volume_unloaded = 0.0
                volume_loaded = 0.0
                weight_unloaded = 0.0
                weight_loaded = 0.0
                
                for order in self.orders:
                    if self.location_id_to_index[order.to_location_id] == node_index:
                        order_id = order.id
                        volume_unloaded = order.volume
                        weight_unloaded = order.weight
                    if self.location_id_to_index[order.from_location_id] == node_index:
                        order_id = order.id
                        volume_loaded = order.volume
                        weight_loaded = order.weight
                
                stop = RouteStop(
                    location_id=location.id,
                    location_type=location.type,
                    order_id=order_id,
                    volume_loaded=volume_loaded,
                    volume_unloaded=volume_unloaded,
                    weight_loaded=weight_loaded,
                    weight_unloaded=weight_unloaded,
                    arrival_distance=distance,
                    arrival_time=arrival_time,
                    departure_time=arrival_time + location.service_time_sec
                )
                
                route.add_stop(stop)
                route_distance = distance
                
                # Move to next node
                index = solution.Value(self.routing.NextVar(index))
            
            # Add end depot
            end_node = self.manager.IndexToNode(index)
            end_location = self.locations[end_node]
            end_distance = solution.Value(distance_dimension.CumulVar(index)) / 1000.0
            end_arrival_time = solution.Value(time_dimension.CumulVar(index))
            
            route.add_stop(RouteStop(
                location_id=end_location.id,
                location_type=end_location.type,
                order_id=None,
                arrival_distance=end_distance,
                arrival_time=end_arrival_time,
                departure_time=end_arrival_time
            ))
            
            route.total_distance = end_distance
            route.total_load = max_load
            
            # Check constraints
            if route.total_distance > vehicle.max_distance:
                route.is_feasible = False
                route.constraint_violations.append(
                    f"Distance exceeded: {route.total_distance:.2f} > {vehicle.max_distance}"
                )
                all_violations.extend(route.constraint_violations)
            
            if route.total_load > vehicle.capacity:
                route.is_feasible = False
                route.constraint_violations.append(
                    f"Capacity exceeded: {route.total_load:.2f} > {vehicle.capacity}"
                )
                all_violations.extend(route.constraint_violations)
            
            if route.stops:  # Only count if vehicle was used
                total_distance += route.total_distance
                total_vehicles_used += 1
            
            routes.append(route)
        
        # Find unserved orders
        served_order_ids = {
            stop.order_id for route in routes for stop in route.stops 
            if stop.order_id is not None and stop.volume_unloaded > 0
        }
        
        for order in self.orders:
            if order.id not in served_order_ids:
                unserved_orders.append(order.id)
        
        is_feasible = len(all_violations) == 0 and len(unserved_orders) == 0
        
        return OptimizationResult(
            routes=routes,
            total_distance=total_distance,
            total_vehicles_used=total_vehicles_used,
            is_feasible=is_feasible,
            unserved_orders=unserved_orders,
            computation_time_ms=0,  # Will be set by solve method
            constraint_violations=all_violations
        )
    
    async def solve_async(
        self,
        time_limit_seconds: int = 30,
        first_solution_strategy: str = "PATH_CHEAPEST_ARC",
        local_search_metaheuristic: str = "GUIDED_LOCAL_SEARCH"
    ) -> OptimizationResult:
        """Asynchronous wrapper for solve() to unblock web frameworks."""
        return await asyncio.to_thread(
            self.solve,
            time_limit_seconds,
            first_solution_strategy,
            local_search_metaheuristic
        )

    def solve(
        self,
        time_limit_seconds: int = 30,
        first_solution_strategy: str = "PATH_CHEAPEST_ARC",
        local_search_metaheuristic: str = "GUIDED_LOCAL_SEARCH"
    ) -> OptimizationResult:
        """
        Solve the vehicle routing problem.
        
        Args:
            time_limit_seconds: Maximum solving time
            first_solution_strategy: Strategy for initial solution
            local_search_metaheuristic: Metaheuristic for improvement
            
        Returns:
            OptimizationResult with routes and statistics
        """
        start_time = time.time()
        
        # Calculate order demands (volume loaded at suppliers)
        # Use += to accumulate when multiple orders share a supplier
        order_demand = {}
        order_weight = {}
        for order in self.orders:
            supplier_index = self.location_id_to_index[order.from_location_id]
            order_demand[supplier_index] = order_demand.get(supplier_index, 0) + order.volume
            order_weight[supplier_index] = order_weight.get(supplier_index, 0) + order.weight
        
        # Create the routing index manager
        num_locations = len(self.locations)
        num_vehicles = len(self.vehicles)

        if num_vehicles == 0:
            return OptimizationResult(
                routes=[],
                total_distance=0.0,
                total_vehicles_used=0,
                is_feasible=False,
                unserved_orders=[order.id for order in self.orders],
                computation_time_ms=0.0,
                constraint_violations=["No vehicles available to route"]
            )

        # Separate start and end indices
        starts = [
            self.location_id_to_index[v.start_depot_id] for v in self.vehicles
        ]
        ends = [
            self.location_id_to_index[v.end_depot_id] for v in self.vehicles
        ]

        self.manager = pywrapcp.RoutingIndexManager(
            num_locations,
            num_vehicles,
            starts,
            ends
        )
        
        self.routing = pywrapcp.RoutingModel(self.manager)
        
        # Setup distance callback
        transit_callback = self._create_distance_matrix_callback()
        transit_callback_index = self.routing.RegisterTransitCallback(transit_callback)
        self.routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        
        # Setup pickup and delivery constraints
        self._setup_pickup_delivery_pairs(self.orders)
        
        # Setup capacity constraints
        self._setup_capacity_constraints(order_demand)
        self._setup_weight_constraints(order_weight)
        
        # Setup distance constraints (reuse the transit callback)
        self._setup_distance_constraints(transit_callback_index)

        # Setup time windows
        self._setup_time_windows()
        
        # Setup priority costs (optional, comment out if not needed)
        # self._setup_priority_costs(self.orders)
        
        # Set search parameters
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        
        # First solution heuristic
        first_solution_strategies = {
            "PATH_CHEAPEST_ARC": routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC,
            "PATH_MOST_CONSTRAINED_ARC": routing_enums_pb2.FirstSolutionStrategy.PATH_MOST_CONSTRAINED_ARC,
            "PARALLEL_CHEAPEST_INSERTION": routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION,
            "SAVINGS": routing_enums_pb2.FirstSolutionStrategy.SAVINGS,
            "SWEEP": routing_enums_pb2.FirstSolutionStrategy.SWEEP,
        }
        search_parameters.first_solution_strategy = first_solution_strategies.get(
            first_solution_strategy,
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        
        # Local search metaheuristic
        metaheuristics = {
            "GUIDED_LOCAL_SEARCH": routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH,
            "SIMULATED_ANNEALING": routing_enums_pb2.LocalSearchMetaheuristic.SIMULATED_ANNEALING,
            "TABU_SEARCH": routing_enums_pb2.LocalSearchMetaheuristic.TABU_SEARCH,
        }
        # Disable metaheuristic for faster solving
        search_parameters.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.AUTOMATIC
        
        # Time limit
        search_parameters.time_limit.FromSeconds(time_limit_seconds)
        
        # Don't look for multiple solutions - just get first feasible
        # search_parameters.solution_limit = 1  # Comment out - may not be compatible
        
        # Solve the problem
        solution = self.routing.SolveWithParameters(search_parameters)
        
        end_time = time.time()
        computation_time_ms = (end_time - start_time) * 1000
        
        # Extract and return solution
        if solution:
            result = self._extract_solution(solution)
            result.computation_time_ms = computation_time_ms
            return result
        else:
            # No solution found
            return OptimizationResult(
                routes=[],
                total_distance=0.0,
                total_vehicles_used=0,
                is_feasible=False,
                unserved_orders=[order.id for order in self.orders],
                computation_time_ms=computation_time_ms,
                constraint_violations=["No feasible solution found within time limit"]
            )


def calculate_euclidean_distance(loc1: Location, loc2: Location) -> float:
    """
    Calculate Euclidean distance between two locations.
    Use for local/flat coordinate systems (not GPS).
    
    Args:
        loc1: First location
        loc2: Second location
        
    Returns:
        Euclidean distance in coordinate units
    """
    return math.sqrt((loc1.x - loc2.x)**2 + (loc1.y - loc2.y)**2)


def calculate_haversine_distance(loc1: Location, loc2: Location) -> float:
    """
    Calculate the great-circle distance between two GPS points using the 
    Haversine formula. Treats loc.x as longitude, loc.y as latitude.
    
    Args:
        loc1: First location (x=longitude, y=latitude in degrees)
        loc2: Second location (x=longitude, y=latitude in degrees)
        
    Returns:
        Distance in kilometers
    """
    R = 6371.0  # Earth's radius in km
    
    lat1 = math.radians(loc1.y)
    lat2 = math.radians(loc2.y)
    dlat = math.radians(loc2.y - loc1.y)
    dlon = math.radians(loc2.x - loc1.x)
    
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def create_distance_matrix(
    locations: List[Location], 
    use_haversine: bool = True
) -> DistanceMatrix:
    """
    Create a distance matrix from locations.
    
    By default uses Haversine (GPS coordinates: x=longitude, y=latitude).
    Set use_haversine=False for flat/local coordinate systems.
    
    Args:
        locations: List of all locations
        use_haversine: If True, use Haversine (km). If False, use Euclidean.
        
    Returns:
        DistanceMatrix object
    """
    dist_fn = calculate_haversine_distance if use_haversine else calculate_euclidean_distance
    
    n = len(locations)
    matrix = [[0.0] * n for _ in range(n)]
    
    for i in range(n):
        for j in range(n):
            if i != j:
                matrix[i][j] = dist_fn(locations[i], locations[j])
    
    return DistanceMatrix(locations=locations, matrix=matrix)


def create_osrm_distance_matrix(locations: List[Location]) -> DistanceMatrix:
    """
    Calls public OSRM mapping server to get real driving distances and durations.
    Max 100 locations recommended.
    """
    if not locations:
        return DistanceMatrix(locations=[], matrix=[], durations=[])
        
    coords = ";".join(f"{loc.x},{loc.y}" for loc in locations)
    url = f"http://router.project-osrm.org/table/v1/driving/{coords}?annotations=distance,duration"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'StrongLogisticsApp/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        if data.get("code") != "Ok":
            raise ValueError(f"OSRM Error: {data.get('code')}")
            
        distances = data.get("distances", []) # Meters
        durations = data.get("durations", []) # Seconds
        
        n = len(locations)
        matrix = [[0.0] * n for _ in range(n)]
        dur_matrix = [[0.0] * n for _ in range(n)]
        
        for i in range(n):
            for j in range(n):
                if distances and i < len(distances) and j < len(distances[i]):
                    val = distances[i][j]
                    matrix[i][j] = val / 1000.0 if val is not None else 0.0
                if durations and i < len(durations) and j < len(durations[i]):
                    dval = durations[i][j]
                    dur_matrix[i][j] = float(dval) if dval is not None else 0.0
                    
        return DistanceMatrix(locations=locations, matrix=matrix, durations=dur_matrix)
        
    except Exception as e:
        print(f"Warning: OSRM request failed ({e}). Falling back to Haversine.")
        return create_distance_matrix(locations, use_haversine=True)

