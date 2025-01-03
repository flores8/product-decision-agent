import os
import sys
from unittest.mock import patch

# Get the project root directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add the project root to the Python path
sys.path.insert(0, project_root)

# Mock weave.init globally for all tests
patch('weave.init').start()

# Create necessary test directories if they don't exist
test_dirs = [
    'tests/tools',
    'tests/models',
    'tests/objects',
    'tests/utils',
    'tests/handlers'
]

for dir_path in test_dirs:
    os.makedirs(dir_path, exist_ok=True) 