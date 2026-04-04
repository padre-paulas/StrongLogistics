# Logistics Optimization Engine

## 📦 What This Code Does

This is a **wrapper for Google OR-Tools** that solves the **Vehicle Routing Problem (VRP)** for logistics optimization. It finds optimal routes for delivering goods from suppliers to customers while respecting vehicle capacity and distance constraints.

---

## 🎯 Problem Solved

```
Depot (Warehouse)
    ↓
    | Vehicle departs with goods
    ↓
Supplier (Pickup goods) ───→ Customer (Delivery)
    ↓
    | Vehicle returns to depot
    ↓
Depot
```

**Constraints Handled:**
- ✅ Vehicle capacity limits (volume/weight)
- ✅ Maximum distance per route
- ✅ Pickup must happen before delivery
- ✅ Multiple vehicles with different capacities
- ✅ Priority-based routing (urgent orders first)
- ✅ Different location types (depot, supplier, delivery point, hotspot)

---

## 📁 File Structure

```
optimization/
├── __init__.py              # Package exports
├── models.py                # Data structures (Location, Vehicle, Order, etc.)
├── ortools_wrapper.py       # Main OR-Tools wrapper (LogisticsOptimizer class)
├── example_usage.py         # Complete working example
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd optimization
pip install -r requirements.txt
```

### 2. Run the Example

```bash
python -m optimization.example_usage
```

### 3. Use in Your Code

```python
from optimization import (
    Location, Vehicle, Order, NodeType,
    LogisticsOptimizer, create_distance_matrix
)

# Create locations
locations = [
    Location(id=0, name="Depot", x=0, y=0, type=NodeType.DEPOT),
    Location(id=1, name="Supplier", x=10, y=0, type=NodeType.SUPPLIER),
    Location(id=2, name="Customer", x=20, y=0, type=NodeType.DELIVERY_POINT),
]

# Create orders
orders = [
    Order(id=1, from_location_id=1, to_location_id=2, volume=5.0)
]

# Create vehicles
vehicles = [
    Vehicle(id=1, depot_id=0, capacity=10.0, max_distance=100.0)
]

# Create distance matrix
distance_matrix = create_distance_matrix(locations)

# Solve
optimizer = LogisticsOptimizer(locations, vehicles, orders, distance_matrix)
result = optimizer.solve(time_limit_seconds=10)

# Print results
print(result.summary())
```

---

## 🧠 How the Code Works (Detailed Explanation)

### Core Algorithm: Vehicle Routing Problem (VRP)

The code uses **Google OR-Tools**, which implements a **Constraint Programming** approach:

1. **Model the Problem**
   - Each location is a "node" in a graph
   - Distances between locations are "edges"
   - Vehicles are "resources" with constraints

2. **Add Constraints**
   - **Pickup & Delivery**: Each order requires visiting supplier → customer
   - **Capacity**: Total volume loaded can't exceed vehicle capacity
   - **Distance**: Total route length can't exceed vehicle's max_distance
   - **Time**: Solver has a time limit to find solutions

3. **Optimize**
   - **First Solution**: Uses a heuristic (e.g., PATH_CHEAPEST_ARC)
   - **Improvement**: Uses metaheuristics (e.g., GUIDED_LOCAL_SEARCH) to find better solutions
   - **Objective**: Minimize total distance traveled

---

## 📊 Code Explanation (Line by Line)

### `models.py` - Data Structures

#### `NodeType` Enum
```python
class NodeType(Enum):
    DEPOT = "depo"
    SUPPLIER = "postachalnyk"
    DELIVERY_POINT = "tochka_vygruzky"
    HOTSPOT = "hotspot"
```
Defines the types of locations in your network.

#### `Location`
```python
@dataclass
class Location:
    id: int
    name: str
    x: float
    y: float
    type: NodeType
```
Represents a physical place. `x` and `y` can be:
- GPS coordinates (latitude/longitude)
- Custom coordinate system
- Grid positions

