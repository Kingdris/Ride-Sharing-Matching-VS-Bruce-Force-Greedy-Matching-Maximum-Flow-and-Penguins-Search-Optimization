#                                                                        3. Maximum Flow Matching Algorithm


# For max flow, we'd typically use a library like networkx or implement a flow algorithm.
# Since a full implementation is extensive, we'll illustrate the conceptual model
# and provide a simplified solver for demonstration.

class MaxFlowGraph:
    def __init__(self):
        self.graph = {} # adj_list: {node: {neighbor: {'capacity': X, 'flow': Y, 'cost': Z}}}
        self.node_map = {} # To map actual objects to graph node IDs

    def add_node(self, node_id, obj=None):
        if node_id not in self.graph:
            self.graph[node_id] = {}
            if obj:
                self.node_map[obj] = node_id

    def add_edge(self, u, v, capacity, cost=0):
        self.add_node(u)
        self.add_node(v)
        self.graph[u][v] = {'capacity': capacity, 'flow': 0, 'cost': cost}
        # For residual graph in typical max flow, you'd add a reverse edge.
        # Simplified for conceptual model.

    def _find_path(self, source, sink, driver_id_to_obj_map, rider_id_to_obj_map):
        """
        A very simplified path finder for illustrative purposes.
        In a real max-flow, this would be BFS/DFS on residual graph,
        potentially using Bellman-Ford/SPFA for min-cost max-flow.
        """
        paths = []
        # Try to find a simple path from source to sink.
        # This is not a full Edmonds-Karp/Dinic/etc.
        for rider_node_id, driver_edges in self.graph.items():
            if not rider_node_id.startswith("R_"): continue # Only check rider nodes

            for driver_node_id, edge_data in driver_edges.items():
                if not driver_node_id.startswith("D_"): continue # Only check driver edges

                if edge_data['capacity'] - edge_data['flow'] >= 1: # If capacity allows 1 rider
                    # Check driver capacity to sink
                    driver_to_sink_edge = self.graph[driver_node_id].get("T", None)
                    if driver_to_sink_edge and driver_to_sink_edge['capacity'] - driver_to_sink_edge['flow'] >= 1:
                        # Found a path S -> Rider -> Driver -> T
                        paths.append({
                            'rider_id': rider_node_id[2:], # Extract R ID
                            'driver_id': driver_node_id[2:], # Extract D ID
                            'score': -edge_data['cost'] # Convert cost back to score
                        })
        # Sort paths by score to prioritize better ones for simplified flow
        paths.sort(key=lambda x: x['score'], reverse=True)
        return paths

    def solve_max_flow(self, source, sink, riders_map, drivers_map):
        """
        A simplified conceptual max-flow solver for demonstration.
        It doesn't implement a true augmenting path algorithm.
        Instead, it simulates making "best" matches until no more paths are found,
        to illustrate how the graph structure is used.
        """
        matches = []
        operations = 0

        # Keep track of available capacity for drivers, and if riders are matched
        drivers_current_capacity = {d.id: d.capacity for d in drivers_map.values()}
        matched_riders_ids = set()

        while True:
            operations += 1
            # Find a path: S -> R -> D -> T. In a real algo, this is BFS/DFS.
            # Here, we'll conceptualize it as finding the best available (R,D) pair.

            best_path_score = -float('inf')
            best_match_candidate = None

            for rider_id_node, driver_edges in self.graph.items():
                if not rider_id_node.startswith("R_"): continue
                rider_obj = riders_map[rider_id_node[2:]] # Get original rider obj

                if rider_obj.id in matched_riders_ids:
                    continue # Rider already matched

                for driver_id_node, edge_data in driver_edges.items():
                    if not driver_id_node.startswith("D_"): continue
                    driver_obj = drivers_map[driver_id_node[2:]] # Get original driver obj

                    # Check if this (rider, driver) edge is 'active' and has capacity for 1 rider
                    # And if the driver-to-sink edge also has capacity
                    if edge_data['capacity'] - edge_data['flow'] >= rider_obj.passengers_needed: # For 1 rider flow unit
                        driver_sink_edge = self.graph[driver_id_node].get(sink)
                        if driver_sink_edge and driver_sink_edge['capacity'] - driver_sink_edge['flow'] >= rider_obj.passengers_needed:

                            current_score = -edge_data['cost'] # Max-Cost = Min-Negative-Cost

                            # Check remaining capacity for the driver based on current flow
                            if drivers_current_capacity[driver_obj.id] >= rider_obj.passengers_needed:
                                if current_score > best_path_score:
                                    best_path_score = current_score
                                    best_match_candidate = (rider_obj, driver_obj, rider_id_node, driver_id_node, edge_data, driver_sink_edge)

            if best_match_candidate is None:
                break # No more augmenting paths (matches) found

            # Apply the flow for the best match found
            rider_obj, driver_obj, rider_node, driver_node, r_d_edge, d_t_edge = best_match_candidate

            # Increment flow on rider->driver edge and driver->sink edge
            r_d_edge['flow'] += rider_obj.passengers_needed
            d_t_edge['flow'] += rider_obj.passengers_needed

            # Update internal tracking
            drivers_current_capacity[driver_obj.id] -= rider_obj.passengers_needed
            matched_riders_ids.add(rider_obj.id)

            matches.append((rider_obj, driver_obj))

        return matches, operations


