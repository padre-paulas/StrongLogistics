"""
Example usage of the OR-Tools logistics optimizer.
This demonstrates how to set up and solve a vehicle routing problem
with depots, suppliers, delivery points, and capacity constraints.
"""

import sys
import os

# Allow direct execution without module errors
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from optimization.models import Location, Vehicle, Order, NodeType
    from optimization.ortools_wrapper import LogisticsOptimizer, create_distance_matrix
except ImportError:
    from .models import Location, Vehicle, Order, NodeType
    from .ortools_wrapper import LogisticsOptimizer, create_distance_matrix


def run_example_optimization():
    """
    Complete example showing how to use the optimization wrapper.
    
    Scenario:
    - 1 depot (warehouse where vehicles start)
    - 2 suppliers (where goods are picked up)
    - 4 delivery points (where goods are delivered)
    - 2 vehicles with different capacities
    - Each order: pickup at supplier -> deliver to customer
    """
    
    print("=" * 70)
    print("LOGISTICS OPTIMIZATION EXAMPLE")
    print("=" * 70)
    
    # =====================================================================
    # STEP 1: Define Locations
    # =====================================================================
    print("\n1. Defining locations...")
    
    locations = [
        # Depot (warehouse) - vehicles start and end here
        Location(id=0, name="Main Depot", x=50.0, y=50.0, type=NodeType.DEPOT),
        
        # Suppliers (where goods are picked up)
        Location(id=1, name="Supplier A", x=20.0, y=30.0, type=NodeType.SUPPLIER),
        Location(id=2, name="Supplier B", x=70.0, y=20.0, type=NodeType.SUPPLIER),
        
        # Hotspot (priority location)
        Location(id=3, name="Hotspot Zone", x=40.0, y=60.0, type=NodeType.HOTSPOT),
        
        # Delivery points (where goods are delivered)
        Location(id=4, name="Customer 1", x=10.0, y=10.0, type=NodeType.DELIVERY_POINT),
        Location(id=5, name="Customer 2", x=80.0, y=50.0, type=NodeType.DELIVERY_POINT),
        Location(id=6, name="Customer 3", x=30.0, y=70.0, type=NodeType.DELIVERY_POINT),
        Location(id=7, name="Customer 4", x=60.0, y=40.0, type=NodeType.DELIVERY_POINT),
    ]
    
    for loc in locations:
        print(f"   - {loc.name} (ID: {loc.id}, Type: {loc.type.value})")
    
    # =====================================================================
    # STEP 2: Define Orders
    # =====================================================================
    print("\n2. Defining orders...")
    
    orders = [
        # Order 1: Pick up from Supplier A, deliver to Customer 1
        Order(
            id=101,
            from_location_id=1,  # Supplier A
            to_location_id=4,    # Customer 1
            volume=5.0,          # 5 cubic meters
            priority=1           # Normal priority
        ),
        
        # Order 2: Pick up from Supplier A, deliver to Customer 2
        Order(
            id=102,
            from_location_id=1,  # Supplier A
            to_location_id=5,    # Customer 2
            volume=8.0,
            priority=2           # High priority
        ),
        
        # Order 3: Pick up from Supplier B, deliver to Customer 3
        Order(
            id=103,
            from_location_id=2,  # Supplier B
            to_location_id=6,    # Customer 3
            volume=6.0,
            priority=1
        ),
        
        # Order 4: Pick up from Supplier B, deliver to Hotspot
        Order(
            id=104,
            from_location_id=2,  # Supplier B
            to_location_id=3,    # Hotspot Zone
            volume=10.0,
            priority=3           # Urgent!
        ),
        
        # Order 5: Pick up from Supplier A, deliver to Customer 4
        Order(
            id=105,
            from_location_id=1,  # Supplier A
            to_location_id=7,    # Customer 4
            volume=4.0,
            priority=1
        ),
    ]
    
    for order in orders:
        print(f"   - Order #{order.id}: Supplier {order.from_location_id} -> "
              f"Customer {order.to_location_id}, Volume: {order.volume}m³, "
              f"Priority: {order.priority}")
    
    # =====================================================================
    # STEP 3: Define Vehicles
    # =====================================================================
    print("\n3. Defining vehicles...")
    
    vehicles = [
        Vehicle(
            id=1,
            depot_id=0,           # Starts at Main Depot
            capacity=20.0,        # Can carry 20 cubic meters
            max_distance=200.0,   # Max 200 km per route
            cost_per_km=1.5       # Costs $1.5 per km
        ),
        Vehicle(
            id=2,
            depot_id=0,           # Also starts at Main Depot
            capacity=25.0,        # Larger vehicle
            max_distance=250.0,   # Can travel further
            cost_per_km=2.0       # More expensive to operate
        ),
    ]
    
    for vehicle in vehicles:
        print(f"   - Vehicle #{vehicle.id}: Capacity={vehicle.capacity}m³, "
              f"Max Distance={vehicle.max_distance}km")
    
    # =====================================================================
    # STEP 4: Create Distance Matrix
    # =====================================================================
    print("\n4. Creating distance matrix...")
    print("   (Using Euclidean distances for this example)")
    
    distance_matrix = create_distance_matrix(locations)
    
    # Print distance matrix
    print("\n   Distance Matrix (km):")
    header = "         " + "  ".join(f"{loc.id:>6}" for loc in locations)
    print(header)
    for i, loc in enumerate(locations):
        row = f"   {loc.id:>2}    " + "  ".join(
            f"{distance_matrix.matrix[i][j]:>6.1f}" 
            for j in range(len(locations))
        )
        print(row)
    
    # =====================================================================
    # STEP 5: Create Optimizer and Solve
    # =====================================================================
    print("\n" + "=" * 70)
    print("5. Solving the optimization problem...")
    print("=" * 70)
    
    # Create the optimizer
    optimizer = LogisticsOptimizer(
        locations=locations,
        vehicles=vehicles,
        orders=orders,
        distance_matrix=distance_matrix
    )
    
    # Solve with parameters
    result = optimizer.solve(
        time_limit_seconds=5,                     # Max 5 seconds
        first_solution_strategy="PATH_CHEAPEST_ARC",  # Initial heuristic
        local_search_metaheuristic="GUIDED_LOCAL_SEARCH"  # Improvement method
    )
    
    # =====================================================================
    # STEP 6: Display Results
    # =====================================================================
    print("\n" + result.summary())
    
    # =====================================================================
    # STEP 7: Interpret Results for Next Developer
    # =====================================================================
    print("\n" + "=" * 70)
    print("INTERPRETATION FOR DATABASE INTEGRATION")
    print("=" * 70)
    print("""
# For the next team member connecting to the database:

# 1. DATA NEEDED FROM DATABASE:
#    ─────────────────────────
#    a) Locations Table:
#       - location_id (INT)
#       - name (VARCHAR)
#       - latitude/longitude OR x,y coordinates (FLOAT)
#       - type (ENUM: 'depo', 'postachalnyk', 'tochka_vygruzky', 'hotspot')
   
#    b) Orders Table:
#       - order_id (INT)
#       - supplier_id (FK -> Locations)
#       - delivery_point_id (FK -> Locations)
#       - volume (FLOAT) - cubic meters or weight
#       - priority (INT) - 1=normal, 2=high, 3=urgent
   
#    c) Vehicles Table:
#       - vehicle_id (INT)
#       - depot_id (FK -> Locations)
#       - capacity (FLOAT) - max volume/weight
#       - max_distance (FLOAT) - km limit per route
#       - cost_per_km (FLOAT)

# 2. HOW TO INTEGRATE:
#    ─────────────────────────
#    a) Query your database and create Location, Order, Vehicle objects
#    b) Create DistanceMatrix (use real road distances, not Euclidean)
#    c) Call LogisticsOptimizer.solve()
#    d) Save results back to database:
#       - Route assignments
#       - Stop sequences
#       - Estimated distances

# 3. RETURN FORMAT FOR FRONTEND:
#    ─────────────────────────
#    Convert OptimizationResult to JSON:
#    {
#      "total_distance": 234.5,
#      "vehicles_used": 2,
#      "feasible": true,
#      "routes": [
#        {
#          "vehicle_id": 1,
#          "stops": [
#            {"location_id": 0, "type": "depo"},
#            {"location_id": 1, "type": "postachalnyk", "order_id": 101},
#            {"location_id": 4, "type": "tochka_vygruzky", "order_id": 101},
#            {"location_id": 0, "type": "depo"}
#          ],
#          "total_distance": 120.3
#        }
#      ]
#    }

# 4. IMPORTANT NOTES:
#    ─────────────────────────
#    - Distance matrix should use REAL road distances (Google Maps API, OSM)
#    - Coordinates can be GPS (lat/lng) or custom (x,y)
#    - Distance limits are CRITICAL - vehicles can't exceed max_distance
#    - Capacity is checked at every point in the route
#    - Pickup MUST happen before delivery for each order
# """)
    
    return result


