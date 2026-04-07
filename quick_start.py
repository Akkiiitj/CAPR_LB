#!/usr/bin/env python3
"""
Quick-start script for Proactive Load Balancing system.

This script provides an interactive menu to:
- Run the complete 5-step build
- Train individual components
- Test predictions
- View forecasts
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Color formatting
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(title):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}")
    print(f"{title.center(80)}")
    print(f"{'='*80}{Colors.ENDC}\n")


def print_success(msg):
    print(f"{Colors.OKGREEN}✓ {msg}{Colors.ENDC}")


def print_info(msg):
    print(f"{Colors.OKCYAN}ℹ {msg}{Colors.ENDC}")


def print_warning(msg):
    print(f"{Colors.WARNING}⚠ {msg}{Colors.ENDC}")


def print_error(msg):
    print(f"{Colors.FAIL}✗ {msg}{Colors.ENDC}")


def check_dependencies():
    """Check if required packages are installed."""
    required = ['simpy', 'pandas', 'numpy', 'sklearn', 'scipy']
    missing = []
    
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    if missing:
        print_error(f"Missing packages: {', '.join(missing)}")
        print_info("Install with: pip install " + " ".join(missing))
        return False
    
    print_success("All dependencies installed")
    return True


def menu_main():
    """Main menu."""
    print_header("PROACTIVE LOAD BALANCING SYSTEM")
    
    print("Choose an option:\n")
    print("1. Run complete 5-step system build (recommended)")
    print("2. Run individual step")
    print("3. Quick test (5 min simulation only)")
    print("4. View documentation")
    print("5. Check system status")
    print("0. Exit\n")
    
    choice = input("Enter choice (0-5): ").strip()
    return choice


def menu_individual_step():
    """Menu for individual step execution."""
    print_header("Select Individual Step")
    
    print("Which step to run?\n")
    print("1. Step 1: Generate Simulation Data (30 days)")
    print("2. Step 2: Train Linear Prediction Model")
    print("3. Step 3: Test Queue Rearrangement Policy")
    print("4. Step 4: Train Q-Learning Agent")
    print("5. Step 5: Test Proactive Orchestrator")
    print("0. Back to main menu\n")
    
    choice = input("Enter choice (0-5): ").strip()
    return choice


def run_complete_build():
    """Run complete 5-step build."""
    print_header("Running Complete 5-Step System Build")
    
    print_info("This will take 5-15 minutes depending on your hardware\n")
    
    try:
        from experiments.run_full_system_build import main
        main()
        print_success("\nComplete system build finished!")
        print_info("Check 'data/', 'models/', and 'results/' directories for outputs")
        
    except ImportError as e:
        print_error(f"Import error: {e}")
        print_info("Make sure you're in the correct directory")
    except Exception as e:
        print_error(f"Error: {e}")


def run_step_simulation_quick():
    """Run quick 5-day simulation."""
    print_header("Running Quick 5-Day Simulation")
    
    try:
        from experiments.advanced_simulation import RealisticDemandSimulation
        import os
        
        os.makedirs("data", exist_ok=True)
        
        print_info("Running 5-day simulation...")
        sim = RealisticDemandSimulation(
            days_to_simulate=5,  # Quick version
            base_arrival_rate=5.0,
            spike_multiplier=3.5,
            spike_probability_per_hour=0.15
        )
        
        results = sim.run_simulation(num_servers=10)
        sim.export_metrics_to_csv("data/quick_simulation_metrics.csv")
        
        summary = sim.get_summary()
        print_success(f"\nQuick simulation complete!")
        print(f"  Days: {summary['simulation_days']}")
        print(f"  Metrics: {summary['total_metrics_collected']}")
        print(f"  Max queue: {summary['max_queue_depth']}")
        print(f"  Spike events: {summary['spike_events']}")
        
        print_info("Data saved to: data/quick_simulation_metrics.csv")
        
    except Exception as e:
        print_error(f"Simulation failed: {e}")


def run_individual_step(step_num):
    """Run a specific step."""
    steps_info = {
        '1': ("Simulation Data Generation", run_step_simulation_quick),
        '2': ("Linear Model Training", "requires_data"),
        '3': ("Queue Rearrangement Testing", "requires_data"),
        '4': ("Q-Learning Training", "requires_data"),
        '5': ("Proactive Orchestrator Testing", "requires_complex")
    }
    
    if step_num not in steps_info:
        print_error("Invalid step")
        return
    
    step_name, handler = steps_info[step_num]
    print_header(f"Running {step_name}")
    
    if callable(handler):
        handler()
    else:
        print_info(f"This step {handler}")
        print_info("Run 'Run complete 5-step system build' instead")


def show_documentation():
    """Display documentation."""
    print_header("Proactive Load Balancing System Documentation")
    
    doc_file = "PROACTIVE_LB_GUIDE.md"
    
    if os.path.exists(doc_file):
        with open(doc_file, 'r') as f:
            content = f.read()
        
        # Show first 2000 chars
        print(content[:2000])
        print(f"\n... (see {doc_file} for full documentation)")
    else:
        print_error(f"Documentation file not found: {doc_file}")


def check_system_status():
    """Check system status and output files."""
    print_header("System Status Check")
    
    files_to_check = [
        ("data/simulation_metrics.csv", "Simulation metrics"),
        ("models/linear_server_predictor.pkl", "Linear model"),
        ("models/q_learning_agent.pkl", "Q-Learning model"),
        ("models/linear_model_deploy_info.json", "Model deploy info"),
        ("results/system_report.json", "System report")
    ]
    
    print("Output Files Status:\n")
    for file_path, description in files_to_check:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print_success(f"{description:30} - {file_path:40} ({size:,} bytes)")
        else:
            print_warning(f"{description:30} - NOT FOUND")
    
    # Check dependencies
    print("\nDependencies:\n")
    if check_dependencies():
        print_success("All dependencies satisfied")
    
    print("\nSystem Ready:\n")
    if os.path.exists("data/simulation_metrics.csv"):
        print_success("✓ Data generated")
    else:
        print_warning("⚠ Run Step 1 first to generate data")
    
    if os.path.exists("models/linear_server_predictor.pkl"):
        print_success("✓ Linear model trained")
    else:
        print_warning("⚠ Run Step 2 to train model")


def main():
    """Main entry point."""
    os.chdir(Path(__file__).parent)
    
    while True:
        if not check_dependencies():
            input("\nPress Enter to exit...")
            sys.exit(1)
        
        choice = menu_main()
        
        if choice == '0':
            print_info("Goodbye!")
            break
        
        elif choice == '1':
            run_complete_build()
            input("\nPress Enter to continue...")
        
        elif choice == '2':
            step = menu_individual_step()
            if step != '0':
                run_individual_step(step)
            input("\nPress Enter to continue...")
        
        elif choice == '3':
            run_step_simulation_quick()
            input("\nPress Enter to continue...")
        
        elif choice == '4':
            show_documentation()
            input("\nPress Enter to continue...")
        
        elif choice == '5':
            check_system_status()
            input("\nPress Enter to continue...")
        
        else:
            print_error("Invalid choice")


if __name__ == "__main__":
    main()
