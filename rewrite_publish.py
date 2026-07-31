import re

with open("publish.py", "r") as f:
    text = f.read()

# We need to insert extraction logic for tex and make4ht integration.
# Actually it is easier to write publish_new.py and overwrite publish.py

import os