#### `Order`
```python
@dataclass
class Order:
    id: int
    from_location_id: int  # Where to pickup
    to_location_id: int    # Where to deliver
    volume: float          # How much goods
    priority: int          # 1=normal, 2=high, 3=urgent
```
Represents a delivery request. The optimizer ensures:
- Goods are picked up at `from_location_id`
- Goods are delivered to `to_location_id`
- Pickup happens BEFORE delivery

#### `Vehicle`
```python
@dataclass
class Vehicle:
    id: int
    depot_id: int          # Where vehicle starts/ends
    capacity: float        # Max volume it can carry
    max_distance: float    # Max km per route
    cost_per_km: float     # Operating cost
```
Represents a delivery truck/van with physical limits.

#### `DistanceMatrix`
```python
@dataclass
class DistanceMatrix:
    locations: List[Location]
    matrix: List[List[float]]  # matrix[i][j] = distance from i to j
```
Pre-calculated distances between ALL pairs of locations. This is critical because:
- OR-Tools queries this thousands of times during solving
- Should use REAL road distances (not straight-line) in production
- Can be from Google Maps API, OpenStreetMap, etc.

---

### `ortools_wrapper.py` - The Main Solver

#### `LogisticsOptimizer.__init__()`
```python
def __init__(self, locations, vehicles, orders, distance_matrix):
    self.locations = locations
    self.vehicles = vehicles
    self.orders = orders
    self.distance_matrix = distance_matrix
```
**What it does:** Stores all problem data. Creates a mapping from location IDs to indices (OR-Tools uses indices internally).

**Why important:** This is where you inject your database data into the optimizer.

#### `solve()` Method - The Main Entry Point
```python
def solve(self, time_limit_seconds=30, ...):
    # 1. Create OR-Tools manager
    self.manager = pywrapcp.RoutingIndexManager(...)
    
    # 2. Create routing model
    self.routing = pywrapcp.RoutingModel(self.manager)
    
    # 3. Add distance callback
    transit_callback = self._create_distance_matrix_callback()
    
    # 4. Add constraints
    self._setup_pickup_delivery_pairs(self.orders)
    self._setup_capacity_constraints(order_demand)
    self._setup_distance_constraints()
    
    # 5. Set search parameters
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    
    # 6. Solve!
    solution = self.routing.SolveWithParameters(search_parameters)
    
    # 7. Extract results
    return self._extract_solution(solution)
```

**Step-by-step explanation:**

1. **RoutingIndexManager**: Manages the node indices OR-Tools uses internally
2. **RoutingModel**: The actual optimization model
3. **Distance Callback**: Function OR-Tools calls to get distance between any two nodes
4. **Constraints**: 
   - Pickup & Delivery pairs ensure order fulfillment
   - Capacity prevents overloading vehicles
   - Distance prevents routes from exceeding limits
5. **Search Parameters**: Control how OR-Tools searches for solutions
6. **Solve**: Runs the optimization algorithm
7. **Extract Solution**: Converts OR-Tools format to our clean data structures

#### `_setup_pickup_delivery_pairs()` - Critical Constraint
```python
def _setup_pickup_delivery_pairs(self, orders):
    for order in orders:
        pickup_index = self.location_id_to_index[order.from_location_id]
        delivery_index = self.location_id_to_index[order.to_location_id]
        
        # Enforce pickup before delivery
        self.routing.AddPickupAndDelivery(pickup_node, delivery_node)
        
        # Same vehicle must handle both
        self.routing.solver().Add(
            self.routing.VehicleVar(pickup_node) == 
            self.routing.VehicleVar(delivery_node)
        )
```

**What it does:**
- Links supplier visits to customer deliveries
- Ensures the SAME vehicle does both pickup and delivery
- Enforces ordering (pickup BEFORE delivery)

