import os
import sys

with open("publish.py", "r") as f:
    publish_code = f.read()

import re

# We will inject process_tex_to_html function and update the main function to handle it
# Wait, make it simple, let's just make a new publish_tex.py or rewrite publish.py using string replace tools.
