#!/usr/bin/env python3

import os
import re
import math
import matplotlib.pyplot as plt

# ---------------------------- Configuration ---------------------------- #

# Directory containing the experiment output files
OUTPUT_DIR = "./experiment_results"

# Regular expression to parse filenames
# Expected format: exp_<CACHE_SIZE>_<COMPRESSION_TYPE>.txt
FILENAME_REGEX = r'exp_(\d+)_(sw|hw)\.txt$'

# Regular expression to parse the mixgraph run time in seconds
# It looks for a line starting with 'mixgraph' and captures the number before 'seconds'
MIXGRAPH_TIME_REGEX = r'mixgraph\s*:\s*[\d\.]+\s*micros/op\s*[\d\.]+\s*ops/sec\s*([\d\.]+)\s*seconds'

# ---------------------------- Parsing Function ---------------------------- #

def parse_experiment_files(output_dir):
    """
    Parses the experiment output files and extracts run times.

    Args:
        output_dir (str): Path to the directory containing experiment output files.

    Returns:
        dict: A dictionary mapping cache sizes to their SW and HW run times.
              Format: { cache_size_in_bytes: {'sw': sw_time, 'hw': hw_time} }
    """
    experiment_data = {}

    # List all files in the output directory
    for filename in os.listdir(output_dir):
        filepath = os.path.join(output_dir, filename)

        # Match the filename against the regex
        match = re.match(FILENAME_REGEX, filename)
        if not match:
            print(f"Skipping unrecognized file format: {filename}")
            continue

        cache_size_str, compression_type = match.groups()
        cache_size = int(cache_size_str)  # in bytes

        # Initialize the dictionary entry if not present
        if cache_size not in experiment_data:
            experiment_data[cache_size] = {}

        # Read the file and extract the run time
        try:
            with open(filepath, 'r') as file:
                content = file.read()

            # Search for the mixgraph run time
            time_match = re.search(MIXGRAPH_TIME_REGEX, content)
            if time_match:
                run_time_seconds = float(time_match.group(1))
                experiment_data[cache_size][compression_type] = run_time_seconds
                print(f"Parsed {compression_type.upper()} run time for cache size {cache_size} bytes: {run_time_seconds} seconds")
            else:
                print(f"Could not find mixgraph run time in file: {filename}")
        except Exception as e:
            print(f"Error reading file {filename}: {e}")

    return experiment_data

# ---------------------------- Plotting Function ---------------------------- #

def plot_time_differences(experiment_data):
    """
    Plots the difference between SW and HW run times against cache sizes.

    Args:
        experiment_data (dict): Parsed experiment data.
    """
    cache_sizes = []
    time_differences = []

    for cache_size in sorted(experiment_data.keys()):
        data = experiment_data[cache_size]
        if 'sw' in data and 'hw' in data:
            sw_time = data['sw']
            hw_time = data['hw']
            difference = sw_time - hw_time  # SW - HW
            cache_sizes.append(cache_size / (1024 * 1024))  # Convert bytes to MB
            time_differences.append(difference)
            print(f"Cache Size: {cache_size} bytes ({cache_size / (1024 * 1024)} MB) - SW Time: {sw_time}s, HW Time: {hw_time}s, Difference: {difference}s")
        else:
            print(f"Missing SW or HW data for cache size {cache_size} bytes. Skipping.")

    if not cache_sizes:
        print("No complete data to plot.")
        return

    # Create the plot
    plt.figure(figsize=(10, 6))
    plt.plot(cache_sizes, time_differences, marker='o', linestyle='-', color='b')
    plt.title('Absolute Speedup From IAA vs Cache Size')
    plt.xlabel('Cache Size (MB)')
    plt.ylabel('Absolute Speedup (s)')
    plt.grid(True)
    plt.axhline(0, color='red', linestyle='--')  # Reference line at y=0
    plt.tight_layout()

    # Save the plot
    plot_filename = 'absolute_iaa_speedup.png'
    plt.savefig(plot_filename)
    print(f"Plot saved as {plot_filename}")

    # Show the plot
    plt.show()

def plot_time_differences_log2(experiment_data):
    """
    Plots the difference between SW and HW run times against log2(cache sizes).

    Args:
        experiment_data (dict): Parsed experiment data.
    """
    cache_sizes_log2 = []
    time_differences = []
    cache_sizes_bytes = []

    for cache_size in sorted(experiment_data.keys()):
        data = experiment_data[cache_size]
        if 'sw' in data and 'hw' in data:
            sw_time = data['sw']
            hw_time = data['hw']
            difference = sw_time - hw_time  # SW - HW
            log2_cache_size = math.log2(cache_size)
            cache_sizes_log2.append(log2_cache_size)
            time_differences.append(difference)
            cache_sizes_bytes.append(cache_size)
            print(f"Cache Size: {cache_size} bytes ({cache_size / (1024 * 1024)} MB) - SW Time: {sw_time}s, HW Time: {hw_time}s, Difference: {difference}s")
        else:
            print(f"Missing SW or HW data for cache size {cache_size} bytes. Skipping.")

    if not cache_sizes_log2:
        print("No complete data to plot.")
        return

    # Create the plot
    plt.figure(figsize=(10, 6))
    plt.plot(cache_sizes_log2, time_differences, marker='o', linestyle='-', color='b')
    plt.title('Absolute Speedup From IAA vs Cache Size')
    plt.ylabel('Absolute Speedup (s)')
    plt.xlabel('Cache Size (MB)')
    plt.grid(True)
    plt.axhline(0, color='red', linestyle='--')  # Reference line at y=0

    # Optional: Customize x-axis ticks to show actual cache sizes
    # Define cache sizes in bytes and their corresponding log2 values
    unique_cache_sizes = sorted(cache_sizes_bytes)
    log2_unique_cache_sizes = [math.log2(cs) for cs in unique_cache_sizes]
    cache_size_labels = [f"{cs // (1024 * 1024)}MB" if cs >= (1024 * 1024) else f"{cs}B" for cs in unique_cache_sizes]
    plt.xticks(log2_unique_cache_sizes, cache_size_labels, rotation=45)

    plt.tight_layout()

    # Save the plot
    plot_filename = 'absolute_iaa_speedup.png'
    plt.savefig(plot_filename)
    print(f"Plot saved as {plot_filename}")

    # Show the plot
    plt.show()

# ---------------------------- Main Execution ---------------------------- #

def main():
    # Check if the output directory exists
    if not os.path.isdir(OUTPUT_DIR):
        print(f"Output directory '{OUTPUT_DIR}' does not exist.")
        return

    # Parse the experiment files
    print("Parsing experiment output files...")
    experiment_data = parse_experiment_files(OUTPUT_DIR)

    # Check if any data was parsed
    if not experiment_data:
        print("No valid experiment data found.")
        return

    # Plot the time differences
    # print("\nPlotting time differences...")
    # plot_time_differences(experiment_data)
    print("\nPlotting time differences with log2(Cache Size)...")
    plot_time_differences_log2(experiment_data)

    print("Done.")

if __name__ == "__main__":
    main()