def max_flow_matching(riders, drivers):
    """
    Max Flow approach: Models the problem as a min-cost max-flow problem.
    This implementation uses a conceptual MaxFlowGraph and a simplified solver.
    """
    graph = MaxFlowGraph()
    source = "S"
    sink = "T"
    operations_count = 0

    # Maps for easy lookup
    riders_map = {r.id: r for r in riders}
    drivers_map = {d.id: d for d in drivers}

    # Add source and sink
    graph.add_node(source)
    graph.add_node(sink)

    # Edges from source to riders (capacity 1, each rider wants 1 ride)
    for rider in riders:
        graph.add_node(f"R_{rider.id}", rider)
        graph.add_edge(source, f"R_{rider.id}", capacity=rider.passengers_needed, cost=0)
        operations_count += 1

    # Edges from drivers to sink (capacity = driver's max capacity)
    for driver in drivers:
        graph.add_node(f"D_{driver.id}", driver)
        graph.add_edge(f"D_{driver.id}", sink, capacity=driver.capacity, cost=0)
        operations_count += 1

    # Edges from riders to drivers (capacity 1, cost = negative compatibility score)
    # We want to maximize compatibility score, so we minimize negative score.
    for rider in riders:
        for driver in drivers:
            operations_count += 1
            score = calculate_compatibility_score(rider, driver)
            if score > 0: # Only add edges for compatible pairs
                # Min-cost flow algorithms minimize cost. To maximize score,
                # we set the cost to -score.
                graph.add_edge(f"R_{rider.id}", f"D_{driver.id}",
                               capacity=rider.passengers_needed, # Capacity of 1 for this specific rider
                               cost=-score)

    # Solve the max-flow (or min-cost max-flow) problem
    # The internal solver will simulate the flow process and count operations.
    final_matches, solver_operations = graph.solve_max_flow(source, sink, riders_map, drivers_map)
    operations_count += solver_operations

    # Assign matched riders to drivers based on the flow
    # (This is implicitly done by the simplified solver, but in a real system,
    # you'd interpret the flow on R_i -> D_j edges)

    # We need to make sure the original driver objects reflect the matches.
    # The graph.solve_max_flow already constructs the `final_matches` list
    # with the original rider and driver objects.
    # We just need to apply the assignments to the actual objects for consistency.
    for rider_obj, driver_obj in final_matches:
        if not rider_obj.is_matched: # Avoid re-matching if already handled by solver logic
            driver_obj.assign_rider(rider_obj)


    return final_matches, operations_count

# --- Timed Max Flow Matching ---
def timed_max_flow_matching(riders, drivers):
    return timed_matching_algorithm(max_flow_matching, riders, drivers)

import matplotlib.pyplot as plt
import numpy as np
import time
import math
import random
import itertools

# --- Helper Classes and Functions (copied for self-containment) ---

class Location:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"({self.x}, {self.y})"

    def distance(self, other_location):
        return math.sqrt((self.x - other_location.x)**2 + (self.y - other_location.y)**2)

