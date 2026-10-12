#!/usr/bin/env python3
"""Legacy alias; project bootstrap requires destination owner."""
try:
    from scripts.project_setup import main
except ModuleNotFoundError:
    from project_setup import main
if __name__=="__main__":main()
