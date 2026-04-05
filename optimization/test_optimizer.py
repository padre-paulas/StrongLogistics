"""
Comprehensive test suite for the Logistics Optimization Engine.
Tests various scenarios and demonstrates how the optimizer works.
"""

from .models import Location, Vehicle, Order, NodeType
from .ortools_wrapper import LogisticsOptimizer, create_distance_matrix


def test_1_simple_pickup_delivery():
    """
    TEST 1: Simple Pickup-Delivery with 1 Vehicle
    
    Scenario:
    - 1 Depot (starting point)
    - 1 Supplier (pickup goods)
    - 1 Customer (deliver goods)
    - 1 Vehicle with sufficient capacity
    
    Expected: Depot -> Supplier -> Customer -> Depot
    Distance: 0->10 + 10->20 + 20->0 = 10 + 10 + 20 = 40 km
    """
    print("\n" + "=" * 70)
    print("TEST 1: Simple Pickup-Delivery with 1 Vehicle")
    print("=" * 70)
    
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
    
    distance_matrix = create_distance_matrix(locations, use_haversine=False)
    print("\nDistances:")
    print(f"  Depot -> Supplier: {distance_matrix.matrix[0][1]:.1f} km")
    print(f"  Supplier -> Customer: {distance_matrix.matrix[1][2]:.1f} km")
    print(f"  Customer -> Depot: {distance_matrix.matrix[2][0]:.1f} km")
    
    optimizer = LogisticsOptimizer(locations, vehicles, orders, distance_matrix)
    result = optimizer.solve(time_limit_seconds=5)
    
    print(result.summary())
    assert result.is_feasible, "Solution should be feasible"
    assert len(result.unserved_orders) == 0, "All orders should be served"
    assert result.total_vehicles_used == 1, "Should use 1 vehicle"
    print("✅ TEST 1 PASSED")
    return result


def test_2_multiple_orders_single_vehicle():
    """
    TEST 2: Multiple Orders with Single Vehicle
    
    Scenario:
    - 1 Depot
    - 2 Suppliers
    - 2 Customers
    - 1 Vehicle that must visit all locations in optimal order
    
    Constraints:
    - Must pickup before each delivery
    - Vehicle capacity: 50 m³ (enough for all orders)
    - Max distance: 200 km
    """
    print("\n" + "=" * 70)
    print("TEST 2: Multiple Orders with Single Vehicle")
    print("=" * 70)
    
    locations = [
        Location(id=0, name="Depot", x=0, y=0, type=NodeType.DEPOT),
        Location(id=1, name="Supplier A", x=10, y=10, type=NodeType.SUPPLIER),
        Location(id=2, name="Supplier B", x=20, y=10, type=NodeType.SUPPLIER),
        Location(id=3, name="Customer 1", x=15, y=20, type=NodeType.DELIVERY_POINT),
        Location(id=4, name="Customer 2", x=25, y=20, type=NodeType.DELIVERY_POINT),
    ]
    
    orders = [
        Order(id=1, from_location_id=1, to_location_id=3, volume=10.0),
        Order(id=2, from_location_id=2, to_location_id=4, volume=15.0),
    ]
    
    vehicles = [
        Vehicle(id=1, depot_id=0, capacity=50.0, max_distance=200.0)
    ]
    
    distance_matrix = create_distance_matrix(locations, use_haversine=False)
    optimizer = LogisticsOptimizer(locations, vehicles, orders, distance_matrix)
    result = optimizer.solve(time_limit_seconds=5)
    
    print(result.summary())
    assert result.is_feasible, "Solution should be feasible"
    assert len(result.unserved_orders) == 0, "All orders should be served"
    print("✅ TEST 2 PASSED")
    return result


def test_3_multiple_vehicles():
    """
    TEST 3: Multiple Vehicles Working in Parallel
    
    Scenario:
    - 1 Depot
    - 4 Orders from different suppliers to different customers
    - 2 Vehicles to split the work
    
    Expected: Optimizer will distribute orders between vehicles to minimize total distance
    """
    print("\n" + "=" * 70)
    print("TEST 3: Multiple Vehicles Working in Parallel")
    print("=" * 70)
    
    locations = [
        Location(id=0, name="Depot", x=0, y=0, type=NodeType.DEPOT),
        Location(id=1, name="Supplier A", x=10, y=0, type=NodeType.SUPPLIER),
        Location(id=2, name="Supplier B", x=20, y=0, type=NodeType.SUPPLIER),
        Location(id=3, name="Customer 1", x=12, y=5, type=NodeType.DELIVERY_POINT),
        Location(id=4, name="Customer 2", x=22, y=5, type=NodeType.DELIVERY_POINT),
    ]
    
    orders = [
        Order(id=1, from_location_id=1, to_location_id=3, volume=10.0),
        Order(id=2, from_location_id=2, to_location_id=4, volume=10.0),
    ]
    
    vehicles = [
        Vehicle(id=1, depot_id=0, capacity=20.0, max_distance=100.0),
        Vehicle(id=2, depot_id=0, capacity=20.0, max_distance=100.0),
    ]
    
    distance_matrix = create_distance_matrix(locations, use_haversine=False)
    optimizer = LogisticsOptimizer(locations, vehicles, orders, distance_matrix)
    result = optimizer.solve(time_limit_seconds=5)
    
    print(result.summary())
    assert result.is_feasible, "Solution should be feasible"
    print(f"Vehicles used: {result.total_vehicles_used}")
    print("✅ TEST 3 PASSED")
    return result