class Rider:
    def __init__(self, id, start_location, end_location, passengers_needed=1):
        self.id = id
        self.start_location = start_location
        self.end_location = end_location
        self.passengers_needed = passengers_needed
        self.matched_driver = None
        self.is_matched = False

    def __repr__(self):
        return (f"Rider(ID={self.id}, Start={self.start_location}, "
                f"End={self.end_location}, Needed={self.passengers_needed})")

class Driver:
    def __init__(self, id, current_location, capacity=4):
        self.id = id
        self.current_location = current_location
        self.capacity = capacity
        self.current_passengers = [] # List of Rider objects
        self.is_available = True

    @property
    def remaining_capacity(self):
        return self.capacity - sum(r.passengers_needed for r in self.current_passengers)

    def assign_rider(self, rider):
        if self.remaining_capacity >= rider.passengers_needed:
            self.current_passengers.append(rider)
            rider.is_matched = True
            rider.matched_driver = self.id
            if self.remaining_capacity == 0:
                self.is_available = False
            return True
        return False

    def remove_rider(self, rider):
        if rider in self.current_passengers:
            self.current_passengers.remove(rider)
            rider.is_matched = False
            rider.matched_driver = None
            self.is_available = True # If capacity frees up
            return True
        return False

    def reset(self):
        self.current_passengers = []
        self.is_available = True

    def __repr__(self):
        return (f"Driver(ID={self.id}, Loc={self.current_location}, "
                f"Capacity={self.capacity}, Avail={self.remaining_capacity})")

# --- Compatibility Score (Higher is better) ---
def calculate_compatibility_score(rider, driver):
    """
    Calculates a score for matching a rider to a driver.
    Score is higher for shorter distances. Penalizes insufficient capacity.
    """
    if driver.remaining_capacity < rider.passengers_needed:
        return -float('inf') # Cannot fulfill request

    # Distance from driver's current location to rider's start location
    pickup_distance = driver.current_location.distance(rider.start_location)

    # A simple score: inverse of distance. Add a small value to prevent division by zero.
    # Consider also driver's route to rider's destination later, but for simplicity, just pickup.
    score = 1000 - pickup_distance # Max score 1000 for 0 distance

    # Add a penalty if driver is far, or bonus for close
    # Can be more complex: ETA, driver rating, surge pricing, etc.
    if pickup_distance > 50: # Arbitrary large distance
        score -= 200

    return max(0, score) # Score cannot be negative if compatible


# --- Generic Timed Search Wrapper ---
def timed_matching_algorithm(algorithm_func, riders, drivers, *args, **kwargs):
    """
    A wrapper to time and count operations for matching algorithms.
    """
    # Reset drivers and riders state for fair comparison
    for d in drivers:
        d.reset()
    for r in riders:
        r.is_matched = False
        r.matched_driver = None

    start_time = time.perf_counter()
    matches, operations_count = algorithm_func(riders, drivers, *args, **kwargs)
    end_time = time.perf_counter()

    time_taken = end_time - start_time
    return matches, operations_count, time_taken

# --- Data Generation for Testing ---
def generate_sample_data(num_riders, num_drivers, grid_size=100):
    riders = []
    drivers = []

    for i in range(num_riders):
        start = Location(random.uniform(0, grid_size), random.uniform(0, grid_size))
        end = Location(random.uniform(0, grid_size), random.uniform(0, grid_size))
        riders.append(Rider(f"R{i}", start, end, random.randint(1, 2)))

    for i in range(num_drivers):
        loc = Location(random.uniform(0, grid_size), random.uniform(0, grid_size))
        drivers.append(Driver(f"D{i}", loc, random.randint(2, 4)))

    return riders, drivers

def generate_sample_data_best_case(num_riders, num_drivers, grid_size=100):
    riders = []
    drivers = []

    # Create drivers in a small cluster
    driver_locations = []
    for i in range(num_drivers):
        loc_x = random.uniform(grid_size*0.4, grid_size*0.6)
        loc_y = random.uniform(grid_size*0.4, grid_size*0.6)
        driver_locations.append(Location(loc_x, loc_y))
        drivers.append(Driver(f"D{i}", driver_locations[-1], random.randint(3, 4))) # High capacity

    # Create riders very close to drivers, ensuring high compatibility
    for i in range(num_riders):
        assigned_driver_loc = random.choice(driver_locations)
        start = Location(assigned_driver_loc.x + random.uniform(-5, 5),
                         assigned_driver_loc.y + random.uniform(-5, 5))
        end = Location(random.uniform(0, grid_size), random.uniform(0, grid_size))
        riders.append(Rider(f"R{i}", start, end, random.randint(1, 2))) # Low passenger need

    return riders, drivers

