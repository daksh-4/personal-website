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
    
    # Extract frontmatter category if present
    category_match = re.search(r'^---\n.*?\bcategory:\s*([^\n]+).*?---\n', html, flags=re.DOTALL | re.IGNORECASE)
    category = category_match.group(1).strip() if category_match else None
    
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
    
    # Split into blocks (double newline)
    blocks = re.split(r'\n\s*\n', html.strip())

    def process_list_block(lines):
        # Build list items from lines that start with list markers.
        # If non-list lines appear in the block (e.g. "Header:\n- a\n- b"),
        # those will be handled outside this function by splitting runs.
        is_ordered = all(re.match(r"^\s*\d+\.\s+", ln) for ln in lines if ln.strip() != '')
        tag = 'ol' if is_ordered else 'ul'
        items = []
        for ln in lines:
            ln = ln.strip()
            if not ln:
                continue
            m_ord = re.match(r"^\s*\d+\.\s+(.*)$", ln)
            m_un = re.match(r"^\s*[-\*]\s+(.*)$", ln)
            if m_ord:
                items.append(m_ord.group(1))
            elif m_un:
                items.append(m_un.group(1))
            else:
                # fallback: whole line
                items.append(ln)
        inner = '\n'.join(f'                <li>{item}</li>' for item in items)
        return f'<{tag}>\n{inner}\n            </{tag}>'

    processed = []
    for blk in blocks:
        blk = blk.strip()
        if not blk:
            continue
        # If block is a header already converted
        if blk.startswith('<h'):
            processed.append(blk)
            continue
        # Check if block contains any list lines. If so, split the block
        # into runs of list-lines and non-list-lines so we don't accidentally
        # include inline list markers inside paragraphs.
        lines = blk.split('\n')
        runs = []
        current_run = {'type': None, 'lines': []}

        def line_type(ln):
            if re.match(r"^\s*[-\*]\s+", ln) or re.match(r"^\s*\d+\.\s+", ln):
                return 'list'
            return 'text'

        for ln in lines:
            lt = line_type(ln)
            if current_run['type'] is None:
                current_run = {'type': lt, 'lines': [ln]}
            elif current_run['type'] == lt:
                current_run['lines'].append(ln)
            else:
                runs.append(current_run)
                current_run = {'type': lt, 'lines': [ln]}
        if current_run['lines']:
            runs.append(current_run)

        if any(r['type'] == 'list' for r in runs):
            for r in runs:
                if r['type'] == 'list':
                    list_html = process_list_block(r['lines'])
                    processed.append(list_html)
                else:
                    # normal paragraph from text run
                    p = re.sub(r'\n', ' ', '\n'.join(r['lines']).strip())
                    processed.append(f'<p>{p}</p>')
            continue

        # Normal paragraph: replace single newlines with spaces
        p = re.sub(r'\n', ' ', blk)
        processed.append(f'<p>{p}</p>')

    return '\n            \n            '.join(processed), category

