#                                                     4. Nature-Inspired Penguin Search Optimization Algorithm


def calculate_matching_fitness(matching_solution):
    """Calculates the total compatibility score for a given matching."""
    total_score = 0
    for rider, driver in matching_solution:
        # We need to calculate this score using the *initial* state or carefully
        # if the driver's current passengers affect the score. For simplicity,
        # we'll assume `calculate_compatibility_score` is based on current state at match time.
        # Here, for fitness, we just sum the original scores.
        # This implies we assume the driver is empty when taking first rider.
        # For multi-rider drivers, this needs more careful scoring (e.g., detour cost).
        # Let's simplify: score is just for the given (rider, driver) pair.
        total_score += calculate_compatibility_score(rider, driver)
    return total_score


def generate_random_valid_matching(riders, drivers, operations_count_ref):
    """
    Generates a single random valid matching.
    Operations count is updated by reference.
    """
    current_matches = []
    available_riders = list(riders)
    available_drivers_map = {d.id: Driver(d.id, d.current_location, d.capacity) for d in drivers}
    for d in available_drivers_map.values():
        d.current_passengers = [] # Ensure it's clean

    random.shuffle(available_riders) # Randomize order of riders

    for rider in available_riders:
        operations_count_ref[0] += 1

        # Find drivers who can take this rider
        eligible_drivers = [d_copy for d_id, d_copy in available_drivers_map.items()
                            if d_copy.remaining_capacity >= rider.passengers_needed and
                               calculate_compatibility_score(rider, d_copy) > 0]

        if eligible_drivers:
            # Pick a random eligible driver
            driver_copy = random.choice(eligible_drivers)

            # Find the original driver object to pass into the final match
            original_driver = next(d for d in drivers if d.id == driver_copy.id)

            # Assign rider to the *copy* to update its state for subsequent rider checks
            driver_copy.assign_rider(rider)
            current_matches.append((rider, original_driver))
            # The rider is now considered "matched" for this solution generation process
            # (though we don't set rider.is_matched on the original object yet).

    return current_matches


def perturb_matching(original_matching, all_riders, all_drivers, operations_count_ref):
    """
    Creates a new matching by perturbing an existing one.
    E.g., unmatch a random pair and try to re-match the rider elsewhere,
    or swap drivers for two riders.
    """
    new_matching = list(original_matching) # Start with a copy

    if not new_matching: # If no matches, try to add one
        return generate_random_valid_matching(all_riders, all_drivers, operations_count_ref)

    # Option 1: Unmatch a random rider and try to rematch them
    rider_to_unmatch, old_driver = random.choice(new_matching)
    new_matching.remove((rider_to_unmatch, old_driver))

    # Recreate driver states for the new_matching
    temp_drivers_state = {d.id: Driver(d.id, d.current_location, d.capacity) for d in all_drivers}
    for r, d_orig in new_matching:
        temp_drivers_state[d_orig.id].assign_rider(r)

    found_new_match = False

    # Try to find a new driver for the un-matched rider
    shuffled_drivers_ids = list(temp_drivers_state.keys())
    random.shuffle(shuffled_drivers_ids)

    for driver_id in shuffled_drivers_ids:
        operations_count_ref[0] += 1
        driver_copy = temp_drivers_state[driver_id]
        original_driver = next(d for d in all_drivers if d.id == driver_id) # Get original driver object

        if driver_copy.remaining_capacity >= rider_to_unmatch.passengers_needed and \
           calculate_compatibility_score(rider_to_unmatch, driver_copy) > 0:

            driver_copy.assign_rider(rider_to_unmatch) # Update copy's state
            new_matching.append((rider_to_unmatch, original_driver))
            found_new_match = True
            break

    if not found_new_match:
        # If the rider couldn't be rematched, add them back with their old driver
        # (This avoids losing a match if no better option is found, or just leaves them unmatched for this iteration)
        # For simplicity, let's just leave the rider unmatched if no better alternative.
        # Or, if we want to ensure *all* riders are always in the potential matching set:
        # new_matching.append((rider_to_unmatch, old_driver))
        pass

    return new_matching


