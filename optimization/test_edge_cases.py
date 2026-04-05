"""
Edge-case tests for the logistics optimization package.
Tests identified vulnerabilities from code review.

Run: python -m pytest optimization/test_edge_cases.py -v
  OR: python optimization/test_edge_cases.py
"""

import sys
import math
import traceback

# ─── Ensure we can import from parent directory ───────────────────────────
sys.path.insert(0, ".")

from optimization.models import (
    Location, Vehicle, Order, DistanceMatrix,
    VehicleRoute, RouteStop, OptimizationResult, NodeType
)
from optimization.ortools_wrapper import (
    LogisticsOptimizer, create_distance_matrix, calculate_euclidean_distance
)


class TestResult:
    """Simple test result tracker"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = 0
        self.results = []

    def record(self, name, status, detail=""):
        self.results.append((name, status, detail))
        if status == "PASS":
            self.passed += 1
        elif status == "FAIL":
            self.failed += 1
        else:
            self.errors += 1

    def summary(self):
        print("\n" + "=" * 70)
        print("EDGE-CASE TEST RESULTS")
        print("=" * 70)
        for name, status, detail in self.results:
            icon = {"PASS": "✅", "FAIL": "❌", "ERROR": "💥"}.get(status, "?")
            line = f"  {icon} [{status}] {name}"
            if detail:
                line += f"\n       → {detail}"
            print(line)
        print(f"\n  Total: {self.passed} passed, {self.failed} failed, {self.errors} errors")
        print("=" * 70)


results = TestResult()


# ═══════════════════════════════════════════════════════════════════════════
# HELPER: Create minimal valid problem for testing
# ═══════════════════════════════════════════════════════════════════════════
def make_minimal_problem():
    """1 depot, 1 supplier, 1 customer, 1 vehicle, 1 order"""
    locations = [
        Location(id=0, name="Depot", x=0, y=0, type=NodeType.DEPOT),
        Location(id=1, name="Supplier", x=10, y=0, type=NodeType.SUPPLIER),
        Location(id=2, name="Customer", x=20, y=0, type=NodeType.DELIVERY_POINT),
    ]
    orders = [Order(id=1, from_location_id=1, to_location_id=2, volume=5.0)]
    vehicles = [Vehicle(id=1, depot_id=0, capacity=10.0, max_distance=100.0)]
    dm = create_distance_matrix(locations, use_haversine=False)
    return locations, vehicles, orders, dm


# ═══════════════════════════════════════════════════════════════════════════
# TEST 1: Import crash (commented-out run_simple_test)
# ═══════════════════════════════════════════════════════════════════════════
def test_package_import():
    """__init__.py imports run_simple_test which is commented out"""
    try:
        # This import should fail because run_simple_test is commented out
        import importlib
        importlib.reload(sys.modules.get("optimization", __import__("optimization")))
        results.record(
            "Package import (run_simple_test)",
            "PASS",
            "Package imported successfully (run_simple_test may be uncommented or gracefully handled)"
        )
    except ImportError as e:
        results.record(
            "Package import (run_simple_test)",
            "FAIL",
            f"ImportError: {e}"
        )
    except Exception as e:
        results.record(
            "Package import (run_simple_test)",
            "ERROR",
            f"{type(e).__name__}: {e}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# TEST 2: Demand overwrite bug — multiple orders from same supplier
# ═══════════════════════════════════════════════════════════════════════════
def test_demand_overwrite():
    """Multiple orders from same supplier should accumulate demand, not overwrite"""
    locations = [
        Location(id=0, name="Depot", x=0, y=0, type=NodeType.DEPOT),
        Location(id=1, name="Supplier", x=10, y=0, type=NodeType.SUPPLIER),
        Location(id=2, name="Customer A", x=20, y=0, type=NodeType.DELIVERY_POINT),
        Location(id=3, name="Customer B", x=20, y=10, type=NodeType.DELIVERY_POINT),
    ]
    # Two orders from same supplier, total = 15m³
    orders = [
        Order(id=1, from_location_id=1, to_location_id=2, volume=8.0),
        Order(id=2, from_location_id=1, to_location_id=3, volume=7.0),
    ]
    # Vehicle capacity is 20m³ — enough for both (15m³ total)
    vehicles = [Vehicle(id=1, depot_id=0, capacity=20.0, max_distance=200.0)]
    dm = create_distance_matrix(locations, use_haversine=False)

    try:
        optimizer = LogisticsOptimizer(locations, vehicles, orders, dm)
        result = optimizer.solve(time_limit_seconds=5)
        if result.is_feasible and len(result.unserved_orders) == 0:
            results.record(
                "Demand accumulation (same supplier)",
                "PASS",
                f"Both orders served from same supplier (total demand=15m³, capacity=20m³)"
            )
        else:
            results.record(
                "Demand accumulation (same supplier)",
                "FAIL",
                f"Expected feasible, got infeasible. Unserved: {result.unserved_orders}"
            )
    except Exception as e:
        results.record(
            "Demand accumulation (same supplier)",
            "ERROR",
            f"Crashed: {type(e).__name__}: {e}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# TEST 3: DistanceMatrix.get_distance with unknown location ID
# ═══════════════════════════════════════════════════════════════════════════
def test_distance_matrix_unknown_id():
    """get_distance should give clear error for non-existent location ID"""
    locations = [
        Location(id=0, name="A", x=0, y=0, type=NodeType.DEPOT),
        Location(id=1, name="B", x=10, y=0, type=NodeType.SUPPLIER),
    ]
    dm = create_distance_matrix(locations, use_haversine=False)

    try:
        dm.get_distance(0, 999)  # ID 999 doesn't exist
        results.record(
            "DistanceMatrix unknown ID",
            "FAIL",
            "No error raised for non-existent location ID=999"
        )
    except StopIteration:
        results.record(
            "DistanceMatrix unknown ID",
            "FAIL",
            "Raised StopIteration (unhelpful) instead of ValueError with context"
        )
    except (ValueError, KeyError) as e:
        results.record(
            "DistanceMatrix unknown ID",
            "PASS",
            f"Proper error: {e}"
        )
    except Exception as e:
        results.record(
            "DistanceMatrix unknown ID",
            "ERROR",
            f"Unexpected {type(e).__name__}: {e}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# TEST 4: Duplicate location IDs
# ═══════════════════════════════════════════════════════════════════════════
def test_duplicate_location_ids():
    """Two locations with same ID should be caught by optimizer validation"""
    locations = [
        Location(id=0, name="Depot", x=0, y=0, type=NodeType.DEPOT),
        Location(id=1, name="Supplier A", x=10, y=0, type=NodeType.SUPPLIER),
        Location(id=1, name="Supplier B", x=99, y=99, type=NodeType.SUPPLIER),  # Duplicate ID!
        Location(id=2, name="Customer", x=20, y=0, type=NodeType.DELIVERY_POINT),
    ]
    orders = [Order(id=1, from_location_id=1, to_location_id=2, volume=5.0)]
    vehicles = [Vehicle(id=1, depot_id=0, capacity=10.0, max_distance=100.0)]
    dm = create_distance_matrix(locations, use_haversine=False)

    try:
        optimizer = LogisticsOptimizer(locations, vehicles, orders, dm)
        # If it gets past construction, the solve may still work (but with wrong data)
        result = optimizer.solve(time_limit_seconds=5)
        results.record(
            "Duplicate location IDs",
            "FAIL",
            "Duplicate ID=1 not caught by validation. This can cause wrong routing."
        )
    except ValueError as e:
        results.record(
            "Duplicate location IDs",
            "PASS",
            f"Caught duplicate ID: {e}"
        )
    except Exception as e:
        results.record(
            "Duplicate location IDs",
            "ERROR",
            f"Unexpected {type(e).__name__}: {e}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# TEST 5: Invalid NodeType string
# ═══════════════════════════════════════════════════════════════════════════
def test_invalid_node_type():
    """Invalid node type string should give helpful error"""
    try:
        loc = Location(id=0, name="Test", x=0, y=0, type="invalid_type")
        results.record(
            "Invalid NodeType string",
            "FAIL",
            "No error raised for type='invalid_type'"
        )
    except ValueError as e:
        msg = str(e)
        if "invalid_type" in msg:
            results.record(
                "Invalid NodeType string",
                "PASS",
                f"ValueError with context: {e}"
            )
        else:
            results.record(
                "Invalid NodeType string",
                "FAIL",
                f"ValueError lacks context about what was invalid: {e}"
            )


# ═══════════════════════════════════════════════════════════════════════════
# TEST 6: Zero-volume order
# ═══════════════════════════════════════════════════════════════════════════
def test_zero_volume_order():
    """Order with volume=0 should either be rejected or handled gracefully"""
    locations, vehicles, _, dm = make_minimal_problem()
    orders = [Order(id=1, from_location_id=1, to_location_id=2, volume=0.0)]

    try:
        optimizer = LogisticsOptimizer(locations, vehicles, orders, dm)
        result = optimizer.solve(time_limit_seconds=5)
        results.record(
            "Zero-volume order",
            "PASS",
            f"Solver handled it: feasible={result.is_feasible}, "
            f"unserved={result.unserved_orders}"
        )
    except Exception as e:
        results.record(
            "Zero-volume order",
            "FAIL",
            f"Crashed: {type(e).__name__}: {e}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# TEST 7: Negative volume order
# ═══════════════════════════════════════════════════════════════════════════
def test_negative_volume_order():
    """Order with negative volume makes no physical sense and should be rejected"""
    try:
        Order(id=1, from_location_id=1, to_location_id=2, volume=-5.0)
        results.record(
            "Negative-volume order",
            "FAIL",
            "Order with negative volume was created without validation"
        )
    except ValueError as e:
        results.record(
            "Negative-volume order",
            "PASS",
            f"Properly rejected: {e}"
        )
    except Exception as e:
        results.record(
            "Negative-volume order",
            "ERROR",
            f"Unexpected crash: {type(e).__name__}: {e}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# TEST 8: Vehicle with zero capacity
# ═══════════════════════════════════════════════════════════════════════════
def test_zero_capacity_vehicle():
    """Vehicle with capacity=0 can't carry anything — should fail gracefully"""
    locations = [
        Location(id=0, name="Depot", x=0, y=0, type=NodeType.DEPOT),
        Location(id=1, name="Supplier", x=10, y=0, type=NodeType.SUPPLIER),
        Location(id=2, name="Customer", x=20, y=0, type=NodeType.DELIVERY_POINT),
    ]
    orders = [Order(id=1, from_location_id=1, to_location_id=2, volume=5.0)]
    vehicles = [Vehicle(id=1, depot_id=0, capacity=0.0, max_distance=100.0)]
    dm = create_distance_matrix(locations, use_haversine=False)

    try:
        optimizer = LogisticsOptimizer(locations, vehicles, orders, dm)
        result = optimizer.solve(time_limit_seconds=5)
        if not result.is_feasible or len(result.unserved_orders) > 0:
            results.record(
                "Zero-capacity vehicle",
                "PASS",
                f"Correctly infeasible or order unserved: "
                f"feasible={result.is_feasible}, unserved={result.unserved_orders}"
            )
        else:
            results.record(
                "Zero-capacity vehicle",
                "FAIL",
                "Claims feasible with zero-capacity vehicle carrying cargo"
            )
    except Exception as e:
        results.record(
            "Zero-capacity vehicle",
            "ERROR",
            f"Crashed: {type(e).__name__}: {e}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# TEST 9: Vehicle with zero max_distance
# ═══════════════════════════════════════════════════════════════════════════
def test_zero_max_distance():
    """Vehicle with max_distance=0 can never leave depot"""
    locations, _, orders, dm = make_minimal_problem()
    vehicles = [Vehicle(id=1, depot_id=0, capacity=100.0, max_distance=0.0)]

    try:
        optimizer = LogisticsOptimizer(locations, vehicles, orders, dm)
        result = optimizer.solve(time_limit_seconds=5)
        if not result.is_feasible or len(result.unserved_orders) > 0:
            results.record(
                "Zero max_distance vehicle",
                "PASS",
                f"Correctly infeasible: feasible={result.is_feasible}, "
                f"unserved={result.unserved_orders}"
            )
        else:
            results.record(
                "Zero max_distance vehicle",
                "FAIL",
                "Claims feasible with max_distance=0"
            )
    except Exception as e:
        results.record(
            "Zero max_distance vehicle",
            "ERROR",
            f"Crashed: {type(e).__name__}: {e}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# TEST 10: No orders (empty order list)
# ═══════════════════════════════════════════════════════════════════════════
def test_empty_orders():
    """No orders should result in vehicles sitting at depots"""
    locations = [
        Location(id=0, name="Depot", x=0, y=0, type=NodeType.DEPOT),
    ]
    vehicles = [Vehicle(id=1, depot_id=0, capacity=10.0, max_distance=100.0)]
    dm = create_distance_matrix(locations, use_haversine=False)

    try:
        optimizer = LogisticsOptimizer(locations, vehicles, [], dm)
        result = optimizer.solve(time_limit_seconds=5)
        results.record(
            "Empty orders",
            "PASS",
            f"Handled: feasible={result.is_feasible}, "
            f"vehicles_used={result.total_vehicles_used}, distance={result.total_distance}"
        )
    except Exception as e:
        results.record(
            "Empty orders",
            "FAIL",
            f"Crashed on empty orders: {type(e).__name__}: {e}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# TEST 11: Empty vehicles list
# ═══════════════════════════════════════════════════════════════════════════
def test_empty_vehicles():
    """No vehicles — problem is trivially infeasible"""
    locations = [
        Location(id=0, name="Depot", x=0, y=0, type=NodeType.DEPOT),
        Location(id=1, name="Supplier", x=10, y=0, type=NodeType.SUPPLIER),
        Location(id=2, name="Customer", x=20, y=0, type=NodeType.DELIVERY_POINT),
    ]
    orders = [Order(id=1, from_location_id=1, to_location_id=2, volume=5.0)]
    dm = create_distance_matrix(locations, use_haversine=False)

    try:
        optimizer = LogisticsOptimizer(locations, [], orders, dm)
        result = optimizer.solve(time_limit_seconds=5)
        results.record(
            "Empty vehicles",
            "PASS",
            f"Handled: feasible={result.is_feasible}"
        )
    except Exception as e:
        results.record(
            "Empty vehicles",
            "FAIL",
            f"Crashed on empty vehicles: {type(e).__name__}: {e}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# TEST 12: Empty locations list
# ═══════════════════════════════════════════════════════════════════════════
def test_empty_locations():
    """No locations — nothing to route"""
    try:
        dm = DistanceMatrix(locations=[], matrix=[])
        optimizer = LogisticsOptimizer([], [], [], dm)
        result = optimizer.solve(time_limit_seconds=5)
        results.record(
            "Empty locations",
            "PASS",
            f"Handled: feasible={result.is_feasible}"
        )
    except Exception as e:
        results.record(
            "Empty locations",
            "FAIL",
            f"Crashed on empty locations: {type(e).__name__}: {e}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# TEST 13: Order referencing non-existent location
# ═══════════════════════════════════════════════════════════════════════════
def test_order_invalid_location_ref():
    """Order references a location ID that doesn't exist"""
    locations = [
        Location(id=0, name="Depot", x=0, y=0, type=NodeType.DEPOT),
        Location(id=1, name="Supplier", x=10, y=0, type=NodeType.SUPPLIER),
        Location(id=2, name="Customer", x=20, y=0, type=NodeType.DELIVERY_POINT),
    ]
    # Order references location 999 which doesn't exist
    orders = [Order(id=1, from_location_id=1, to_location_id=999, volume=5.0)]
    vehicles = [Vehicle(id=1, depot_id=0, capacity=10.0, max_distance=100.0)]
    dm = create_distance_matrix(locations, use_haversine=False)

    try:
        optimizer = LogisticsOptimizer(locations, vehicles, orders, dm)
        result = optimizer.solve(time_limit_seconds=5)
        results.record(
            "Order with invalid location ref",
            "FAIL",
            "No error raised for referencing non-existent location ID=999"
        )
    except KeyError as e:
        results.record(
            "Order with invalid location ref",
            "FAIL",
            f"KeyError (unhelpful): {e} — should give descriptive message"
        )
    except (ValueError, RuntimeError) as e:
        results.record(
            "Order with invalid location ref",
            "PASS",
            f"Proper error: {e}"
        )
    except Exception as e:
        results.record(
            "Order with invalid location ref",
            "ERROR",
            f"Unexpected {type(e).__name__}: {e}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# TEST 14: Vehicle with non-existent depot ID
# ═══════════════════════════════════════════════════════════════════════════
def test_vehicle_invalid_depot():
    """Vehicle references a depot ID that doesn't exist"""
    locations = [
        Location(id=0, name="Depot", x=0, y=0, type=NodeType.DEPOT),
        Location(id=1, name="Supplier", x=10, y=0, type=NodeType.SUPPLIER),
        Location(id=2, name="Customer", x=20, y=0, type=NodeType.DELIVERY_POINT),
    ]
    orders = [Order(id=1, from_location_id=1, to_location_id=2, volume=5.0)]
    vehicles = [Vehicle(id=1, depot_id=999, capacity=10.0, max_distance=100.0)]  # 999 doesn't exist
    dm = create_distance_matrix(locations, use_haversine=False)

    try:
        optimizer = LogisticsOptimizer(locations, vehicles, orders, dm)
        result = optimizer.solve(time_limit_seconds=5)
        results.record(
            "Vehicle with invalid depot ID",
            "FAIL",
            "No error raised for referencing non-existent depot ID=999"
        )
    except KeyError as e:
        results.record(
            "Vehicle with invalid depot ID",
            "FAIL",
            f"KeyError (unhelpful): {e} — should give descriptive message about depot"
        )
    except (ValueError, RuntimeError) as e:
        results.record(
            "Vehicle with invalid depot ID",
            "PASS",
            f"Proper error: {e}"
        )
    except Exception as e:
        results.record(
            "Vehicle with invalid depot ID",
            "ERROR",
            f"Unexpected {type(e).__name__}: {e}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# TEST 15: Very large distance (potential integer overflow in ×1000 scaling)
# ═══════════════════════════════════════════════════════════════════════════
def test_large_distances():
    """Locations very far apart — int(distance * 1000) could be huge"""
    locations = [
        Location(id=0, name="Depot", x=0, y=0, type=NodeType.DEPOT),
        Location(id=1, name="Supplier", x=1_000_000, y=0, type=NodeType.SUPPLIER),
        Location(id=2, name="Customer", x=2_000_000, y=0, type=NodeType.DELIVERY_POINT),
    ]
    orders = [Order(id=1, from_location_id=1, to_location_id=2, volume=5.0)]
    vehicles = [Vehicle(id=1, depot_id=0, capacity=10.0, max_distance=10_000_000.0)]
    dm = create_distance_matrix(locations, use_haversine=False)

    max_scaled = max(
        int(dm.matrix[i][j] * 1000) 
        for i in range(len(locations))
        for j in range(len(locations))
    )

    try:
        optimizer = LogisticsOptimizer(locations, vehicles, orders, dm)
        result = optimizer.solve(time_limit_seconds=5)
        results.record(
            "Large distances (overflow risk)",
            "PASS",
            f"Solver handled large distances. Max scaled value: {max_scaled:,}"
        )
    except Exception as e:
        results.record(
            "Large distances (overflow risk)",
            "FAIL",
            f"Crashed with large distances (max scaled: {max_scaled:,}): "
            f"{type(e).__name__}: {e}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# TEST 16: Coincident locations (distance = 0)
# ═══════════════════════════════════════════════════════════════════════════
def test_coincident_locations():
    """Two locations at exact same coordinates"""
    locations = [
        Location(id=0, name="Depot", x=10, y=10, type=NodeType.DEPOT),
        Location(id=1, name="Supplier", x=10, y=10, type=NodeType.SUPPLIER),  # Same as depot!
        Location(id=2, name="Customer", x=10, y=10, type=NodeType.DELIVERY_POINT),  # Same too!
    ]
    orders = [Order(id=1, from_location_id=1, to_location_id=2, volume=5.0)]
    vehicles = [Vehicle(id=1, depot_id=0, capacity=10.0, max_distance=100.0)]
    dm = create_distance_matrix(locations, use_haversine=False)

    try:
        optimizer = LogisticsOptimizer(locations, vehicles, orders, dm)
        result = optimizer.solve(time_limit_seconds=5)
        results.record(
            "Coincident locations (distance=0)",
            "PASS",
            f"Handled: feasible={result.is_feasible}, distance={result.total_distance}"
        )
    except Exception as e:
        results.record(
            "Coincident locations (distance=0)",
            "FAIL",
            f"Crashed: {type(e).__name__}: {e}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# TEST 17: Single location only (just a depot)
# ═══════════════════════════════════════════════════════════════════════════
def test_single_location():
    """Only a depot, no suppliers or customers"""
    locations = [Location(id=0, name="Depot", x=0, y=0, type=NodeType.DEPOT)]
    vehicles = [Vehicle(id=1, depot_id=0, capacity=10.0, max_distance=100.0)]
    dm = create_distance_matrix(locations, use_haversine=False)

    try:
        optimizer = LogisticsOptimizer(locations, vehicles, [], dm)
        result = optimizer.solve(time_limit_seconds=5)
        results.record(
            "Single location (depot only)",
            "PASS",
            f"Handled: feasible={result.is_feasible}"
        )
    except Exception as e:
        results.record(
            "Single location (depot only)",
            "FAIL",
            f"Crashed: {type(e).__name__}: {e}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# TEST 18: Order with same pickup and delivery location
# ═══════════════════════════════════════════════════════════════════════════
def test_self_delivery_order():
    """Order where from == to (pickup and delivery are the same place)"""
    locations = [
        Location(id=0, name="Depot", x=0, y=0, type=NodeType.DEPOT),
        Location(id=1, name="Place", x=10, y=0, type=NodeType.SUPPLIER),
    ]
    orders = [Order(id=1, from_location_id=1, to_location_id=1, volume=5.0)]  # Same location!
    vehicles = [Vehicle(id=1, depot_id=0, capacity=10.0, max_distance=100.0)]
    dm = create_distance_matrix(locations, use_haversine=False)

    try:
        optimizer = LogisticsOptimizer(locations, vehicles, orders, dm)
        result = optimizer.solve(time_limit_seconds=5)
        results.record(
            "Self-delivery order (from==to)",
            "PASS",
            f"Handled: feasible={result.is_feasible}, distance={result.total_distance}"
        )
    except Exception as e:
        results.record(
            "Self-delivery order (from==to)",
            "FAIL",
            f"Crashed: {type(e).__name__}: {e}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# TEST 19: Capacity exactly equal to demand
# ═══════════════════════════════════════════════════════════════════════════
def test_exact_capacity():
    """Vehicle capacity exactly equals order volume"""
    locations, _, _, dm = make_minimal_problem()
    orders = [Order(id=1, from_location_id=1, to_location_id=2, volume=10.0)]
    vehicles = [Vehicle(id=1, depot_id=0, capacity=10.0, max_distance=100.0)]

    try:
        optimizer = LogisticsOptimizer(locations, vehicles, orders, dm)
        result = optimizer.solve(time_limit_seconds=5)
        if result.is_feasible:
            results.record(
                "Exact capacity match",
                "PASS",
                "Vehicle with capacity=10 can carry order with volume=10"
            )
        else:
            results.record(
                "Exact capacity match",
                "FAIL",
                f"Should be feasible but got infeasible. Unserved: {result.unserved_orders}"
            )
    except Exception as e:
        results.record(
            "Exact capacity match",
            "ERROR",
            f"Crashed: {type(e).__name__}: {e}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# TEST 20: VehicleRoute.calculate_totals with empty stops
# ═══════════════════════════════════════════════════════════════════════════
def test_calculate_totals_empty():
    """calculate_totals on route with no stops"""
    route = VehicleRoute(vehicle_id=1)
    try:
        route.calculate_totals()
        results.record(
            "calculate_totals() empty route",
            "PASS",
            f"total_distance={route.total_distance}, total_load={route.total_load}"
        )
    except Exception as e:
        results.record(
            "calculate_totals() empty route",
            "FAIL",
            f"Crashed: {type(e).__name__}: {e}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# TEST 21: OptimizationResult.summary with no routes
# ═══════════════════════════════════════════════════════════════════════════
def test_summary_empty_result():
    """summary() should work on an empty result"""
    result = OptimizationResult(
        routes=[],
        total_distance=0,
        total_vehicles_used=0,
        is_feasible=False,
        unserved_orders=[1, 2, 3],
        computation_time_ms=0,
        constraint_violations=["No solution"]
    )
    try:
        s = result.summary()
        assert isinstance(s, str)
        assert "No" in s or "0" in s
        results.record(
            "summary() on empty result",
            "PASS",
            f"Summary generated ({len(s)} chars)"
        )
    except Exception as e:
        results.record(
            "summary() on empty result",
            "FAIL",
            f"Crashed: {type(e).__name__}: {e}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# TEST 22: NaN coordinates
# ═══════════════════════════════════════════════════════════════════════════
def test_nan_coordinates():
    """NaN coordinates should be rejected at Location creation"""
    try:
        Location(id=1, name="Bad", x=float('nan'), y=float('nan'), type=NodeType.SUPPLIER)
        results.record(
            "NaN coordinates",
            "FAIL",
            "Location with NaN coordinates was created without error"
        )
    except ValueError as e:
        results.record(
            "NaN coordinates",
            "PASS",
            f"Location creation properly rejected NaN: {e}"
        )
    except Exception as e:
        results.record(
            "NaN coordinates",
            "ERROR",
            f"Unexpected {type(e).__name__}: {e}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# TEST 23: Minimal valid solve (sanity check)
# ═══════════════════════════════════════════════════════════════════════════
def test_minimal_solve():
    """Basic sanity check — simplest possible problem should solve"""
    locations, vehicles, orders, dm = make_minimal_problem()

    try:
        optimizer = LogisticsOptimizer(locations, vehicles, orders, dm)
        result = optimizer.solve(time_limit_seconds=5)
        if result.is_feasible and len(result.unserved_orders) == 0:
            results.record(
                "Minimal valid solve",
                "PASS",
                f"Solved: distance={result.total_distance:.2f}, "
                f"vehicles={result.total_vehicles_used}"
            )
        else:
            results.record(
                "Minimal valid solve",
                "FAIL",
                f"Should be feasible: feasible={result.is_feasible}, "
                f"unserved={result.unserved_orders}, "
                f"violations={result.constraint_violations}"
            )
    except Exception as e:
        results.record(
            "Minimal valid solve",
            "ERROR",
            f"Crashed: {type(e).__name__}: {e}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# TEST 24: Capacity too small for any order
# ═══════════════════════════════════════════════════════════════════════════
def test_capacity_too_small():
    """Vehicle capacity is less than the order volume"""
    locations, _, _, dm = make_minimal_problem()
    orders = [Order(id=1, from_location_id=1, to_location_id=2, volume=50.0)]
    vehicles = [Vehicle(id=1, depot_id=0, capacity=10.0, max_distance=100.0)]

    try:
        optimizer = LogisticsOptimizer(locations, vehicles, orders, dm)
        result = optimizer.solve(time_limit_seconds=5)
        if not result.is_feasible or len(result.unserved_orders) > 0:
            results.record(
                "Capacity too small",
                "PASS",
                f"Correctly infeasible: unserved={result.unserved_orders}"
            )
        else:
            results.record(
                "Capacity too small",
                "FAIL",
                "Claims feasible with order volume(50) > capacity(10)"
            )
    except Exception as e:
        results.record(
            "Capacity too small",
            "ERROR",
            f"Crashed: {type(e).__name__}: {e}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# TEST 25: Fleet Minimization / Excess Vehicles
# ═══════════════════════════════════════════════════════════════════════════
def test_excess_vehicles():
    """Algorithm should only use 1 vehicle if 1 is sufficient, leaving others at depot"""
    locations, _, orders, dm = make_minimal_problem()
    # Provide 2 identical vehicles. Only 1 is needed to fulfill the 1 order.
    vehicles = [
        Vehicle(id=1, depot_id=0, capacity=10.0, max_distance=100.0),
        Vehicle(id=2, depot_id=0, capacity=10.0, max_distance=100.0)
    ]

    try:
        optimizer = LogisticsOptimizer(locations, vehicles, orders, dm)
        result = optimizer.solve(time_limit_seconds=5)
        
        if result.is_feasible and result.total_vehicles_used == 1:
            results.record(
                "Fleet Minimization (Excess Vehicles)",
                "PASS",
                "Successfully left the unnecessary vehicle at the depot."
            )
        else:
            results.record(
                "Fleet Minimization (Excess Vehicles)",
                "FAIL",
                f"Expected 1 vehicle used, got {result.total_vehicles_used} (feasible: {result.is_feasible})"
            )
    except Exception as e:
        results.record(
            "Fleet Minimization (Excess Vehicles)",
            "ERROR",
            f"Crashed: {type(e).__name__}: {e}"
        )

# ═══════════════════════════════════════════════════════════════════════════
# TEST 26: Weight Capacity Constraints
# ═══════════════════════════════════════════════════════════════════════════
def test_weight_constraints():
    """Verify that a volumetrically small but overly heavy order is rejected"""
    locations, vehicles, _, dm = make_minimal_problem()
    # Vol 5.0, but Weight is 100
    orders = [Order(id=1, from_location_id=1, to_location_id=2, volume=5.0, weight=100.0)]
    # Vehicle can hold vol 10.0, but only weight 50
    vehicles[0].weight_capacity = 50.0

    try:
        optimizer = LogisticsOptimizer(locations, vehicles, orders, dm)
        result = optimizer.solve(time_limit_seconds=5)

        if not result.is_feasible and result.unserved_orders:
            results.record("Weight Capacity Exceeded", "PASS", "Order appropriately rejected due to weight")
        elif result.is_feasible:
            results.record("Weight Capacity Exceeded", "FAIL", "Order routed despite exceeding weight capacity!")
        else:
            results.record("Weight Capacity Exceeded", "FAIL", f"Unexpected: feasible={result.is_feasible}, unserved={result.unserved_orders}")
    except Exception as e:
        results.record("Weight Capacity Exceeded", "ERROR", f"Crashed: {e}")

# ═══════════════════════════════════════════════════════════════════════════
# TEST 27: Async Solver Wrapping
# ═══════════════════════════════════════════════════════════════════════════
def test_async_solve():
    """Verify that the async solver works correctly"""
    import asyncio
    locations, vehicles, orders, dm = make_minimal_problem()
    
    async def run_it():
        optimizer = LogisticsOptimizer(locations, vehicles, orders, dm)
        return await optimizer.solve_async(time_limit_seconds=5)

    try:
        result = asyncio.run(run_it())
        results.record("Async Solver execution", "PASS", f"Async solved, feasible: {result.is_feasible}")
    except Exception as e:
        results.record("Async Solver execution", "ERROR", f"Failed: {e}")

# ═══════════════════════════════════════════════════════════════════════════
# TEST 28: Split Depots (Different Start and End)
# ═══════════════════════════════════════════════════════════════════════════
def test_split_depots():
    """Verify vehicles can start and end at different locations"""
    locations = [
        Location(id=0, name="Start Depot", x=0, y=0, type=NodeType.DEPOT),
        Location(id=1, name="Supplier", x=10, y=0, type=NodeType.SUPPLIER),
        Location(id=2, name="Customer", x=20, y=0, type=NodeType.DELIVERY_POINT),
        Location(id=3, name="End Depot", x=30, y=0, type=NodeType.DEPOT),
    ]
    orders = [Order(id=1, from_location_id=1, to_location_id=2, volume=5.0)]
    vehicles = [Vehicle(id=1, depot_id=0, start_depot_id=0, end_depot_id=3, capacity=10.0, max_distance=100.0)]
    dm = create_distance_matrix(locations, use_haversine=False)
    
    try:
        optimizer = LogisticsOptimizer(locations, vehicles, orders, dm)
        result = optimizer.solve(time_limit_seconds=5)
        
        if result.is_feasible and result.routes[0].stops[-1].location_id == 3:
            results.record("Split Depots", "PASS", "Vehicle successfully ended at Depot 3")
        else:
            results.record("Split Depots", "FAIL", "Vehicle did not end at expected depot")
    except Exception as e:
        results.record("Split Depots", "ERROR", f"Crashed: {e}")

# ═══════════════════════════════════════════════════════════════════════════
# TEST 29: Time Windows Rejection
# ═══════════════════════════════════════════════════════════════════════════
def test_time_windows_rejection():
    """Verify that an order with an impossible time window is rejected"""
    locations, vehicles, _, dm = make_minimal_problem()
    # Order strictly requires delivery between time 0 and 1 (seconds).
    # But it takes much longer to travel from Depot(x=0) to Supplier(x=10) to Customer(x=20)
    orders = [Order(id=1, from_location_id=1, to_location_id=2, volume=5.0, time_window_start=0, time_window_end=1)]
    
    try:
        optimizer = LogisticsOptimizer(locations, vehicles, orders, dm)
        result = optimizer.solve(time_limit_seconds=5)

        if not result.is_feasible and result.unserved_orders:
             results.record("Time Windows", "PASS", "Order properly ignored because delivery time constraint impossible")
        elif result.is_feasible:
             results.record("Time Windows", "FAIL", "Order routed despite impossible time window constraint")
        else:
             results.record("Time Windows", "FAIL", f"Unexpected: feasible={result.is_feasible}, unserved={result.unserved_orders}")
    except Exception as e:
         results.record("Time Windows", "ERROR", f"Crashed: {e}")

# ═══════════════════════════════════════════════════════════════════════════
# RUN ALL TESTS
# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 70)
    print("EDGE-CASE TEST SUITE — StrongLogistics/optimization")
    print("=" * 70)

    tests = [
        test_package_import,
        test_demand_overwrite,
        test_distance_matrix_unknown_id,
        test_duplicate_location_ids,
        test_invalid_node_type,
        test_zero_volume_order,
        test_negative_volume_order,
        test_zero_capacity_vehicle,
        test_zero_max_distance,
        test_empty_orders,
        test_empty_vehicles,
        test_empty_locations,
        test_order_invalid_location_ref,
        test_vehicle_invalid_depot,
        test_large_distances,
        test_coincident_locations,
        test_single_location,
        test_self_delivery_order,
        test_exact_capacity,
        test_calculate_totals_empty,
        test_summary_empty_result,
        test_nan_coordinates,
        test_minimal_solve,
        test_capacity_too_small,
        test_excess_vehicles,
        test_weight_constraints,
        test_async_solve,
        test_split_depots,
        test_time_windows_rejection,
    ]

    for test_fn in tests:
        print(f"\n  Running: {test_fn.__name__}...")
        try:
            test_fn()
        except Exception as e:
            results.record(
                test_fn.__name__,
                "ERROR",
                f"Unhandled: {type(e).__name__}: {e}\n{traceback.format_exc()}"
            )

    results.summary()
