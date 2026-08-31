"""
Solvosys Desktop HPC Agent Adapter
==================================
Allows desktop environment integration for Supercomputer execution.
Delegates to backend.hpc subsystem.
"""

import sys
import os

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from hpc.agent import get_hpc_agent, LocalHPCAgent

def main():
    agent = get_hpc_agent()
    print("Solvosys Local HPC Agent")
    print(f"Status: {agent.get_status()}")

if __name__ == "__main__":
    main()