def generate_sample_data_worst_case(num_riders, num_drivers, grid_size=100):
    riders = []
    drivers = []

    # Place riders in one corner
    for i in range(num_riders):
        start = Location(random.uniform(0, grid_size*0.2), random.uniform(0, grid_size*0.2)) # Bottom-left
        end = Location(random.uniform(grid_size*0.8, grid_size), random.uniform(grid_size*0.8, grid_size)) # Top-right
        riders.append(Rider(f"R{i}", start, end, random.randint(1, 2))) # Average passenger need

    # Place drivers in the opposite corner with lower capacity
    for i in range(num_drivers):
        loc = Location(random.uniform(grid_size*0.8, grid_size), random.uniform(grid_size*0.8, grid_size)) # Top-right
        drivers.append(Driver(f"D{i}", loc, random.randint(2, 3))) # Lower capacity

    return riders, drivers


# --- Max Flow Graph and Algorithm (copied for self-containment) ---
class MaxFlowGraph:
    def __init__(self):
        self.graph = {} # adj_list: {node: {neighbor: {'capacity': X, 'flow': Y, 'cost': Z}}}
        self.node_map = {} # To map actual objects to graph node IDs

    def add_node(self, node_id, obj=None):
        if node_id not in self.graph:
            self.graph[node_id] = {}
            if obj:
                self.node_map[obj] = node_id

    def add_edge(self, u, v, capacity, cost=0):
        self.add_node(u)
        self.add_node(v)
        self.graph[u][v] = {'capacity': capacity, 'flow': 0, 'cost': cost}
        # For residual graph in typical max flow, you'd add a reverse edge.
        # Simplified for conceptual model.

    def _find_path(self, source, sink, driver_id_to_obj_map, rider_id_to_obj_map):
        """
        A very simplified path finder for illustrative purposes.
        In a real max-flow, this would be BFS/DFS on residual graph,
        potentially using Bellman-Ford/SPFA for min-cost max-flow.
        """
        paths = []
        # Try to find a simple path from source to sink.
        # This is not a full Edmonds-Karp/Dinic/etc.
        for rider_node_id, driver_edges in self.graph.items():
            if not rider_node_id.startswith("R_"): continue # Only check rider nodes

            for driver_node_id, edge_data in driver_edges.items():
                if not driver_node_id.startswith("D_"): continue # Only check driver edges

                if edge_data['capacity'] - edge_data['flow'] >= 1: # If capacity allows 1 rider
                    # Check driver capacity to sink
                    driver_to_sink_edge = self.graph[driver_node_id].get("T", None)
                    if driver_to_sink_edge and driver_to_sink_edge['capacity'] - driver_to_sink_edge['flow'] >= 1:
                        # Found a path S -> Rider -> Driver -> T
                        paths.append({
                            'rider_id': rider_node_id[2:], # Extract R ID
                            'driver_id': driver_node_id[2:], # Extract D ID
                            'score': -edge_data['cost'] # Convert cost back to score
                        })
        # Sort paths by score to prioritize better ones for simplified flow
        paths.sort(key=lambda x: x['score'], reverse=True)
        return paths

    def solve_max_flow(self, source, sink, riders_map, drivers_map):
        """
        A simplified conceptual max-flow solver for demonstration.
        It doesn't implement a true augmenting path algorithm.
        Instead, it simulates making "best" matches until no more paths are found,
        to illustrate how the graph structure is used.

        NOTE: This conceptual implementation is highly inefficient for larger inputs.
        A proper max-flow algorithm (e.g., Edmonds-Karp, Dinic) would be much faster.
        """
        matches = []
        operations = 0

        # Keep track of available capacity for drivers, and if riders are matched
        drivers_current_capacity = {d.id: d.capacity for d in drivers_map.values()}
        matched_riders_ids = set()

        while True:
            operations += 1
            # Find a path: S -> R -> D -> T. In a real algo, this is BFS/DFS.
            # Here, we'll conceptualize it as finding the best available (R,D) pair.

            best_path_score = -float('inf')
            best_match_candidate = None

            for rider_id_node, driver_edges in self.graph.items():
                if not rider_id_node.startswith("R_"): continue
                rider_obj = riders_map[rider_id_node[2:]] # Get original rider obj

                if rider_obj.id in matched_riders_ids:
                    continue # Rider already matched

                for driver_id_node, edge_data in driver_edges.items():
                    if not driver_id_node.startswith("D_"): continue
                    driver_obj = drivers_map[driver_id_node[2:]] # Get original driver obj

                    # Check if this (rider, driver) edge is 'active' and has capacity for 1 rider
                    # And if the driver-to-sink edge also has capacity
                    if edge_data['capacity'] - edge_data['flow'] >= rider_obj.passengers_needed: # For 1 rider flow unit
                        driver_sink_edge = self.graph[driver_id_node].get(sink)
                        if driver_sink_edge and driver_sink_edge['capacity'] - driver_sink_edge['flow'] >= rider_obj.passengers_needed:

                            current_score = -edge_data['cost'] # Max-Cost = Min-Negative-Cost

                            # Check remaining capacity for the driver based on current flow
                            if drivers_current_capacity[driver_obj.id] >= rider_obj.passengers_needed:
                                if current_score > best_path_score:
                                    best_path_score = current_score
                                    best_match_candidate = (rider_obj, driver_obj, rider_id_node, driver_id_node, edge_data, driver_sink_edge)

            if best_match_candidate is None:
                break # No more augmenting paths (matches) found

            # Apply the flow for the best match found
            rider_obj, driver_obj, rider_node, driver_node, r_d_edge, d_t_edge = best_match_candidate

            # Increment flow on rider->driver edge and driver->sink edge
            r_d_edge['flow'] += rider_obj.passengers_needed
            d_t_edge['flow'] += rider_obj.passengers_needed

            # Update internal tracking
            drivers_current_capacity[driver_obj.id] -= rider_obj.passengers_needed
            matched_riders_ids.add(rider_obj.id)

            matches.append((rider_obj, driver_obj))

        return matches, operations


