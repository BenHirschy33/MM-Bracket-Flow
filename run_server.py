import sys
import os

root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, root_dir) # For core.*
sys.path.insert(0, os.path.join(root_dir, 'local_lib')) # For flask, etc.
sys.path.insert(0, os.path.join(root_dir, 'web')) # For app.py

import app
app.app.run(debug=True, port=5001)