def penguin_search_matching(riders, drivers, population_size=10, generations=50):
    """
    Penguin Search Optimization (PSO)-like approach for matching.
    Uses an iterative, population-based improvement strategy.
    """
    operations_count = [0] # Use a list to allow modification in nested functions

    # Step 1: Initialize population of random valid matchings
    population = []
    for _ in range(population_size):
        population.append(generate_random_valid_matching(riders, drivers, operations_count))
        operations_count[0] += 1 # Count population generation

    # Evaluate initial population
    best_matching = None
    best_fitness = -float('inf')

    for p_idx, matching in enumerate(population):
        fitness = calculate_matching_fitness(matching)
        if fitness > best_fitness:
            best_fitness = fitness
            best_matching = matching
        # Store fitness with the matching for easier access
        population[p_idx] = (matching, fitness)
        operations_count[0] += 1 # Count fitness calculation

    # Step 2: Iterate through generations
    for gen in range(generations):
        new_population = []
        for matching, fitness in population:
            operations_count[0] += 1 # Count iteration over population member

            # "Penguin explores": Create a perturbed version (neighbor)
            new_candidate_matching = perturb_matching(matching, riders, drivers, operations_count)
            new_candidate_fitness = calculate_matching_fitness(new_candidate_matching)
            operations_count[0] += 1 # Count fitness calculation

            # "Penguin moves towards better food source": If new is better, replace
            if new_candidate_fitness > fitness:
                new_population.append((new_candidate_matching, new_candidate_fitness))
            else:
                new_population.append((matching, fitness)) # Keep old if no improvement

            # Update global best
            if new_candidate_fitness > best_fitness:
                best_fitness = new_candidate_fitness
                best_matching = new_candidate_matching

        population = new_population # Update population for next generation

    # Apply the best found matching to the original driver objects
    # Reset drivers first (handled by timed_matching_algorithm, but good to be explicit here)
    for driver in drivers:
        driver.reset()
    for rider in riders:
        rider.is_matched = False
        rider.matched_driver = None

    if best_matching:
        for rider, driver in best_matching:
            driver.assign_rider(rider) # Assign to original driver objects

    return best_matching, operations_count[0]

# --- Timed Penguin Search Matching ---
def timed_penguin_search_matching(riders, drivers, population_size=10, generations=50):
    # Pass population_size and generations as *args to timed_matching_algorithm
    return timed_matching_algorithm(penguin_search_matching, riders, drivers,
                                    population_size=population_size, generations=generations)

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


# --- Penguin Search Optimization-like Matching Algorithm (copied for self-containment) ---
def calculate_matching_fitness(matching_solution):
    """Calculates the total compatibility score for a given matching."""
    total_score = 0
    for rider, driver in matching_solution:
        # We need to calculate this score using the *initial* state or carefully
        # if the driver's current passengers affect the score. For simplicity,
        # we'll assume `calculate_compatibility_score` is based on current state at match time.
        # Here, for fitness, we just sum the original scores.
        # This implies we assume the driver is empty when taking first rider.
        # For multi-rider drivers, this needs more careful scoring (e.g., detour cost).
        # Let's simplify: score is just for the given (rider, driver) pair.
        total_score += calculate_compatibility_score(rider, driver)
    return total_score