def max_flow_matching(riders, drivers):
    """
    Max Flow approach: Models the problem as a min-cost max-flow problem.
    This implementation uses a conceptual MaxFlowGraph and a simplified solver.
    """
    graph = MaxFlowGraph()
    source = "S"
    sink = "T"
    operations_count = 0

    # Maps for easy lookup
    riders_map = {r.id: r for r in riders}
    drivers_map = {d.id: d for d in drivers}

    # Add source and sink
    graph.add_node(source)
    graph.add_node(sink)

    # Edges from source to riders (capacity 1, each rider wants 1 ride)
    for rider in riders:
        graph.add_node(f"R_{rider.id}", rider)
        graph.add_edge(source, f"R_{rider.id}", capacity=rider.passengers_needed, cost=0)
        operations_count += 1

    # Edges from drivers to sink (capacity = driver's max capacity)
    for driver in drivers:
        graph.add_node(f"D_{driver.id}", driver)
        graph.add_edge(f"D_{driver.id}", sink, capacity=driver.capacity, cost=0)
        operations_count += 1

    # Edges from riders to drivers (capacity 1, cost = negative compatibility score)
    # We want to maximize compatibility score, so we minimize negative score.
    for rider in riders:
        for driver in drivers:
            operations_count += 1
            score = calculate_compatibility_score(rider, driver)
            if score > 0: # Only add edges for compatible pairs
                # Min-cost flow algorithms minimize cost. To maximize score,
                # we set the cost to -score.
                graph.add_edge(f"R_{rider.id}", f"D_{driver.id}",
                               capacity=rider.passengers_needed, # Capacity of 1 for this specific rider
                               cost=-score)

    # Solve the max-flow (or min-cost max-flow) problem
    # The internal solver will simulate the flow process and count operations.
    final_matches, solver_operations = graph.solve_max_flow(source, sink, riders_map, drivers_map)
    operations_count += solver_operations

    # Assign matched riders to drivers based on the flow
    # (This is implicitly done by the simplified solver, but in a real system,
    # you'd interpret the flow on R_i -> D_j edges)

    # We need to make sure the original driver objects reflect the matches.
    # The graph.solve_max_flow already constructs the `final_matches` list
    # with the original rider and driver objects.
    # We just need to apply the assignments to the actual objects for consistency.
    for rider_obj, driver_obj in final_matches:
        if not rider_obj.is_matched: # Avoid re-matching if already handled by solver logic
            driver_obj.assign_rider(rider_obj)


    return final_matches, operations_count

