#!/usr/bin/env python3
"""
Automation Script for Mesher.py
Executes all meshing commands from Dev - 1.md to generate meshes
for all combinations of methods and formats.
"""

import subprocess
import os
import sys
from pathlib import Path
import time

# Define all meshing configurations
MESHING_CONFIGS = [
    # OBJ format
    {"input": "../pclouds/chiller.ply", "output": "chiller_poisson.obj", "format": "obj", "method": "poisson"},
    {"input": "../pclouds/chiller.ply", "output": "chiller_bpa.obj", "format": "obj", "method": "bpa"},
    {"input": "../pclouds/chiller.ply", "output": "chiller_alpha.obj", "format": "obj", "method": "alpha"},
    
    # GLB format
    {"input": "../pclouds/chiller.ply", "output": "chiller_poisson.glb", "format": "glb", "method": "poisson"},
    {"input": "../pclouds/chiller.ply", "output": "chiller_bpa.glb", "format": "glb", "method": "bpa"},
    {"input": "../pclouds/chiller.ply", "output": "chiller_alpha.glb", "format": "glb", "method": "alpha"},
    
    # STL format
    {"input": "../pclouds/chiller.ply", "output": "chiller_poisson.stl", "format": "stl", "method": "poisson"},
    {"input": "../pclouds/chiller.ply", "output": "chiller_bpa.stl", "format": "stl", "method": "bpa"},
    {"input": "../pclouds/chiller.ply", "output": "chiller_alpha.stl", "format": "stl", "method": "alpha"},
]


def run_mesher_command(config, index, total):
    """Execute a single mesher.py command."""
    print(f"\n{'='*70}")
    print(f"Processing {index}/{total}: {config['method'].upper()} → {config['format'].upper()}")
    print(f"{'='*70}")
    
    # Build command
    cmd = [
        "./mesher.py",
        "--input_file", config["input"],
        "--output_filename", config["output"],
        "--output_format", config["format"],
        "--meshing_method", config["method"]
    ]
    
    print(f"Command: {' '.join(cmd)}")
    
    # Execute command
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        elapsed_time = time.time() - start_time
        
        # Display output
        if result.stdout:
            print(result.stdout)
        
        if result.returncode == 0:
            print(f"✓ SUCCESS - Completed in {elapsed_time:.2f}s")
            return True
        else:
            print(f"✗ FAILED - Exit code: {result.returncode}")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ EXCEPTION: {e}")
        return False


def main():
    """Main function to execute all meshing commands."""
    print("="*70)
    print("AUTOMATED MESH GENERATION")
    print("="*70)
    print(f"Total configurations to process: {len(MESHING_CONFIGS)}")
    
    # Check if mesher.py exists
    if not os.path.exists("mesher.py"):
        print("\n✗ ERROR: mesher.py not found in current directory")
        print("Please run this script from the Open3D workspace directory")
        sys.exit(1)
    
    # Check if input file exists
    input_file = MESHING_CONFIGS[0]["input"]
    if not os.path.exists(input_file):
        print(f"\n✗ ERROR: Input file '{input_file}' not found")
        sys.exit(1)
    
    # Create output directory for meshes
    output_dir = Path("../meshes")
    output_dir.mkdir(exist_ok=True)
    print(f"\nOutput directory: {output_dir.absolute()}")
    
    # Execute all configurations
    results = []
    for i, config in enumerate(MESHING_CONFIGS, 1):
        # Update output path to use output directory
        original_output = config["output"]
        config["output"] = str(output_dir / original_output)
        
        success = run_mesher_command(config, i, len(MESHING_CONFIGS))
        results.append({
            "config": config,
            "success": success
        })
        
        # Restore original output name
        config["output"] = original_output
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful
    
    print(f"\nTotal: {len(results)}")
    print(f"✓ Successful: {successful}")
    print(f"✗ Failed: {failed}")
    
    if failed > 0:
        print("\nFailed configurations:")
        for r in results:
            if not r["success"]:
                c = r["config"]
                print(f"  - {c['method']} → {c['format']}")
    
    print("\n" + "="*70)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