**Why important:** This is the core logistics constraint - you can't deliver what you haven't picked up!

#### `_setup_capacity_constraints()` - Volume Limits
```python
def _setup_capacity_constraints(self, order_demand):
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

**What it does:**
- Tracks cumulative load on vehicle at every point in route
- Ensures load never exceeds capacity
- The `* 1000` scaling is because OR-Tools works with integers

**Why important:** Prevents assigning 30m³ of goods to a 20m³ truck!

#### `_setup_distance_constraints()` - Route Length Limits
```python
def _setup_distance_constraints(self):
    self.routing.AddDimensionWithVehicleTransit(
        transit_callback_index,
        0,  # No slack
        [int(v.max_distance * 1000) for v in self.vehicles],
        True,
        "distance"
    )
```

**What it does:**
- Tracks cumulative distance traveled by each vehicle
- Hard constraint: route can't exceed `max_distance`

**Why important:** Real vehicles have limits (fuel, driver hours, etc.)

---

## 🔧 Integration Guide (For Next Team Member)

### Database Schema Example

```sql
CREATE TABLE locations (
    id INT PRIMARY KEY,
    name VARCHAR(255),
    lat FLOAT,
    lng FLOAT,
    type ENUM('depo', 'postachalnyk', 'tochka_vygruzky', 'hotspot')
);

CREATE TABLE orders (
    id INT PRIMARY KEY,
    supplier_id INT REFERENCES locations(id),
    delivery_point_id INT REFERENCES locations(id),
    volume FLOAT,
    priority INT DEFAULT 1
);

CREATE TABLE vehicles (
    id INT PRIMARY KEY,
    depot_id INT REFERENCES locations(id),
    capacity FLOAT,
    max_distance FLOAT
);

CREATE TABLE routes (
    id INT PRIMARY KEY,
    vehicle_id INT,
    route_order INT,
    location_id INT REFERENCES locations(id),
    distance_from_prev FLOAT
);
```

### Python Integration Code

```python
import psycopg2  # or your database driver
from optimization import *

def load_from_database(db_connection):
    """Load problem data from database"""
    cursor = db_connection.cursor()
    
    # Load locations
    cursor.execute("SELECT id, name, lat, lng, type FROM locations")
    locations = [
        Location(id=row[0], name=row[1], x=row[2], y=row[3], type=NodeType(row[4]))
        for row in cursor.fetchall()
    ]
    
    # Load orders
    cursor.execute("SELECT id, supplier_id, delivery_point_id, volume, priority FROM orders")
    orders = [
        Order(id=row[0], from_location_id=row[1], to_location_id=row[2], 
              volume=row[3], priority=row[4])
        for row in cursor.fetchall()
    ]
    
    # Load vehicles
    cursor.execute("SELECT id, depot_id, capacity, max_distance FROM vehicles")
    vehicles = [
        Vehicle(id=row[0], depot_id=row[1], capacity=row[2], max_distance=row[3])
        for row in cursor.fetchall()
    ]
    
    return locations, orders, vehicles

def save_results_to_database(result: OptimizationResult, db_connection):
    """Save optimized routes back to database"""
    cursor = db_connection.cursor()
    
    for route in result.routes:
        for stop_idx, stop in enumerate(route.stops):
            cursor.execute("""
                INSERT INTO routes (vehicle_id, route_order, location_id, distance_from_prev)
                VALUES (%s, %s, %s, %s)
            """, (
                route.vehicle_id,
                stop_idx,
                stop.location_id,
                stop.arrival_distance
            ))
    
    db_connection.commit()

# Usage
db_conn = psycopg2.connect("your_connection_string")
locations, orders, vehicles = load_from_database(db_conn)

# Create distance matrix (use REAL distances!)
distance_matrix = create_distance_matrix(locations)

# Solve
optimizer = LogisticsOptimizer(locations, vehicles, orders, distance_matrix)
result = optimizer.solve(time_limit_seconds=30)