def generate_random_valid_matching(riders, drivers, operations_count_ref):
    """
    Generates a single random valid matching.
    Operations count is updated by reference.
    """
    current_matches = []
    available_riders = list(riders)
    available_drivers_map = {d.id: Driver(d.id, d.current_location, d.capacity) for d in drivers}
    for d in available_drivers_map.values():
        d.current_passengers = [] # Ensure it's clean

    random.shuffle(available_riders) # Randomize order of riders

    for rider in available_riders:
        operations_count_ref[0] += 1

        # Find drivers who can take this rider
        eligible_drivers = [d_copy for d_id, d_copy in available_drivers_map.items()
                            if d_copy.remaining_capacity >= rider.passengers_needed and
                               calculate_compatibility_score(rider, d_copy) > 0]

        if eligible_drivers:
            # Pick a random eligible driver
            driver_copy = random.choice(eligible_drivers)

            # Find the original driver object to pass into the final match
            original_driver = next(d for d in drivers if d.id == driver_copy.id)

            # Assign rider to the *copy* to update its state for subsequent rider checks
            driver_copy.assign_rider(rider)
            current_matches.append((rider, original_driver))
            # The rider is now considered "matched" for this solution generation process
            # (though we don't set rider.is_matched on the original object yet).

    return current_matches


def perturb_matching(original_matching, all_riders, all_drivers, operations_count_ref):
    """
    Creates a new matching by perturbing an existing one.
    E.g., unmatch a random pair and try to re-match the rider elsewhere,
    or swap drivers for two riders.
    """
    new_matching = list(original_matching) # Start with a copy

    if not new_matching: # If no matches, try to add one
        return generate_random_valid_matching(all_riders, all_drivers, operations_count_ref)

    # Option 1: Unmatch a random rider and try to rematch them
    rider_to_unmatch, old_driver = random.choice(new_matching)
    new_matching.remove((rider_to_unmatch, old_driver))

    # Recreate driver states for the new_matching
    temp_drivers_state = {d.id: Driver(d.id, d.current_location, d.capacity) for d in all_drivers}
    for r, d_orig in new_matching:
        temp_drivers_state[d_orig.id].assign_rider(r)

    found_new_match = False

    # Try to find a new driver for the un-matched rider
    shuffled_drivers_ids = list(temp_drivers_state.keys())
    random.shuffle(shuffled_drivers_ids)

    for driver_id in shuffled_drivers_ids:
        operations_count_ref[0] += 1
        driver_copy = temp_drivers_state[driver_id]
        original_driver = next(d for d in all_drivers if d.id == driver_copy.id) # Get original driver object

        if driver_copy.remaining_capacity >= rider_to_unmatch.passengers_needed and \
           calculate_compatibility_score(rider_to_unmatch, driver_copy) > 0:

            driver_copy.assign_rider(rider_to_unmatch) # Update copy's state
            new_matching.append((rider_to_unmatch, original_driver))
            found_new_match = True
            break

    if not found_new_match:
        # If the rider couldn't be rematched, add them back with their old driver
        # (This avoids losing a match if no better option is found, or just leaves them unmatched for this iteration)
        # For simplicity, let's just leave the rider unmatched if no better alternative.
        # Or, if we want to ensure *all* riders are always in the potential matching set:
        # new_matching.append((rider_to_unmatch, old_driver))
        pass

    return new_matching


