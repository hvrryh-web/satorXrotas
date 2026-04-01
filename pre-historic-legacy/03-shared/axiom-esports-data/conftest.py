# conftest.py — root pytest configuration for axiom-esports-data
# importlib mode resolves the tests/ namespace collision between
# analytics/tests and api/tests packages.
import sys
import os

# Ensure the project root is on sys.path for all test modules
sys.path.insert(0, os.path.dirname(__file__))
