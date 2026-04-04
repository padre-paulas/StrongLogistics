# Logistics Optimization Engine - How It Works (Step-by-Step Guide)

## 🎯 What This Code Does

This is a **Vehicle Routing Problem (VRP) solver** with pickup and delivery constraints. It finds the **optimal routes** for vehicles to:
1. **Pickup goods** from suppliers
2. **Deliver goods** to customers
3. **Minimize total distance** traveled
4. **Respect constraints** (vehicle capacity, max distance, etc.)

---

## 📊 Step-by-Step: How the Solver Works

### STEP 1: Define the Problem

```python
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
```

**What this means:**
- We have 3 locations: a depot, a supplier, and a customer
- We need to pickup 5m³ from the supplier and deliver to the customer
- We have 1 vehicle that can carry 10m³ and travel max 100km

---

### STEP 2: Create Distance Matrix

```python
distance_matrix = create_distance_matrix(locations)
```

**What this does:**
- Calculates distances between ALL pairs of locations
- Creates a table like this:

```
        Depot  Supplier  Customer
Depot     0.0     10.0      20.0
Supplier 10.0      0.0      10.0
Customer 20.0     10.0       0.0
```

**Why important:**
- OR-Tools uses this to calculate route distances
- In production, use REAL road distances (Google Maps API, OpenStreetMap)

---

### STEP 3: Create Optimizer

```python
optimizer = LogisticsOptimizer(
    locations=locations,
    vehicles=vehicles,
    orders=orders,
    distance_matrix=distance_matrix
)
```

**What this does:**
- Stores all problem data
- Prepares to build constraints

---

### STEP 4: Solve the Problem (The Magic Happens Here)

```python
result = optimizer.solve(time_limit_seconds=5)
```

**What happens inside:**

#### 4.1 Create OR-Tools Manager
```python
self.manager = pywrapcp.RoutingIndexManager(
    num_locations,      # How many locations
    num_vehicles,       # How many vehicles
    depot_indices,      # Where vehicles start
    depot_indices       # Where vehicles end
)
```

#### 4.2 Create Routing Model
```python
self.routing = pywrapcp.RoutingModel(self.manager)
```

This is the main optimization model that OR-Tools will solve.

#### 4.3 Setup Distance Callback
```python
def distance_callback(from_index, to_index):
    from_node = self.manager.IndexToNode(from_index)
    to_node = self.manager.IndexToNode(to_index)
    distance = self._calculate_distance(from_node, to_node)
    return int(distance * 1000)  # Convert to integer (meters)
```

**Why multiply by 1000?**
- OR-Tools works with integers only
- Multiplying by 1000 preserves decimal precision
- Example: 12.345 km → 12345 (stored as integer) → 12.345 km (when retrieved)

#### 4.4 Setup Pickup & Delivery Constraints
```python
for order in orders:
    pickup_index = self.location_id_to_index[order.from_location_id]
    delivery_index = self.location_id_to_index[order.to_location_id]
    
    pickup_node = self.manager.NodeToIndex(pickup_index)
    delivery_node = self.manager.NodeToIndex(delivery_index)
    
    # Enforce pickup before delivery
    self.routing.AddPickupAndDelivery(pickup_node, delivery_node)
    
    # Same vehicle must handle both
    self.routing.solver().Add(
        self.routing.VehicleVar(pickup_node) ==
        self.routing.VehicleVar(delivery_node)
    )
```

**What this enforces:**
- ✅ Goods must be picked up at supplier BEFORE delivery to customer
- ✅ The SAME vehicle must do both pickup and delivery
- ❌ You can't deliver what you haven't picked up!

#### 4.5 Setup Capacity Constraints
```python
def demand_callback(from_index):
    from_node = self.manager.IndexToNode(from_index)
    return int(order_demand.get(from_node, 0) * 1000)

self.routing.AddDimensionWithVehicleCapacity(
    demand_callback_index,
    0,  # No slack
    [int(v.capacity * 1000) for v in self.vehicles],
    True,
    "capacity"
)
```

