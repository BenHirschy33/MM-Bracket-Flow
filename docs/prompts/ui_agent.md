🎨 UI Reconstruction Agent Prompt
Objective: Rebuild the front-end layout to match the "Quad" design and refine weight labels.

Detailed Task:

Layout Reconstruction:
Modify web/templates/index.html and web/static/css/styles.css to implement a 2x2 grid for the regions.
Placement: Top-Left: East, Bottom-Left: South, Top-Right: Midwest, Bottom-Right: West, Center: Final Four/Championship.
Ensure right-side regions (Midwest/West) flow from Right-to-Left (mirrored) towards the center.

Weight Renaming:
Rename "Highest Average" to "Average Bracket" in the UI tabs and relevant labels.
Rename "Perfect Bracket" (ensure consistency).

Responsive Zoom:
Ensure the zoom-container correctly centers the new 2x2 layout by default.