def penguin_search_matching(riders, drivers, population_size=10, generations=50):
    """
    Penguin Search Optimization (PSO)-like approach for matching.
    Uses an iterative, population-based improvement strategy.
    """
    operations_count = [0] # Use a list to allow modification in nested functions

    # Step 1: Initialize population of random valid matchings
    population = []
    for _ in range(population_size):
        population.append(generate_random_valid_matching(riders, drivers, operations_count))
        operations_count[0] += 1 # Count population generation

    # Evaluate initial population
    best_matching = None
    best_fitness = -float('inf')

    for p_idx, matching in enumerate(population):
        fitness = calculate_matching_fitness(matching)
        if fitness > best_fitness:
            best_fitness = fitness
            best_matching = matching
        # Store fitness with the matching for easier access
        population[p_idx] = (matching, fitness)
        operations_count[0] += 1 # Count fitness calculation

    # Step 2: Iterate through generations
    for gen in range(generations):
        new_population = []
        for matching, fitness in population:
            operations_count[0] += 1 # Count iteration over population member

            # "Penguin explores": Create a perturbed version (neighbor)
            new_candidate_matching = perturb_matching(matching, riders, drivers, operations_count)
            new_candidate_fitness = calculate_matching_fitness(new_candidate_matching)
            operations_count[0] += 1 # Count fitness calculation

            # "Penguin moves towards better food source": If new is better, replace
            if new_candidate_fitness > fitness:
                new_population.append((new_candidate_matching, new_candidate_fitness))
            else:
                new_population.append((matching, fitness)) # Keep old if no improvement

            # Update global best
            if new_candidate_fitness > best_fitness:
                best_fitness = new_candidate_fitness
                best_matching = new_candidate_matching

        population = new_population # Update population for next generation

    # Apply the best found matching to the original driver objects
    # Reset drivers first (handled by timed_matching_algorithm, but good to be explicit here)
    for driver in drivers:
        driver.reset()
    for rider in riders:
        rider.is_matched = False
        rider.matched_driver = None

    if best_matching:
        for rider, driver in best_matching:
            driver.assign_rider(rider) # Assign to original driver objects

    return best_matching, operations_count[0]

# --- Timed Penguin Search Matching ---
def timed_penguin_search_matching(riders, drivers, population_size=10, generations=50):
    # Pass population_size and generations as *args to timed_matching_algorithm
    return timed_matching_algorithm(penguin_search_matching, riders, drivers,
                                    population_size=population_size, generations=generations)

# --- Main plotting logic for Penguin Search ---

# Define a range of input sizes to test
sizes_penguin = np.arange(5, 405, 5) # Number of riders, drivers will be half of riders

# Store results for penguin search algorithm for average, best, and worst cases
ps_avg_times_plot = []
ps_avg_ops_plot = []
ps_best_times_plot = []
ps_best_ops_plot = []
ps_worst_times_plot = []
ps_worst_ops_plot = []

print("--- Running simulations for various input sizes (Penguin Search Matching) ---")
for num_riders in sizes_penguin:
    num_drivers = num_riders // 2 # Keep drivers proportional to riders
    if num_drivers == 0: num_drivers = 1 # Ensure at least one driver

    # Average Case
    riders_avg, drivers_avg = generate_sample_data(num_riders, num_drivers, grid_size=100)
    _, ops_avg, time_avg = timed_penguin_search_matching(riders_avg, drivers_avg)
    ps_avg_times_plot.append(time_avg)
    ps_avg_ops_plot.append(ops_avg)

    # Best Case
    riders_best, drivers_best = generate_sample_data_best_case(num_riders, num_drivers, grid_size=100)
    _, ops_best, time_best = timed_penguin_search_matching(riders_best, drivers_best)
    ps_best_times_plot.append(time_best)
    ps_best_ops_plot.append(ops_best)

    # Worst Case
    riders_worst, drivers_worst = generate_sample_data_worst_case(num_riders, num_drivers, grid_size=100)
    _, ops_worst, time_worst = timed_penguin_search_matching(riders_worst, drivers_worst)
    ps_worst_times_plot.append(time_worst)
    ps_worst_ops_plot.append(ops_worst)

print("--- Penguin Search Matching Simulation complete ---")

# Plotting results for Penguin Search
plt.figure(figsize=(14, 6))

# Plot Time Complexity
plt.subplot(1, 2, 1) # 1 row, 2 columns, first plot
plt.plot(sizes_penguin, ps_avg_times_plot, 'o-', label='Penguin Search Time (Average)')
plt.plot(sizes_penguin, ps_best_times_plot, 'o-', label='Penguin Search Time (Best Case)')
plt.plot(sizes_penguin, ps_worst_times_plot, 'o-', label='Penguin Search Time (Worst Case)')
plt.xlabel('Number of Riders (Input Size)')
plt.ylabel('Time Taken (seconds)')
plt.title('Penguin Search Algorithm Time Complexity')
plt.legend()
plt.grid(True)