**What this enforces:**
- ✅ Vehicle load never exceeds its capacity
- ✅ Load is tracked at every point in the route
- ❌ Can't overload vehicles

#### 4.6 Setup Distance Constraints
```python
self.routing.AddDimension(
    transit_callback_index,
    0,  # No slack
    int(max_distance * 1000),  # Max distance
    True,
    "distance"
)
```

**What this enforces:**
- ✅ Total route distance never exceeds vehicle's max_distance
- ✅ Distance is cumulative along the route
- ❌ Vehicles can't exceed their range limits

#### 4.7 Set Search Parameters
```python
search_parameters = pywrapcp.DefaultRoutingSearchParameters()
search_parameters.first_solution_strategy = PATH_CHEAPEST_ARC
search_parameters.local_search_metaheuristic = AUTOMATIC
search_parameters.time_limit.FromSeconds(5)
```

**What these control:**
- **First solution strategy**: How to build initial route (greedy approach)
- **Metaheuristic**: How to improve the solution (search for better routes)
- **Time limit**: How long to search (trade-off: time vs quality)

#### 4.8 Solve!
```python
solution = self.routing.SolveWithParameters(search_parameters)
```

**What OR-Tools does:**
1. Builds initial solution using heuristic
2. Iteratively improves it using local search
3. Stops when time limit reached or no better solution found
4. Returns the best solution found

---

### STEP 5: Extract Results

```python
result = self._extract_solution(solution)
```

**What this does:**
- Converts OR-Tools internal format to clean Python objects
- Extracts route for each vehicle
- Calculates totals (distance, load)
- Checks constraint violations
- Identifies unserved orders

---

## 🔍 Test Results Explained

### TEST 1: Simple Pickup-Delivery ✅
```
Route: Depot -> Supplier -> Customer -> Depot
Distance: 40.00 km
Vehicles: 1
```

**Why this route?**
- Depot (0) → Supplier (10km) → Customer (10km) → Depot (20km) = 40km
- This is the ONLY valid route (must pickup before delivery)

---

### TEST 2: Multiple Orders, Single Vehicle ✅
```
Route: Depot -> Supplier A -> Supplier B -> Customer 2 -> Customer 1 -> Depot
Distance: 70.32 km
Vehicles: 1
```

**Why this route?**
- Optimizer found this is the shortest path
- Both pickups happen before deliveries ✅
- Total load (25m³) < capacity (50m³) ✅

**Alternative routes considered:**
- Depot → A → B → C1 → C2 → Depot (longer)
- Depot → A → C1 → B → C2 → Depot (longer)

---

### TEST 3: Multiple Vehicles ✅
```
Vehicle 1: Depot -> Supplier A -> Customer 1 -> Depot (28.39 km)
Vehicle 2: Depot -> Supplier B -> Customer 2 -> Depot (47.95 km)
Total: 76.33 km
Vehicles: 2
```

**Why split between vehicles?**
- Each vehicle handles one order independently
- Parallel execution is faster
- Total distance optimized across all vehicles

---

### TEST 4: Capacity Constraint Violation ⚠️
```
Order volume: 50 m³
Vehicle capacity: 20 m³
Result: INFEASIBLE (order dropped)
```

**Why infeasible?**
- Order requires 50m³ but vehicle can only carry 20m³
- Constraint prevents impossible assignment
- Order marked as "unserved"

**How to fix:**
- Increase vehicle capacity: `capacity=60.0`
- Use larger vehicle
- Split order into smaller shipments

---

### TEST 5: Distance Constraint Violation ⚠️
```
Required distance: ~40 km
Vehicle max distance: 30 km
Result: INFEASIBLE (order dropped)
```

**Why infeasible?**
- Route requires 40km but vehicle can only travel 30km
- Constraint prevents over-distance routes
- Order marked as "unserved"