def run_simple_test():
    """
    Minimal test case to verify the optimizer works.
    """
    print("\n" + "=" * 70)
    print("MINIMAL TEST CASE")
    print("=" * 70)

    # Simple scenario: 1 depot, 1 supplier, 1 delivery, 1 vehicle
    locations = [
        Location(id=0, name="Depot", x=0, y=0, type=NodeType.DEPOT),
        Location(id=1, name="Supplier", x=10, y=0, type=NodeType.SUPPLIER),
        Location(id=2, name="Customer", x=20, y=0, type=NodeType.DELIVERY_POINT),
    ]

    orders = [
        Order(id=1, from_location_id=1, to_location_id=2, volume=5.0)
    ]

    vehicles = [
        Vehicle(id=1, depot_id=0, capacity=10.0, max_distance=100.0)
    ]

    distance_matrix = create_distance_matrix(locations)

    optimizer = LogisticsOptimizer(locations, vehicles, orders, distance_matrix)
    result = optimizer.solve(time_limit_seconds=5)

    print(result.summary())
    return result


if __name__ == "__main__":
    # Simple test without capacity issues
    print("\n" + "=" * 70)
    print("SIMPLE PICKUP-DELIVERY TEST - 1 order, 1 vehicle")
    print("=" * 70)

    locations = [
        Location(id=0, name="Depot", x=0, y=0, type=NodeType.DEPOT),
        Location(id=1, name="Supplier", x=10, y=0, type=NodeType.SUPPLIER),
        Location(id=2, name="Customer", x=20, y=0, type=NodeType.DELIVERY_POINT),
    ]

    orders = [
    
    ]

    vehicles = [
        Vehicle(id=1, depot_id=0, capacity=100.0, max_distance=1000.0)
    ]

    distance_matrix = create_distance_matrix(locations)

    optimizer = LogisticsOptimizer(locations, vehicles, orders, distance_matrix)
    result = optimizer.solve(time_limit_seconds=5)

    print(result.summary())
    print("\nExpected route: Depot -> Supplier (pickup) -> Customer (deliver) -> Depot")
    print(f"Solution feasible: {result.is_feasible}")