def test_4_capacity_constraint_violation():
    """
    TEST 4: Capacity Constraint Test
    
    Scenario:
    - Order volume exceeds vehicle capacity
    - This tests if the optimizer correctly identifies infeasible solutions
    
    Expected: Solution may be infeasible or order dropped
    """
    print("\n" + "=" * 70)
    print("TEST 4: Capacity Constraint Test (Overloaded Vehicle)")
    print("=" * 70)
    
    locations = [
        Location(id=0, name="Depot", x=0, y=0, type=NodeType.DEPOT),
        Location(id=1, name="Supplier", x=10, y=0, type=NodeType.SUPPLIER),
        Location(id=2, name="Customer", x=20, y=0, type=NodeType.DELIVERY_POINT),
    ]
    
    orders = [
        Order(id=1, from_location_id=1, to_location_id=2, volume=50.0)  # 50 m³ order
    ]
    
    vehicles = [
        Vehicle(id=1, depot_id=0, capacity=20.0, max_distance=100.0)  # Only 20 m³ capacity
    ]
    
    distance_matrix = create_distance_matrix(locations, use_haversine=False)
    optimizer = LogisticsOptimizer(locations, vehicles, orders, distance_matrix)
    result = optimizer.solve(time_limit_seconds=5)
    
    print(result.summary())
    print(f"Solution feasible: {result.is_feasible}")
    print(f"Unserved orders: {result.unserved_orders}")
    print("⚠️  TEST 4 COMPLETED (capacity violation expected)")
    return result


def test_5_distance_constraint():
    """
    TEST 5: Distance Constraint Test
    
    Scenario:
    - Vehicle has very limited max_distance
    - Route might exceed this limit
    
    Expected: Tests distance constraint enforcement
    """
    print("\n" + "=" * 70)
    print("TEST 5: Distance Constraint Test (Limited Range)")
    print("=" * 70)
    
    locations = [
        Location(id=0, name="Depot", x=0, y=0, type=NodeType.DEPOT),
        Location(id=1, name="Supplier", x=10, y=0, type=NodeType.SUPPLIER),
        Location(id=2, name="Customer", x=20, y=0, type=NodeType.DELIVERY_POINT),
    ]
    
    orders = [
        Order(id=1, from_location_id=1, to_location_id=2, volume=5.0)
    ]
    
    vehicles = [
        Vehicle(id=1, depot_id=0, capacity=20.0, max_distance=30.0)  # Tight limit
    ]
    
    distance_matrix = create_distance_matrix(locations, use_haversine=False)
    print(f"\nRequired distance: ~40 km (Depot->Supplier->Customer->Depot)")
    print(f"Vehicle max distance: 30 km")
    
    optimizer = LogisticsOptimizer(locations, vehicles, orders, distance_matrix)
    result = optimizer.solve(time_limit_seconds=5)
    
    print(result.summary())
    print(f"Solution feasible: {result.is_feasible}")
    print("⚠️  TEST 5 COMPLETED (distance constraint test)")
    return result


def test_6_priority_orders():
    """
    TEST 6: Priority-based Order Serving
    
    Scenario:
    - Multiple orders with different priorities
    - If not all can be served, higher priority should be served first
    """
    print("\n" + "=" * 70)
    print("TEST 6: Priority-based Order Serving")
    print("=" * 70)
    
    locations = [
        Location(id=0, name="Depot", x=0, y=0, type=NodeType.DEPOT),
        Location(id=1, name="Supplier A", x=5, y=0, type=NodeType.SUPPLIER),
        Location(id=2, name="Supplier B", x=10, y=0, type=NodeType.SUPPLIER),
        Location(id=3, name="Customer 1", x=7, y=3, type=NodeType.DELIVERY_POINT),
        Location(id=4, name="Customer 2", x=12, y=3, type=NodeType.DELIVERY_POINT),
    ]
    
    orders = [
        Order(id=1, from_location_id=1, to_location_id=3, volume=5.0, priority=1),  # Normal
        Order(id=2, from_location_id=2, to_location_id=4, volume=5.0, priority=3),  # Urgent
    ]
    
    vehicles = [
        Vehicle(id=1, depot_id=0, capacity=15.0, max_distance=50.0)
    ]
    
    distance_matrix = create_distance_matrix(locations, use_haversine=False)
    optimizer = LogisticsOptimizer(locations, vehicles, orders, distance_matrix)
    result = optimizer.solve(time_limit_seconds=5)
    
    print(result.summary())
    print("✅ TEST 6 COMPLETED")
    return result


def run_all_tests():
    """Run all tests and provide summary"""
    print("\n" + "=" * 70)
    print("LOGISTICS OPTIMIZATION ENGINE - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    
    results = []
    
    # Run tests
    results.append(("Simple Pickup-Delivery", test_1_simple_pickup_delivery()))
    results.append(("Multiple Orders", test_2_multiple_orders_single_vehicle()))
    results.append(("Multiple Vehicles", test_3_multiple_vehicles()))
    results.append(("Capacity Constraint", test_4_capacity_constraint_violation()))
    results.append(("Distance Constraint", test_5_distance_constraint()))
    results.append(("Priority Orders", test_6_priority_orders()))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    for name, result in results:
        status = "✅ PASS" if result.is_feasible else "⚠️  COMPLETED"
        print(f"{status} | {name:30} | Distance: {result.total_distance:6.2f} km | "
              f"Vehicles: {result.total_vehicles_used}")
    
    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