def latex_to_html(tex_text):
    """Convert a simple subset of LaTeX to HTML."""
    html = tex_text
    
    # Extract metadata using regex
    title_match = re.search(r'\\title\{([^}]+)\}', html)
    title = title_match.group(1).strip() if title_match else None
    
    date_match = re.search(r'\\date\{([^}]+)\}', html)
    date = date_match.group(1).strip() if date_match else "2026"
    
    # Optional % category: data
    category_match = re.search(r'%\s*category:\s*([^\n]+)', html, flags=re.IGNORECASE)
    category = category_match.group(1).strip() if category_match else None
    
    # Extract body between \begin{document} and \end{document}
    body_match = re.search(r'\\begin\{document\}(.*?)\\end\{document\}', html, flags=re.DOTALL)
    if body_match:
        html = body_match.group(1)
    
    # Remove \maketitle
    html = re.sub(r'\\maketitle', '', html)
    
    # Convert headers
    html = re.sub(r'\\section\*?\{([^}]+)\}', r'<h2>\1</h2>', html)
    html = re.sub(r'\\subsection\*?\{([^}]+)\}', r'<h3>\1</h3>', html)
    html = re.sub(r'\\subsubsection\*?\{([^}]+)\}', r'<h4>\1</h4>', html)
    html = re.sub(r'\\paragraph\*?\{([^}]+)\}', r'<h5>\1</h5>', html)
    
    # Convert styling
    html = re.sub(r'\\textbf\{([^}]+)\}', r'<strong>\1</strong>', html)
    html = re.sub(r'\\textit\{([^}]+)\}', r'<em>\1</em>', html)
    html = re.sub(r'\\emph\{([^}]+)\}', r'<em>\1</em>', html)
    
    # Check for figures and graphics
    # We will convert \begin{figure}...\end{figure} containing \includegraphics to standard HTML <img>
    def process_figure(match):
        content = match.group(1)
        src_match = re.search(r'\\includegraphics(?:\[.*?\])?\{([^}]+)\}', content)
        caption_match = re.search(r'\\caption\{([^}]+)\}', content)
        label_match = re.search(r'\\label\{([^}]+)\}', content)
        
        if not src_match:
            return ""
            
        src = src_match.group(1)
        caption = caption_match.group(1) if caption_match else ""
        label = label_match.group(1) if label_match else ""
        
        img_id = f' id="{label}"' if label else ""
        
        return f'<figure{img_id} style="text-align: center;">\n<img src="../files/{Path(src).name}" alt="{caption}" style="max-width: 100%; height: auto;">\n<figcaption><em>{caption}</em></figcaption>\n</figure>'

    html = re.sub(r'\\begin\{figure\}.*?(.*?)\\end\{figure\}', process_figure, html, flags=re.DOTALL)
    
    # Basic ref conversion assuming href points to the label ID
    html = re.sub(r'Figure \\ref\{([^}]+)\}', r'<a href="#\1">Figure</a>', html)

    # Convert verbatim block to <code> block inside <pre>
    html = re.sub(r'\\begin\{verbatim\}(.*?)\\end\{verbatim\}', r'<pre><code>\1</code></pre>', html, flags=re.DOTALL)

    # Clean leftover \\\\ for paragraphs where we might want standard breaks
    html = re.sub(r'\\\\\n?', '<br>\n', html)
    
    # Split into blocks based on double blank lines to process paragraphs and lists
    blocks = re.split(r'\n\s*\n', html.strip())
    
    processed = []
    in_list = False
    list_tag = ''
    
    for blk in blocks:
        blk = blk.strip()
        if not blk: continue
        
        # Check if block is a heading or line break
        if re.match(r'^<h[1-6]>', blk) or blk == '<br>':
            processed.append(blk)
            continue
            
        # Process lists line by line
        lines = blk.split('\n')
        new_lines = []
        for line in lines:
            if r'\begin{enumerate}' in line:
                in_list = True
                list_tag = 'ol'
                new_lines.append('<ol>')
                continue
            elif r'\begin{itemize}' in line:
                in_list = True
                list_tag = 'ul'
                new_lines.append('<ul>')
                continue
            elif r'\end{enumerate}' in line:
                in_list = False
                new_lines.append('</ol>')
                continue
            elif r'\end{itemize}' in line:
                in_list = False
                new_lines.append('</ul>')
                continue
                
            if in_list and r'\item' in line:
                item_content = re.sub(r'\\item\s*', '', line).strip()
                new_lines.append(f'<li>{item_content}</li>')
            elif in_list:
                # continuation of list item
                new_lines.append(line.strip())
            else:
                new_lines.append(line)
                
        if in_list:
            processed.append('\n'.join(new_lines))
        else:
            # combine into paragraph if it's not wrapped in html tags
            joined = ' '.join(new_lines).strip()
            if joined.startswith('<') and not joined.startswith('<strong'):
                processed.append(joined)
            else:
                processed.append(f'<p>{joined}</p>')
                
    return '\n'.join(processed), category, title, date

def create_essay_html(title, content, category=None, date="2026"):
    """Wrap content in the essay template."""
    category_meta = f'\n    <meta name="category" content="{category}">' if category else ''
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">{category_meta}
    <title>{title} - Daksh Mehta</title>
    <!-- MathJax for rendering math -->
    <script>
      MathJax = {{
        tex: {{
          inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
          displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']]
        }}
      }};
    </script>
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
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
    <script data-goatcounter="https://daksh-4.goatcounter.com/count"
            async src="//gc.zgo.at/count.js"></script>
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
        print("Usage: ./publish.py <markdown-or-tex-file> [title]")
        print("Example: ./publish.py drafts/my-essay.md")
        print("         ./publish.py drafts/my-essay.tex \"My Custom Title\"")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found")
        sys.exit(1)
    
    # Read file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Process based on extension
    is_tex = input_file.endswith('.tex')
    
    if is_tex:
        html_content, category, default_title, date = latex_to_html(content)
        title = default_title or title_from_filename(input_file)
    else:
        # Default markdown processing
        date = "2026"  # default markdown date
        # Try to extract title from first # header
        title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
        if title_match:
            title = title_match.group(1)
            # Remove the title from content since we'll add it in template
            content = re.sub(r'^# .+\n', '', content, count=1)
        else:
            title = title_from_filename(input_file)
            
        html_content, category = markdown_to_html(content)
    
    # Override title if provided as argument
    if len(sys.argv) >= 3:
        title = sys.argv[2]
        
    # Create full HTML
    full_html = create_essay_html(title, html_content, category=category, date=date)
    
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
