import sys
import re
import os
import subprocess
import tempfile
import json
from pathlib import Path

def extract_tex_metadata(tex_text):
    title = "Untitled Essay"
    date_val = "2026-06"
    nodes = []
    links = []
    
    frontmatter_match = re.search(r'^%\s*---\n(.*?)^%\s*---', tex_text, flags=re.MULTILINE | re.DOTALL)
    if frontmatter_match:
        fm = frontmatter_match.group(1)
        m = re.search(r'^%\s*title:\s*(.+)$', fm, flags=re.MULTILINE)
        if m: title = m.group(1).strip()
        
        m = re.search(r'^%\s*date:\s*(.+)$', fm, flags=re.MULTILINE)
        if m: date_val = m.group(1).strip()
        
        m = re.search(r'^%\s*nodes:\s*(.+)$', fm, flags=re.MULTILINE)
        if m: nodes = [n.strip() for n in m.group(1).split(',')]
        
        m = re.search(r'^%\s*links:\s*(.+)$', fm, flags=re.MULTILINE)
        if m: links = [l.strip() for l in m.group(1).split(',')]
        
        m = re.search(r'^%\s*category:\s*(.+)$', fm, flags=re.MULTILINE)
        if m: category = m.group(1).strip()
        else: category = None
    else:
        category = None
        
    return title, date_val, nodes, links, category

# Modify publish.py
with open("publish.py", "r") as f:
    publish_code = f.read()

# Replace latex_to_html
# We'll just define a new publish script that handles make4ht, and replace publish.py with it.
