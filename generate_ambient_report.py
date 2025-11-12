#!/usr/bin/env python3
"""Generate Service Mesh (Ambient Mode) Performance Report"""

import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd
from pathlib import Path

RESULTS_DIR = Path("./ambient_test_results")
METRICS_DIR = RESULTS_DIR / "metrics"
OUTPUT_PDF = "service_mesh_latency_trials.pdf"

SDP_DATA = {
    5: {'p50': 5.03, 'p90': 5.63, 'p99': 6.39, 'avg': 4.98},
    10: {'p50': 4.85, 'p90': 5.50, 'p99': 6.14, 'avg': 4.82},
    25: {'p50': 5.47, 'p90': 45.16, 'p99': 46.09, 'avg': 23.51},
    50: {'p50': 44.07, 'p90': 45.08, 'p99': 45.99, 'avg': 29.40},
    75: {'p50': 44.01, 'p90': 45.01, 'p99': 45.81, 'avg': 31.51}
}

def load_test_summary(rps):
    file = RESULTS_DIR / f"ambient_{rps}_rps_summary.json"
    try:
        with open(file, 'r') as f:
            return json.load(f)
    except:
        return None

def load_latency_csv(rps):
    file = RESULTS_DIR / f"ambient_{rps}_rps_latency.csv"
    try:
        df = pd.read_csv(file)
        return df[df['ok'] == 1]['latency_ms'].values
    except:
        return None

def load_metrics_csv(rps):
    file = METRICS_DIR / f"ambient_{rps}_rps_metrics.csv"
    try:
        return pd.read_csv(file)
    except:
        return None

def parse_value(val):
    if pd.isna(val):
        return None
    val = str(val)
    if 'm' in val:
        return float(val.replace('m', ''))
    elif 'Mi' in val:
        return float(val.replace('Mi', ''))
    return None

def analyze_metrics(rps):
    df = load_metrics_csv(rps)
    if df is None or df.empty:
        return None
    cpu = df['cpu'].apply(parse_value).dropna()
    mem = df['memory'].apply(parse_value).dropna()
    return {
        'avg_cpu': cpu.mean() if len(cpu) > 0 else 0,
        'max_cpu': cpu.max() if len(cpu) > 0 else 0,
        'min_cpu': cpu.min() if len(cpu) > 0 else 0,
        'avg_mem': mem.mean() if len(mem) > 0 else 0,
        'max_mem': mem.max() if len(mem) > 0 else 0,
        'min_mem': mem.min() if len(mem) > 0 else 0
    }

print("Generating Service Mesh Performance Report...")
print(f"Output: {OUTPUT_PDF}\n")

rps_levels = [5, 10, 25, 50, 75]