**How to fix:**
- Increase max_distance: `max_distance=50.0`
- Use vehicle with larger range
- Add intermediate depot

---

### TEST 6: Priority Orders ✅
```
Route: Depot -> Supplier A -> Supplier B -> Customer 2 -> Customer 1 -> Depot
Distance: 26.22 km
All orders served
```

**How priorities work:**
- Priority 1 = Normal, Priority 3 = Urgent
- If constraints force dropping orders, lower priority dropped first
- In this case, both orders fit, so all served

---

## 🚫 Key Constraints Summary

| Constraint | What It Does | Example |
|------------|--------------|---------|
| **Pickup & Delivery** | Must pickup before delivery | Can't deliver before picking up |
| **Same Vehicle** | Pickup & delivery by same vehicle | Order stays on one truck |
| **Capacity** | Vehicle load ≤ capacity | 20m³ truck can't carry 30m³ |
| **Distance** | Route distance ≤ max_distance | 100km truck can't travel 150km |
| **Time Limit** | Solver stops after N seconds | 5s limit = fast but maybe not optimal |

---

## 🔧 How Constraints Are Enforced

### Hard Constraints (MUST satisfy):
1. **Pickup before delivery** - Enforced by `AddPickupAndDelivery()`
2. **Same vehicle** - Enforced by `VehicleVar` equality
3. **Capacity limits** - Enforced by `AddDimensionWithVehicleCapacity()`
4. **Distance limits** - Enforced by `AddDimension()`

### Soft Constraints (PREFER to satisfy):
1. **Minimize distance** - Enforced by `SetGlobalSpanCostCoefficient(100)`
2. **Priority orders** - Enforced by disjunction penalties (if used)

---

## 💡 Real-World Usage Example

```python
# Load from database
locations = query_locations_from_db()
orders = query_orders_from_db()
vehicles = query_vehicles_from_db()

# Create REAL distance matrix (use Google Maps API, OpenStreetMap, etc.)
distance_matrix = create_real_distance_matrix(locations)

# Solve
optimizer = LogisticsOptimizer(locations, vehicles, orders, distance_matrix)
result = optimizer.solve(time_limit_seconds=30)

# Save results
if result.is_feasible:
    save_routes_to_database(result.routes)
    print(f"Optimized routes saved! Total distance: {result.total_distance:.2f} km")
else:
    print(f"Problem infeasible: {result.constraint_violations}")
    print(f"Unserved orders: {result.unserved_orders}")
```

---

## 🎓 Key Concepts

### What is Constraint Programming?
Instead of telling the solver HOW to solve, we:
1. Define WHAT constraints must be satisfied
2. Define WHAT to optimize (minimize distance)
3. Solver finds the best solution automatically

### What is a Vehicle Routing Problem (VRP)?
Classic optimization problem:
- Given: Locations, vehicles, demands
- Find: Optimal routes
- Constraints: Capacity, time, distance
- Objective: Minimize cost/distance

### Why Use OR-Tools?
- Industry-standard optimization library
- Handles complex constraints automatically
- Much faster than brute-force
- Scales to hundreds of locations

---

## 📈 Performance Tips

| Scenario | Solution |
|----------|----------|
| Solver too slow | Reduce time_limit, use simpler first solution strategy |
| Solution not optimal | Increase time_limit, try different metaheuristics |
| No feasible solution | Relax constraints (increase capacity/distance) |
| Too many unserved orders | Add more vehicles, increase capacities |

---

## 🔗 Resources

- [OR-Tools VRP Documentation](https://developers.google.com/optimization/routing)
- [Test Suite](test_optimizer.py) - Comprehensive tests showing how it works
- [Example Usage](example_usage.py) - Complete working examples

---

**Run tests:** `python -m optimization.test_optimizer`  
**Run example:** `python -m optimization.example_usage`
