#!/bin/bash

NAMESPACE="mesh-demo"
SERVICE1_PORT=8000
OUTPUT_DIR="./ambient_test_results"
METRICS_DIR="${OUTPUT_DIR}/metrics"

mkdir -p "$OUTPUT_DIR"
mkdir -p "$METRICS_DIR"

KUBECTL="minikube kubectl --"

SERVICE1_POD=$($KUBECTL -n "$NAMESPACE" get pod -l app=service1 -o jsonpath="{.items[0].metadata.name}")
SERVICE2_POD=$($KUBECTL -n "$NAMESPACE" get pod -l app=service2 -o jsonpath="{.items[0].metadata.name}")

echo "============================================"
echo "Service Mesh Performance Tests with Metrics"
echo "============================================"
echo "Service1 Pod: $SERVICE1_POD"
echo "Service2 Pod: $SERVICE2_POD"
echo ""

# Function to monitor resources
monitor_resources() {
    local duration=$1
    local rps=$2
    local metrics_file="${METRICS_DIR}/ambient_${rps}_rps_metrics.csv"
    
    echo "timestamp,cpu,memory" > "$metrics_file"
    
    local end_time=$((SECONDS + duration))
    while [ $SECONDS -lt $end_time ]; do
        timestamp=$(date +%s)
        stats=$($KUBECTL top pod "$SERVICE2_POD" -n "$NAMESPACE" --no-headers 2>/dev/null | awk '{print $2","$3}')
        if [ ! -z "$stats" ]; then
            echo "${timestamp},${stats}" >> "$metrics_file"
        fi
        sleep 2
    done
}

# Test configurations
declare -a tests=(
    "5:60"
    "10:90"
    "25:120"
    "50:180"
    "75:240"
)

for test in "${tests[@]}"; do
    IFS=':' read -r rps duration <<< "$test"
    
    echo "============================================"
    echo "Test: ${rps} RPS for ${duration} seconds"
    echo "============================================"
    
    # Start monitoring in background
    monitor_resources "$duration" "$rps" &
    MONITOR_PID=$!
    
    # Get initial metrics
    echo "Initial metrics:"
    $KUBECTL top pod "$SERVICE2_POD" -n "$NAMESPACE"
    
    # Run test
    echo "Running load test..."
    curl -s "http://127.0.0.1:${SERVICE1_PORT}/measure_rps?rps=${rps}&duration=${duration}&concurrency=8&timeout=2.0" \
        > "${OUTPUT_DIR}/ambient_${rps}_rps_summary.json"
    
    # Wait for monitoring to finish
    wait $MONITOR_PID
    
    # Get final metrics
    echo "Final metrics:"
    $KUBECTL top pod "$SERVICE2_POD" -n "$NAMESPACE"
    
    # Copy latency CSV
    echo "Copying latency data..."
    $KUBECTL -n "$NAMESPACE" cp "${SERVICE1_POD}:/app/latency_results.csv" \
        "${OUTPUT_DIR}/ambient_${rps}_rps_latency.csv"
    
    # Show summary
    cat "${OUTPUT_DIR}/ambient_${rps}_rps_summary.json"
    echo ""
    echo "✅ Test ${rps} RPS completed"
    echo ""
    
    # Wait between tests
    if [ "$rps" != "75" ]; then
        echo "Waiting 10 seconds before next test..."
        sleep 10
    fi
done

echo "============================================"
echo "All tests completed!"
echo "============================================"
echo "Results in: $OUTPUT_DIR"