with PdfPages(OUTPUT_PDF) as pdf:
    # Page 1: Summary Tables
    fig = plt.figure(figsize=(11, 8.5))
    fig.suptitle('Service Mesh (Ambient Mode) - Latency Trials', 
                 fontsize=18, fontweight='bold', y=0.96)
    
    # Latency Table
    ax1 = fig.add_subplot(211)
    ax1.axis('tight')
    ax1.axis('off')
    
    latency_data = []
    for rps in rps_levels:
        summary = load_test_summary(rps)
        if summary:
            latency_data.append([
                rps,
                f"{summary['p50_ms']:.2f}",
                f"{summary['p90_ms']:.2f}",
                f"{summary['p99_ms']:.2f}",
                f"{summary['avg_ms']:.2f}",
                f"{summary['count']}"
            ])
            print(f"✓ {rps} RPS: avg={summary['avg_ms']:.2f}ms, p99={summary['p99_ms']:.2f}ms")
    
    table1 = ax1.table(cellText=latency_data,
                      colLabels=['RPS', 'p50 (ms)', 'p90 (ms)', 'p99 (ms)', 'avg (ms)', 'Total Requests'],
                      cellLoc='center',
                      loc='center')
    table1.auto_set_font_size(False)
    table1.set_fontsize(11)
    table1.scale(1, 2.5)
    
    for i in range(len(latency_data) + 1):
        for j in range(6):
            cell = table1[(i, j)]
            if i == 0:
                cell.set_facecolor('#4CAF50')
                cell.set_text_props(weight='bold', color='white')
    
    ax1.set_title('Latency Performance Summary', fontsize=14, fontweight='bold', pad=20)
    
    # CPU/Memory Table
    ax2 = fig.add_subplot(212)
    ax2.axis('tight')
    ax2.axis('off')
    
    resource_data = []
    for rps in rps_levels:
        metrics = analyze_metrics(rps)
        if metrics:
            resource_data.append([
                rps,
                f"{metrics['avg_cpu']:.1f}",
                f"{metrics['max_cpu']:.0f}",
                f"{metrics['min_cpu']:.0f}",
                f"{metrics['avg_mem']:.1f}",
                f"{metrics['max_mem']:.0f}",
                f"{metrics['min_mem']:.0f}"
            ])
    
    table2 = ax2.table(cellText=resource_data,
                      colLabels=['RPS', 'Avg CPU (m)', 'Max CPU (m)', 'Min CPU (m)', 
                               'Avg Mem (MiB)', 'Max Mem (MiB)', 'Min Mem (MiB)'],
                      cellLoc='center',
                      loc='center')
    table2.auto_set_font_size(False)
    table2.set_fontsize(11)
    table2.scale(1, 2.5)
    
    for i in range(len(resource_data) + 1):
        for j in range(7):
            cell = table2[(i, j)]
            if i == 0:
                cell.set_facecolor('#2196F3')
                cell.set_text_props(weight='bold', color='white')
    
    ax2.set_title('Resource Pod (service2) - CPU & Memory Usage', 
                 fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()
    
    # Histogram and CDF pages
    for rps in rps_levels:
        latencies = load_latency_csv(rps)
        
        if latencies is not None and len(latencies) > 0:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5))
            fig.suptitle(f'At {rps} RPS', fontsize=16, fontweight='bold')
            
            # Histogram
            ax1.hist(latencies, bins=50, color='steelblue', edgecolor='black', alpha=0.7)
            ax1.set_xlabel('Latency (ms)', fontsize=11)
            ax1.set_ylabel('Frequency', fontsize=11)
            ax1.set_title(f'Histogram of Latency - {rps} RPS', fontsize=13, fontweight='bold')
            ax1.grid(True, alpha=0.3)
            
            # CDF
            sorted_lat = np.sort(latencies)
            cdf = np.arange(1, len(sorted_lat) + 1) / len(sorted_lat)
            ax2.plot(sorted_lat, cdf, linewidth=2, color='darkgreen')
            ax2.set_xlabel('Latency (ms)', fontsize=11)
            ax2.set_ylabel('CDF', fontsize=11)
            ax2.set_title(f'CDF of Latency - {rps} RPS', fontsize=13, fontweight='bold')
            ax2.grid(True, alpha=0.3)
            ax2.set_ylim([0, 1])
            
            plt.tight_layout()
            pdf.savefig(fig, bbox_inches='tight')
            plt.close()
    
    # Comparison page
    fig, ax = plt.subplots(figsize=(11, 8.5))
    fig.suptitle('Service Mesh vs SDP - Performance Comparison', 
                 fontsize=18, fontweight='bold')
    
    comparison_data = []
    for rps in rps_levels:
        summary = load_test_summary(rps)
        if summary and rps in SDP_DATA:
            mesh_avg = summary['avg_ms']
            mesh_p99 = summary['p99_ms']
            sdp = SDP_DATA[rps]
            
            improvement_avg = ((sdp['avg'] - mesh_avg) / sdp['avg'] * 100)
            improvement_p99 = ((sdp['p99'] - mesh_p99) / sdp['p99'] * 100)
            
            comparison_data.append([
                rps,
                f"{sdp['avg']:.2f}",
                f"{mesh_avg:.2f}",
                f"{improvement_avg:+.1f}%",
                f"{sdp['p99']:.2f}",
                f"{mesh_p99:.2f}",
                f"{improvement_p99:+.1f}%"
            ])
    
    ax.axis('tight')
    ax.axis('off')
    table = ax.table(cellText=comparison_data,
                    colLabels=['RPS', 'SDP Avg (ms)', 'Mesh Avg (ms)', 'Δ %', 
                             'SDP P99 (ms)', 'Mesh P99 (ms)', 'Δ %'],
                    cellLoc='center',
                    loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 3)
    
    for i in range(len(comparison_data) + 1):
        for j in range(7):
            cell = table[(i, j)]
            if i == 0:
                cell.set_facecolor('#FF9800')
                cell.set_text_props(weight='bold', color='white')
    
    plt.tight_layout()
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()

print(f"\n✅ Report generated successfully: {OUTPUT_PDF}")
