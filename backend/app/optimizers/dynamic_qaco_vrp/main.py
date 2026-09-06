# main.py
from __future__ import annotations
from config import CFG, FLAGS
from qaco.solver.runner import DynamicQACO

def run_experiment():
    print("Initializing Dynamic QACO-VRP Execution...")
    
    # Active feature flags for the experiment
    active_flags = {
        **FLAGS,
        'interference_on': True,
        'tunneling_on': True,
        'local_search_on': True,
        'adaptive_on': True,
        'dynamic_on': True,
        'partial_reconstruct_on': True,
    }

    engine = DynamicQACO(CFG, active_flags)
    records, interference_log = engine.run()
    
    print(f"Execution completed over {len(records)} iterations.")
    print(f"Final Objective Score: {records[-1]['objective']:.4f}")
    print(f"Final Congestion Score: {records[-1]['congestion']:.4f}")

if __name__ == "__main__":
    run_experiment()