# Save results
save_results_to_database(result, db_conn)
```

---

## 📈 Solver Parameters Explained

### `time_limit_seconds`
- **What**: Maximum time to spend searching for solutions
- **Trade-off**: More time = better solutions, but slower
- **Recommendation**: 10-30 seconds for hackathon, 60+ for production

### `first_solution_strategy`
Options (best to worst):
1. `"PATH_CHEAPEST_ARC"` - Greedy, picks shortest edges first ⚡ **FAST**
2. `"PARALLEL_CHEAPEST_INSERTION"` - Builds routes in parallel
3. `"SAVINGS"` - Clarke-Wright savings algorithm
4. `"SWEEP"` - Sweeps around depot

### `local_search_metaheuristic`
Options (best to worst):
1. `"GUIDED_LOCAL_SEARCH"` - Escapes local optima 🏆 **RECOMMENDED**
2. `"SIMULATED_ANNEALING"` - Probabilistic acceptance
3. `"TABU_SEARCH"` - Avoids recent moves

---

## 🎓 Key Concepts Explained

### Why Integer Scaling (`* 1000`)?
OR-Tools' constraint solver works with **integers only**. We multiply floats by 1000 to preserve precision:
```python
distance = 12.345 km
# Stored as: 12345 (integer)
# Retrieved as: 12345 / 1000 = 12.345 km
```

### What is a "Callback"?
A function OR-Tools calls to ask questions:
```python
def distance_callback(from_index, to_index):
    return distance_between(from_index, to_index)
```
OR-Tools calls this thousands of times during solving to build its internal model.

### What are "Dimensions"?
Dimensions track cumulative quantities along routes:
- **Capacity dimension**: Tracks volume loaded at each stop
- **Distance dimension**: Tracks total distance traveled

### What is "Constraint Programming"?
Instead of telling the solver HOW to solve, we:
1. Define WHAT constraints must be satisfied
2. Define WHAT to optimize (minimize distance)
3. Solver finds the best solution automatically

---

## 🐛 Troubleshooting

### "No feasible solution found"
**Causes:**
- Orders too large for vehicle capacities
- Distances too far for max_distance limits
- Constraints too restrictive

**Fix:**
- Increase vehicle capacities
- Increase max_distance
- Check if orders can physically fit

### Solver Too Slow
**Fix:**
- Reduce `time_limit_seconds`
- Use simpler first solution strategy
- Reduce problem size (split into regions)

### Solution Not Optimal
**Fix:**
- Increase `time_limit_seconds`
- Try different metaheuristics
- Run multiple times and pick best

---

## 📞 Quick API Reference

| Class/Method | Purpose |
|--------------|---------|
| `Location` | Represents a place (depot, supplier, customer) |
| `Order` | Delivery request (from → to, with volume) |
| `Vehicle` | Truck with capacity and distance limits |
| `LogisticsOptimizer` | Main solver class |
| `optimizer.solve()` | Find optimal routes |
| `result.summary()` | Print human-readable results |
| `result.routes` | List of vehicle routes |
| `result.is_feasible` | Whether all constraints satisfied |

---

## 🏆 Hackathon Tips

1. **Start Simple**: Test with 3-5 locations first
2. **Visualize**: Plot routes on a map to verify they make sense
3. **Real Distances**: Use OpenStreetMap or Google Maps API for distance matrix
4. **Iterate**: Run solver multiple times with different parameters
5. **Demo**: Use `result.summary()` for impressive output!

---

## 🔗 Resources

- [OR-Tools VRP Documentation](https://developers.google.com/optimization/routing)
- [OR-Tools Python Examples](https://github.com/google/or-tools/tree/stable/examples/python)
- [Vehicle Routing Problem Explained](https://en.wikipedia.org/wiki/Vehicle_routing_problem)

---

**Good luck with your hackathon! 🚀**
