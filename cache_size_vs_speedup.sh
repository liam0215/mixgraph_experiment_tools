#!/bin/bash

# ------------------------------------------------------------------
# Bash Script to Run mixgraph Benchmark with SW and HW Compression
# for Varying Cache Sizes
# ------------------------------------------------------------------

# Exit immediately if a command exits with a non-zero status
set -e

# ---------------------------- Configuration ---------------------------- #

# Path to the db_bench executable
DB_BENCH_PATH="./db_bench"  # Update this path if db_bench is located elsewhere

# Database directory
DB_PATH="./db"

# Directory to store experiment outputs
OUTPUT_DIR="../experiment_results"
mkdir -p "$OUTPUT_DIR"

# List of cache sizes for the mixgraph benchmark (in bytes)
# Example sizes: 256MB, 512MB, 1GB, 2GB
CACHE_SIZES=(1048576 2097152 4194304 8388608 16777216 33554432 67108864 134217728 268435456 536870912)

# Compression types and their corresponding compressor_options
declare -A COMPRESSOR_OPTIONS
COMPRESSOR_OPTIONS["sw"]="execution_path=sw"
COMPRESSOR_OPTIONS["hw"]="execution_path=hw"

# Fixed cache size for fillrandom benchmark (e.g., 256MB)
FILLRANDOM_CACHE_SIZE=268435456

# Benchmark parameters (adjust as needed)
NUM_KEYS=5000000
KEY_SIZE=48
READS=42000000
MIX_GET_RATIO=0.85
MIX_PUT_RATIO=0.14
MIX_SEEK_RATIO=0.01
SINE_MIX_RATE_INTERVAL_MS=5000
SINE_A=1000
SINE_B=0.00000073
SINE_D=90000
KEYRANGE_DIST_A=14.18
KEYRANGE_DIST_B=-2.917
KEYRANGE_DIST_C=0.0164
KEYRANGE_DIST_D=-0.08082
KEYRANGE_NUM=30
VALUE_K=0.2615
VALUE_SIGMA=25.45
ITER_K=2.517
ITER_SIGMA=14.236

# taskset mask
TASKSET_MASK="0xAAAAAAAAAAAAAAAA"

# Sudo prefix
SUDO_PREFIX="sudo"

# Number of iterations (set to 1 for single run)
NUM_ITERATIONS=1

# -------------------------------------------------------------------

# Function to run a command and handle errors
run_command() {
    local CMD="$*"
    echo "Executing: $CMD"
    eval "$CMD"
}

# Function to populate the database using fillrandom
populate_database() {
    local compression_option="$1"
    local compression_type="$2"

    echo "Populating the database with fillrandom using $compression_type compression..."
    
    # Remove existing database if it exists
    if [ -d "$DB_PATH" ]; then
        echo "Removing existing database at $DB_PATH..."
        run_command "sudo rm -rf $DB_PATH"
    fi

    # Run fillrandom benchmark
    run_command "taskset $TASKSET_MASK $SUDO_PREFIX $DB_BENCH_PATH \
        --compression_type=com.intel.iaa_compressor_rocksdb \
        --compressor_options=\"$compression_option\" \
        --benchmarks=\"fillrandom\" \
        -num=$NUM_KEYS \
        -key_size=$KEY_SIZE \
        -cache_size=$FILLRANDOM_CACHE_SIZE \
        --db=$DB_PATH"

    echo "Database populated successfully."
}

# Function to run the mixgraph benchmark
run_mixgraph() {
    local compression_option="$1"
    local compression_type="$2"
    local cache_size="$3"

    echo "Running mixgraph with $compression_type compression and cache size $cache_size bytes..."

    # Define output file name
    local OUTPUT_FILE="$OUTPUT_DIR/exp_${cache_size}_${compression_type}.txt"

    # Run mixgraph benchmark
    run_command "taskset $TASKSET_MASK $SUDO_PREFIX $DB_BENCH_PATH \
        --compression_type=com.intel.iaa_compressor_rocksdb \
        --compressor_options=\"$compression_option\" \
        --benchmarks=\"mixgraph\" \
        --db=$DB_PATH \
        --use_existing_db=true \
        -keyrange_dist_a=$KEYRANGE_DIST_A \
        -keyrange_dist_b=$KEYRANGE_DIST_B \
        -keyrange_dist_c=$KEYRANGE_DIST_C \
        -keyrange_dist_d=$KEYRANGE_DIST_D \
        -keyrange_num=$KEYRANGE_NUM \
        -value_k=$VALUE_K \
        -value_sigma=$VALUE_SIGMA \
        -iter_k=$ITER_K \
        -iter_sigma=$ITER_SIGMA \
        -mix_get_ratio=$MIX_GET_RATIO \
        -mix_put_ratio=$MIX_PUT_RATIO \
        -mix_seek_ratio=$MIX_SEEK_RATIO \
        -sine_mix_rate_interval_milliseconds=$SINE_MIX_RATE_INTERVAL_MS \
        -sine_a=$SINE_A \
        -sine_b=$SINE_B \
        -sine_d=$SINE_D \
        -reads=$READS \
        -num=$NUM_KEYS \
        -key_size=$KEY_SIZE \
        -cache_size=$cache_size > $OUTPUT_FILE"

    echo "mixgraph completed. Output saved to $OUTPUT_FILE."
}

# ---------------------------- Main Execution ---------------------------- #

echo "Starting experiments..."

# Iterate over each cache size
for CACHE_SIZE in "${CACHE_SIZES[@]}"; do
    echo "---------------------------------------------"
    echo "Starting experiments for cache size: $CACHE_SIZE bytes"
    echo "---------------------------------------------"

    # Iterate over each compression type
    for COMPRESSION_TYPE in "${!COMPRESSOR_OPTIONS[@]}"; do
        COMPRESSION_OPTION=${COMPRESSOR_OPTIONS[$COMPRESSION_TYPE]}
        
        echo "---------------------------------------------"
        echo "Compression Type: $COMPRESSION_TYPE"
        echo "---------------------------------------------"

        # Populate the database
        populate_database "$COMPRESSION_OPTION" "$COMPRESSION_TYPE"

        # Run mixgraph benchmark
        for ((i=1; i<=NUM_ITERATIONS; i++)); do
            echo "Iteration $i for cache size $CACHE_SIZE and compression $COMPRESSION_TYPE"
            run_mixgraph "$COMPRESSION_OPTION" "$COMPRESSION_TYPE" "$CACHE_SIZE"
        done

        echo "Completed experiments for cache size: $CACHE_SIZE bytes with $COMPRESSION_TYPE compression."
        echo ""
    done

    echo "Completed all compression types for cache size: $CACHE_SIZE bytes."
    echo ""
done

echo "All experiments completed successfully."
echo "Results are stored in the directory: $OUTPUT_DIR"
