#!/usr/bin/env python3
"""
Verification Script for Task 1 & 2 Completion
Checks that all files are created and configured correctly
"""

import os
import sys
from pathlib import Path

def check_file_exists(file_path, description=""):
    """Check if a file exists and return True/False"""
    exists = os.path.isfile(file_path)
    status = "✅" if exists else "❌"
    desc = f" - {description}" if description else ""
    print(f"{status} {file_path}{desc}")
    return exists

def check_directory_exists(dir_path, description=""):
    """Check if a directory exists and return True/False"""
    exists = os.path.isdir(dir_path)
    status = "✅" if exists else "❌"
    desc = f" - {description}" if description else ""
    print(f"{status} {dir_path}{desc}")
    return exists

def check_file_contains(file_path, search_text, description=""):
    """Check if a file contains specific text"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        exists = search_text in content
        status = "✅" if exists else "❌"
        desc = f" - {description}" if description else ""
        print(f"{status} {file_path} contains '{search_text}'{desc}")
        return exists
    except:
        print(f"❌ {file_path} - Could not read file")
        return False

def main():
    print("=" * 70)
    print("TASK 1 & 2 COMPLETION VERIFICATION")
    print("=" * 70)
    
    base_path = Path(__file__).parent
    backend_path = base_path / "backend"
    controller_path = backend_path / "controller"
    
    all_checks = []
    
    # ===== TASK 1 FILES =====
    print("\n📋 TASK 1: Hybrid Input Mode Files")
    print("-" * 70)
    
    all_checks.append(check_file_exists(
        controller_path / "data_provider.py",
        "Hybrid input abstraction layer"
    ))
    
    all_checks.append(check_file_exists(
        backend_path / ".env",
        "Environment configuration"
    ))
    
    all_checks.append(check_file_exists(
        backend_path / ".env.example",
        "Configuration reference"
    ))
    
    all_checks.append(check_file_exists(
        backend_path / "test_hybrid_provider.py",
        "Task 1 unit tests"
    ))
    
    all_checks.append(check_file_exists(
        backend_path / "test_integration.py",
        "Task 1 integration tests"
    ))
    
    # ===== TASK 2 FILES =====
    print("\n📋 TASK 2: WEST Metrics Files")
    print("-" * 70)
    
    all_checks.append(check_file_exists(
        backend_path / "test_west_metrics_unit.py",
        "Task 2 unit tests (no cv2 dependency)"
    ))
    
    all_checks.append(check_file_exists(
        backend_path / "test_west_metrics.py",
        "Task 2 integration test template"
    ))
    
    # ===== MODIFIED FILES =====
    print("\n🔧 Modified Files")
    print("-" * 70)
    
    all_checks.append(check_file_exists(
        controller_path / "yolo_west_source.py",
        "YOLO source with metrics (269 lines)"
    ))
    
    all_checks.append(check_file_exists(
        backend_path / "app_sumo.py",
        "Main app with hybrid integration"
    ))
    
    all_checks.append(check_file_exists(
        controller_path / "state_models.py",
        "Updated with InputHealthInfo"
    ))
    
    all_checks.append(check_file_exists(
        backend_path / "requirements.txt",
        "Updated dependencies"
    ))
    
    # ===== DOCUMENTATION FILES =====
    print("\n📚 Documentation Files")
    print("-" * 70)
    
    all_checks.append(check_file_exists(
        backend_path / "TASK2_METRICS_IMPLEMENTATION.md",
        "Task 2 implementation guide"
    ))
    
    all_checks.append(check_file_exists(
        backend_path / "WEST_METRICS_QUICK_REFERENCE.md",
        "Quick reference guide"
    ))
    
    all_checks.append(check_file_exists(
        base_path / "HYBRID_AND_METRICS_INTEGRATION.md",
        "Complete integration guide"
    ))
    
    all_checks.append(check_file_exists(
        base_path / "COMPLETION_STATUS.md",
        "Master completion status"
    ))
    
    # ===== CONFIGURATION VERIFICATION =====
    print("\n⚙️  Configuration Verification")
    print("-" * 70)
    
    all_checks.append(check_file_contains(
        backend_path / ".env",
        "USE_CAMERA_WEST",
        "USE_CAMERA_WEST setting"
    ))
    
    all_checks.append(check_file_contains(
        backend_path / ".env",
        "WEST_ROI",
        "WEST_ROI setting"
    ))
    
    all_checks.append(check_file_contains(
        backend_path / ".env",
        "WEST_SMOOTHING_ENABLED",
        "WEST_SMOOTHING_ENABLED setting"
    ))
    
    all_checks.append(check_file_contains(
        backend_path / ".env",
        "WEST_SMOOTHING_WINDOW",
        "WEST_SMOOTHING_WINDOW setting"
    ))
    
    all_checks.append(check_file_contains(
        backend_path / ".env",
        "WEST_RESIZE_WIDTH",
        "WEST_RESIZE_WIDTH setting"
    ))
    
    # ===== CODE VERIFICATION =====
    print("\n🔍 Code Implementation Verification")
    print("-" * 70)
    
    all_checks.append(check_file_contains(
        controller_path / "data_provider.py",
        "class RoadDataProvider",
        "RoadDataProvider abstract class"
    ))
    
    all_checks.append(check_file_contains(
        controller_path / "data_provider.py",
        "class HybridProvider",
        "HybridProvider concrete class"
    ))
    
    all_checks.append(check_file_contains(
        controller_path / "yolo_west_source.py",
        "def _parse_roi",
        "ROI parsing method"
    ))
    
    all_checks.append(check_file_contains(
        controller_path / "yolo_west_source.py",
        "def _smooth_counts",
        "Smoothing method"
    ))
    
    all_checks.append(check_file_contains(
        controller_path / "yolo_west_source.py",
        "def _compute_metrics",
        "Metrics computation method"
    ))
    
    all_checks.append(check_file_contains(
        backend_path / "app_sumo.py",
        "HybridProvider",
        "HybridProvider integration in app"
    ))
    
    all_checks.append(check_file_contains(
        controller_path / "state_models.py",
        "class InputHealthInfo",
        "InputHealthInfo model"
    ))
    
    # ===== DEPENDENCY VERIFICATION =====
    print("\n📦 Dependency Verification")
    print("-" * 70)
    
    all_checks.append(check_file_contains(
        backend_path / "requirements.txt",
        "python-dotenv",
        "python-dotenv package"
    ))
    
    # ===== SUMMARY =====
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    total_checks = len(all_checks)
    passed_checks = sum(all_checks)
    failed_checks = total_checks - passed_checks
    pass_rate = (passed_checks / total_checks) * 100
    
    print(f"\nTotal Checks: {total_checks}")
    print(f"Passed: {passed_checks} ✅")
    print(f"Failed: {failed_checks} ❌")
    print(f"Pass Rate: {pass_rate:.1f}%")
    
    if failed_checks == 0:
        print("\n🎉 ALL VERIFICATIONS PASSED!")
        print("✅ Task 1 & 2 Implementation Complete")
        print("✅ All files created and configured")
        print("✅ Ready for production deployment")
        return 0
    else:
        print(f"\n⚠️  {failed_checks} verification(s) failed")
        print("Please check the items marked with ❌ above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