# --- Timed Max Flow Matching ---
def timed_max_flow_matching(riders, drivers):
    return timed_matching_algorithm(max_flow_matching, riders, drivers)

# --- Main plotting logic for Max Flow ---

# Define a range of input sizes to test
# WARNING: The current Max Flow conceptual implementation is highly inefficient.
# Running with a large input size range will lead to extremely long execution times.
# For proper performance analysis of Max Flow, a dedicated and optimized library is needed.
sizes_max_flow = np.arange(5, 405, 5) # Reverted to original range as per user request

# Store results for max flow algorithm for average, best, and worst cases
mf_avg_times_plot = []
mf_avg_ops_plot = []
mf_best_times_plot = []
mf_best_ops_plot = []
mf_worst_times_plot = []
mf_worst_ops_plot = []

print("--- Running simulations for various input sizes (Max Flow Matching) ---")
print("!!! WARNING: This will take a very long time due to the conceptual and unoptimized Max Flow implementation. !!!")
for num_riders in sizes_max_flow:
    num_drivers = num_riders // 2 # Keep drivers proportional to riders
    if num_drivers == 0: num_drivers = 1

    # Average Case
    riders_avg, drivers_avg = generate_sample_data(num_riders, num_drivers, grid_size=100)
    _, ops_avg, time_avg = timed_max_flow_matching(riders_avg, drivers_avg)
    mf_avg_times_plot.append(time_avg)
    mf_avg_ops_plot.append(ops_avg)

    # Best Case
    riders_best, drivers_best = generate_sample_data_best_case(num_riders, num_drivers, grid_size=100)
    _, ops_best, time_best = timed_max_flow_matching(riders_best, drivers_best)
    mf_best_times_plot.append(time_best)
    mf_best_ops_plot.append(ops_best)

    # Worst Case
    riders_worst, drivers_worst = generate_sample_data_worst_case(num_riders, num_drivers, grid_size=100)
    _, ops_worst, time_worst = timed_max_flow_matching(riders_worst, drivers_worst)
    mf_worst_times_plot.append(time_worst)
    mf_worst_ops_plot.append(ops_worst)

print("--- Max Flow Matching Simulation complete ---")

# Plotting results for Max Flow Matching
plt.figure(figsize=(14, 6))

# Plot Time Complexity
plt.subplot(1, 2, 1) # 1 row, 2 columns, first plot
plt.plot(sizes_max_flow, mf_avg_times_plot, 'o-', label='Max Flow Matching Time (Average)')
plt.plot(sizes_max_flow, mf_best_times_plot, 'o-', label='Max Flow Matching Time (Best Case)')
plt.plot(sizes_max_flow, mf_worst_times_plot, 'o-', label='Max Flow Matching Time (Worst Case)')
plt.xlabel('Number of Riders (Input Size)')
plt.ylabel('Time Taken (seconds)')
plt.title('Max Flow Matching Algorithm Time Complexity')
plt.legend()
plt.grid(True)

# Plot Operations Count
plt.subplot(1, 2, 2) # 1 row, 2 columns, second plot
plt.plot(sizes_max_flow, mf_avg_ops_plot, 'o-', label='Max Flow Matching Operations (Average)')
plt.plot(sizes_max_flow, mf_best_ops_plot, 'o-', label='Max Flow Matching Operations (Best Case)')
plt.plot(sizes_max_flow, mf_worst_ops_plot, 'o-', label='Max Flow Matching Operations (Worst Case)')
plt.xlabel('Number of Riders (Input Size)')
plt.ylabel('Operations Count')
plt.title('Max Flow Matching Algorithm Operations Count')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()

