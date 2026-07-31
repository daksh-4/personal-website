import os
import sys
import re
import subprocess
import tempfile
import json
from pathlib import Path

def process_tex_to_html(input_file):
    # Read the tex file to get frontmatter
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract frontmatter block
    frontmatter_match = re.search(r'^%\s*---\n(.*?)^%\s*---', content, flags=re.MULTILINE | re.DOTALL)
    
    title = "Untitled Essay"
    date_val = "2026-01-01"
    nodes = []
    links = []
    
    if frontmatter_match:
        fm = frontmatter_match.group(1)
        # Parse title
        m = re.search(r'^%\s*title:\s*(.+)$', fm, flags=re.MULTILINE)
        if m: title = m.group(1).strip()
        # Parse date
        m = re.search(r'^%\s*date:\s*(.+)$', fm, flags=re.MULTILINE)
        if m: date_val = m.group(1).strip()
        # Parse nodes
        m = re.search(r'^%\s*nodes:\s*(.+)$', fm, flags=re.MULTILINE)
        if m: nodes = [n.strip() for n in m.group(1).split(',')]
        # Parse links
        m = re.search(r'^%\s*links:\s*(.+)$', fm, flags=re.MULTILINE)
        if m: links = [l.strip() for l in m.group(1).split(',')]
        
    return {
        "title": title,
        "date": date_val,
        "nodes": nodes,
        "links": links
    }
print(process_tex_to_html("drafts/template.tex"))