# Plot Operations Count
plt.subplot(1, 2, 2) # 1 row, 2 columns, second plot
plt.plot(sizes_penguin, ps_avg_ops_plot, 'o-', label='Penguin Search Operations (Average)')
plt.plot(sizes_penguin, ps_best_ops_plot, 'o-', label='Penguin Search Operations (Best Case)')
plt.plot(sizes_penguin, ps_worst_ops_plot, 'o-', label='Penguin Search Operations (Worst Case)')
plt.xlabel('Number of Riders (Input Size)')
plt.ylabel('Operations Count')
plt.title('Penguin Search Algorithm Operations Count')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()


#                                                                        Analysis of Algorithms


# --- Main Execution ---
if __name__ == "__main__":
    NUM_RIDERS = 20
    NUM_DRIVERS = 10
    GRID_SIZE = 100

    print(f"--- Running Matching Algorithms for {NUM_RIDERS} Riders, {NUM_DRIVERS} Drivers ---")
    print("-" * 60)

    # Generate initial data (will be copied/reset for each algorithm run by timed_matching_algorithm)
    original_riders, original_drivers = generate_sample_data(NUM_RIDERS, NUM_DRIVERS, GRID_SIZE)

    # Function to print results
    def print_results(algo_name, matches, ops_count, time_taken, riders_list, drivers_list):
        total_score = calculate_matching_fitness(matches)
        unmatched_riders = [r for r in riders_list if not r.is_matched]
        matched_drivers_count = len(set(d.id for r, d in matches))

        print(f"\n### {algo_name} ###")
        print(f"Time Taken: {time_taken:.6f} seconds")
        print(f"Operations Count: {ops_count}")
        print(f"Total Matches Made: {len(matches)}")
        print(f"Total Compatibility Score: {total_score:.2f}")
        print(f"Unmatched Riders: {len(unmatched_riders)}")
        print(f"Drivers Utilized: {matched_drivers_count}/{len(drivers_list)}")

        # Optional: Print details of first few matches
        # print("Sample Matches:")
        # for i, (rider, driver) in enumerate(matches[:5]):
        #     print(f"  Rider {rider.id} matched with Driver {driver.id} (Score: {calculate_compatibility_score(rider, driver):.2f})")
        # if len(matches) > 5:
        #     print("  ...")


    # --- Run Brute Force ---
    print("--- Running Brute Force ---")
    bf_matches, bf_ops, bf_time = timed_brute_force_matching(original_riders, original_drivers)
    print_results("Brute Force Matching", bf_matches, bf_ops, bf_time, original_riders, original_drivers)

    # --- Run Greedy Matching ---
    print("\n" + "-" * 60)
    print("--- Running Greedy Matching ---")
    greedy_matches, greedy_ops, greedy_time = timed_greedy_matching(original_riders, original_drivers)
    print_results("Greedy Matching", greedy_matches, greedy_ops, greedy_time, original_riders, original_drivers)

    # --- Run Max Flow Matching (Conceptual) ---
    print("\n" + "-" * 60)
    print("--- Running Max Flow Matching (Conceptual) ---")
    mf_matches, mf_ops, mf_time = timed_max_flow_matching(original_riders, original_drivers)
    print_results("Max Flow Matching", mf_matches, mf_ops, mf_time, original_riders, original_drivers)

    # --- Run Penguin Search Optimization-like Matching ---
    print("\n" + "-" * 60)
    print("--- Running Penguin Search Optimization-like Matching ---")
    # Adjust population_size and generations for larger problems or more exploration
    penguin_matches, penguin_ops, penguin_time = timed_penguin_search_matching(original_riders, original_drivers,
                                                                               population_size=20, generations=100)
    print_results("Penguin Search Matching", penguin_matches, penguin_ops, penguin_time, original_riders, original_drivers)
