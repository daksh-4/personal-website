#!/usr/bin/env python3
"""
Converts a Markdown file to a styled HTML essay.
Usage: ./publish.py my-essay.md
       ./publish.py drafts/my-essay.md "Custom Title"
"""

import sys
import re
import os
from pathlib import Path

def markdown_to_html(md_text):
    """Convert markdown to HTML."""
    html = md_text
    
    # Remove YAML frontmatter (---...---)
    html = re.sub(r'^---\n.*?---\n', '', html, flags=re.DOTALL)
    
    # Convert headers
    html = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    
    # Convert bold and italic
    html = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', html)
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    html = re.sub(r'___(.+?)___', r'<strong><em>\1</em></strong>', html)
    html = re.sub(r'__(.+?)__', r'<strong>\1</strong>', html)
    html = re.sub(r'_(.+?)_', r'<em>\1</em>', html)
    
    # Convert links [text](url)
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)
    
    # Convert inline code
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
    
    # Split into paragraphs (double newline)
    paragraphs = re.split(r'\n\s*\n', html.strip())
    
    processed = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        # Don't wrap headers in <p>
        if p.startswith('<h') or p.startswith('<ul') or p.startswith('<ol'):
            processed.append(p)
        else:
            # Replace single newlines with spaces within paragraph
            p = re.sub(r'\n', ' ', p)
            processed.append(f'<p>{p}</p>')
    
    return '\n            \n            '.join(processed)

def create_essay_html(title, content, date="2026"):
    """Wrap content in the essay template."""
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Daksh Mehta</title>
    <style>
        body {{
            font-family: Verdana, Geneva, sans-serif;
            font-size: 14px;
            line-height: 1.8;
            color: #000;
            background-color: #f6f6ef;
            margin: 0;
            padding: 20px;
        }}
        
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        h1 {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        h2 {{
            font-size: 16px;
            font-weight: bold;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        
        h3 {{
            font-size: 15px;
            font-weight: bold;
            margin-top: 25px;
            margin-bottom: 12px;
        }}
        
        a {{
            color: #000;
            text-decoration: underline;
        }}
        
        a:hover {{
            color: #666;
        }}
        
        .nav {{
            margin-bottom: 30px;
        }}
        
        .nav a {{
            margin-right: 15px;
        }}
        
        .date {{
            color: #666;
            font-size: 12px;
            margin-bottom: 30px;
        }}
        
        .content p {{
            margin-bottom: 20px;
            text-align: justify;
        }}
        
        .content code {{
            background-color: #e8e8e0;
            padding: 2px 5px;
            font-family: monospace;
        }}
        
        .footer {{
            margin-top: 50px;
            font-size: 12px;
            color: #666;
        }}
        
        hr {{
            border: none;
            border-top: 1px solid #ccc;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <div class="date">{date}</div>
        
        <div class="nav">
            <a href="../index.html">Home</a>
            <a href="../articles.html">Essays</a>
            <a href="../about.html">About</a>
        </div>
        
        <hr>
        
        <div class="content">
            {content}
        </div>
        
        <hr>
        
        <div class="footer">
            &copy; 2026 Daksh Mehta
        </div>
    </div>
</body>
</html>
'''

def title_from_filename(filename):
    """Convert filename to title."""
    name = Path(filename).stem
    # Replace hyphens/underscores with spaces and title case
    return name.replace('-', ' ').replace('_', ' ').title()

def filename_from_title(title):
    """Convert title to filename."""
    # Lowercase, replace spaces with hyphens, remove special chars
    filename = title.lower()
    filename = re.sub(r'[^a-z0-9\s-]', '', filename)
    filename = re.sub(r'\s+', '-', filename)
    return filename + '.html'

def main():
    if len(sys.argv) < 2:
        print("Usage: ./publish.py <markdown-file> [title]")
        print("Example: ./publish.py drafts/my-essay.md")
        print("         ./publish.py drafts/my-essay.md \"My Custom Title\"")
        sys.exit(1)
    
    md_file = sys.argv[1]
    
    if not os.path.exists(md_file):
        print(f"Error: File '{md_file}' not found")
        sys.exit(1)
    
    # Read markdown
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Get title (from argument or filename)
    if len(sys.argv) >= 3:
        title = sys.argv[2]
    else:
        # Try to extract title from first # header
        title_match = re.search(r'^# (.+)$', md_content, re.MULTILINE)
        if title_match:
            title = title_match.group(1)
            # Remove the title from content since we'll add it in template
            md_content = re.sub(r'^# .+\n', '', md_content, count=1)
        else:
            title = title_from_filename(md_file)
    
    # Convert to HTML
    html_content = markdown_to_html(md_content)
    
    # Create full HTML
    full_html = create_essay_html(title, html_content)
    
    # Determine output filename
    script_dir = Path(__file__).parent
    essays_dir = script_dir / 'essays'
    output_file = essays_dir / filename_from_title(title)
    
    # Write file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_html)
    
    print(f"✓ Created: {output_file}")
    
    # Run update-essays.sh to refresh the list
    update_script = script_dir / 'update-essays.sh'
    if update_script.exists():
        os.system(f'"{update_script}"')

if __name__ == '__main__':
    main()
