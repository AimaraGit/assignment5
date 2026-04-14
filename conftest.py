# conftest.py
# pytest reads this file automatically.
# It adds the project folder to Python's path so imports work correctly.

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))