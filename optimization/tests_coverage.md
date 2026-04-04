# StrongLogistics Edge Case Test Coverage

This document outlines all the edge-case tests we have added to our test suite (`test_edge_cases.py`) to systematically test the `LogisticsOptimizer` and its components against problematic data and constraints.

## Goal

The objective is to ensure that the VRP (Vehicle Routing Problem) solver:
1. Cannot be tricked by bad or conflicting inputs (e.g. duplicate IDs, nonexistent IDs).
2. Does not fail silently and produce bad routing logic (e.g. overriding orders from the same supplier).
3. Safely rejects unsolvable scenarios and handles OR-Tools internal requirements without causing a Hard-Crash in C++.
4. Handles scenarios where we have more vehicles than required without misbehaving.

---

## 1. Safety and Stability Tests

*   **`test_package_import`**: Ensures that the `optimization` module can actually be imported without throwing an error (found a previously commented-out function causing fatal crashes).
*   **`test_invalid_node_type`**: Verifies that passing an unknown string to `NodeType` stops processing immediately with an exact reason, instead of causing math errors later.
*   **`test_nan_coordinates`**: Validates `NaN` or `Inf` GPS coordinates are blocked at creation. **Why**: Or-Tools uses integer division distances. NaN values result in corrupt math and infinite distances.
*   **`test_empty_vehicles`**: Tests the case where the solver receives an empty list of `Vehicle` objects (`[]`).
    *   **Fix Applied**: If `num_vehicles == 0`, we intercept it and return `is_feasible = False` automatically. If we didn't, OR-Tools C++ layer would have a fatal check exception (`0 < vehicles_`) which force-kills the Python interpreter.
*   **`test_empty_locations` & `test_empty_orders`**: Ensures system generates empty but technically "feasible" (cost = 0) solutions without crashing.

## 2. Invalid Input & Data Corruption Tests

*   **`test_demand_overwrite`**: Tests if two different orders picked up from the exact same supplier ID handle correctly.
    *   **Fix Applied**: Before, `demand = order.volume` replaced the previous demand. Now we properly simulate loading BOTH orders by accumulating `demand += order.volume`.
*   **`test_distance_matrix_unknown_id`**: Passing an ID the matrix does not have now properly informs the user which list of known IDs it expected, instead of throwing an obscure Python `StopIteration` error.
*   **`test_duplicate_location_ids`**: Creating `Location(id=1, ...)` twice overwrites dictionaries silently. We now catch this actively.
*   **`test_order_invalid_location_ref` & `test_vehicle_invalid_depot`**: Creating references to locations that don't exist is checked immediately by the `LogisticsOptimizer` constructor.

## 3. Boundary & Physical Constraints Tests

*   **`test_zero_volume_order`**: Checks that an order taking up 0 space is successfully completed.
*   **`test_negative_volume_order`**: Asserts that negative volumes (which could artificially simulate "creating space" inside a fully loaded truck) are rejected.
*   **`test_zero_capacity_vehicle`**: Simulates a vehicle with `0.0` capacity and verifies it gets effectively sidelined and the orders stay unserved (unless there is another capable vehicle).
*   **`test_zero_max_distance`**: Similar to above, a truck with zero distance threshold must not perform any deliveries.
*   **`test_capacity_too_small`**: Order volume = 50, but vehicle capacity = 10. The test verifies it marks the order as unserved rather than forcing a failure.
*   **`test_exact_capacity`**: Order volume = 10, Vehicle capacity = 10. Asserts the system allows identical boundary conditions seamlessly.
*   **`test_coincident_locations` & `test_self_delivery_order`**: Verifies behavior if the Pickup location and the Delivery location are at the exact same geographic point (distance = 0).

## 4. Optimization Logic Tests

*   **`test_minimal_solve`**: Sanity check that 1 Depot, 1 Supplier, 1 Customer, and 1 vehicle solves a simple route accurately.
*   **`test_excess_vehicles` (Fleet Minimization Test)**: Supplies 2 identical vehicles to satisfy only 1 small order. 
    *   **Why**: Confirms the OR-Tools optimization logic actively understands that leaving a truck at the depot (saving the distance cost of dispatching it) is optimal. Ensures it only returns "1 Vehicle Used" and leaves the remaining one untouched.
*   **`test_summary_empty_result` & `test_calculate_totals_empty`**: Asserts that trying to summarize metrics on empty routes doesn't trigger calculation crashes.
