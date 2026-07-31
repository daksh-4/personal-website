#!/usr/bin/env python3
"""
Converts a Markdown or LaTeX file to a styled HTML essay.
Usage: ./publish.py my-essay.md
       ./publish.py drafts/my-essay.md "Custom Title"
       ./publish.py drafts/my-essay.tex
"""

import sys
import re
import os
import subprocess
import tempfile
import json
from pathlib import Path

def get_frontmatter(text, is_tex=False):
    title = None
    date = "2026-06"
    category = None
    nodes = []
    links = []

    if is_tex:
        frontmatter_match = re.search(r'^%\s*---\n(.*?)^%\s*---', text, flags=re.MULTILINE | re.DOTALL)
        if frontmatter_match:
            fm = frontmatter_match.group(1)
            m = re.search(r'^%[ \t]*title:[ \t]*(.+)$', fm, flags=re.MULTILINE)
            if m: title = m.group(1).strip()

            m = re.search(r'^%[ \t]*date:[ \t]*(.+)$', fm, flags=re.MULTILINE)
            if m: date = m.group(1).strip()

            m = re.search(r'^%[ \t]*nodes:[ \t]*(.+)$', fm, flags=re.MULTILINE)
            if m: nodes = [n.strip().title() for n in m.group(1).split(',')]

            m = re.search(r'^%[ \t]*links:[ \t]*(.+)$', fm, flags=re.MULTILINE)
            if m:
                def normalize_link(l):
                    l = l.strip()
                    if l and '/' not in l and not l.endswith('.html'):
                        return f'essays/{l}.html'
                    return l
                links = [normalize_link(l) for l in m.group(1).split(',') if l.strip()]

            m = re.search(r'^%[ \t]*category:[ \t]*(.+)$', fm, flags=re.MULTILINE)
            if m: category = m.group(1).strip() or None
    return title, date, category, nodes, links

def markdown_to_html(md_text):
    # Minimal stub since original was long. We will just preserve basic markdown
    html = md_text
    category_match = re.search(r'^---\n.*?\bcategory:\s*([^\n]+).*?---\n', html, flags=re.DOTALL | re.IGNORECASE)
    category = category_match.group(1).strip() if category_match else None
    html = re.sub(r'^---\n.*?---\n', '', html, flags=re.DOTALL)
    
    html = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    html = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', html)
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
    
    blocks = re.split(r'\n\s*\n', html.strip())
    return '\n<br>\n'.join(blocks), category

def latex_to_html_make4ht(input_file):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Run make4ht
        print(f"Running make4ht on {input_file}...")
        result = subprocess.run(["make4ht", "-u", input_file, "-d", tmpdir], capture_output=True, text=True)
        if result.returncode != 0:
            print("make4ht error:\n" + result.stderr)
        
        base_name = Path(input_file).stem
        html_file = os.path.join(tmpdir, f"{base_name}.html")
        
        if not os.path.exists(html_file):
            print("Failed to generate HTML.")
            sys.exit(1)
            
        with open(html_file, 'r', encoding='utf-8') as f:
            full_html = f.read()
            
        # Extract body
        body_match = re.search(r'<body[^>]*>(.*?)</body>', full_html, flags=re.DOTALL | re.IGNORECASE)
        html_content = body_match.group(1) if body_match else full_html
        
        # Clean up auxiliary files generated next to the tex file
        directory = os.path.dirname(input_file)
        base = Path(input_file).stem
        for ext in ['.aux', '.log', '.lg', '.idv', '.xref', '.4tc', '.4ct', '.dvi', '.tmp']:
            junk = os.path.join(directory, base + ext)
            if os.path.exists(junk):
                try: os.remove(junk)
                except: pass
                
        return html_content

def title_from_filename(filepath):
    name = Path(filepath).stem
    return name.replace('-', ' ').title()

def filename_from_title(title):
    clean = re.sub(r'[^a-zA-Z0-9 ]', '', title.lower())
    return clean.replace(' ', '-') + '.html'

def create_essay_html(title, content, category=None, date="2026"):
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
            line-height: 1.6;
            color: #000;
            background-color: #f6f6ef;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2, h3, h4 {{ font-weight: bold; margin-bottom: 20px; margin-top: 30px; }}
        h1 {{ font-size: 20px; }}
        h2 {{ font-size: 18px; }}
        h3 {{ font-size: 16px; }}
        a {{ color: #000; text-decoration: underline; }}
        a:hover {{ color: #666; }}
        .date {{ color: #666; font-size: 12px; margin-bottom: 20px; }}
        .footer {{ margin-top: 50px; font-size: 12px; color: #666; border-top: 1px solid #ccc; padding-top: 20px; }}
        .nav {{ margin-bottom: 30px; }}
        .nav a {{ margin-right: 15px; }}
        .content {{ transition: opacity 0.15s ease; }}
        #version-bar {{ margin-bottom: 30px; display: none; }}
        #version-bar input[type=range] {{
            width: 100%;
            margin: 0 0 6px 0;
            accent-color: #333;
            cursor: pointer;
        }}
        #version-label {{
            font-size: 11px;
            color: #888;
        }}
        ins.vc-add {{ background: #d4edda; text-decoration: none; border-radius: 2px; padding: 0 1px; }}
        del.vc-del {{ background: #f8d7da; color: #721c24; text-decoration: line-through; border-radius: 2px; padding: 0 1px; }}
    </style>
</head>
<body>
    <div class="nav">
        <a href="../index.html">Home</a>
        <a href="../articles.html">Essays</a>
        <a href="../about.html">About</a>
    </div>

    <h1>{title}</h1>
    <div class="date">{date}</div>

    <div id="version-bar">
        <input type="range" id="version-slider" min="0" max="0" value="0" step="1">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-top:4px;">
            <div id="version-label"></div>
            <label id="diff-label" style="display:none;font-size:11px;color:#888;cursor:pointer;user-select:none;"><input type="checkbox" id="diff-toggle" style="margin-right:4px;cursor:pointer;">highlight changes</label>
        </div>
    </div>

    <div class="content">
        {content}
    </div>

    <div class="footer">
        &copy; 2026 Daksh Mehta
    </div>
    <script data-goatcounter="https://daksh-4.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
    <script>
    (async function () {{
        const repo = 'daksh-4/personal-website';
        const filename = window.location.pathname.split('/').pop() || '';
        if (!filename) return;
        const filePath = 'essays/' + filename;
        const cacheKey = 'vc_' + filename;

        let commits;
        try {{
            const cached = sessionStorage.getItem(cacheKey);
            if (cached) commits = JSON.parse(cached);
            else {{
                const res = await fetch(`https://api.github.com/repos/${{repo}}/commits?path=${{filePath}}&per_page=100`);
                if (!res.ok) return;
                commits = await res.json();
                sessionStorage.setItem(cacheKey, JSON.stringify(commits));
            }}
        }} catch (e) {{ return; }}

        const versions = commits.filter(c => /^publish:/i.test(c.commit.message.trim())).reverse();
        if (versions.length === 0) return;

        const bar        = document.getElementById('version-bar');
        const slider     = document.getElementById('version-slider');
        const label      = document.getElementById('version-label');
        const diffLabel  = document.getElementById('diff-label');
        const diffToggle = document.getElementById('diff-toggle');
        const contentEl  = document.querySelector('.content');
        const currentHTML = contentEl.innerHTML;
        const cache = {{}};
        let activePos = versions.length;

        slider.max   = versions.length;
        slider.value = versions.length;

        function fmtDate(iso) {{
            return new Date(iso).toLocaleDateString('en-GB', {{ year: 'numeric', month: 'long', day: 'numeric' }});
        }}

        function setLabel(pos) {{
            if (pos === versions.length) {{
                label.textContent = 'Current version';
                diffLabel.style.display = 'none';
            }} else {{
                const v = versions[pos];
                const msg = v.commit.message.trim().replace(/^publish:\\s*/i, '');
                label.textContent = fmtDate(v.commit.author.date) + (msg ? ' — ' + msg : '');
                diffLabel.style.display = '';
            }}
        }}

        function getBlocks(html) {{
            const d = document.createElement('div');
            d.innerHTML = html;
            return Array.from(d.children).map(el => ({{
                html: el.outerHTML,
                key:  el.textContent.replace(/\\s+/g, ' ').trim()
            }})).filter(b => b.key);
        }}

        function blockDiff(oldB, newB) {{
            const m = oldB.length, n = newB.length;
            if (m * n > 100000) return null;
            const dp = Array.from({{length: m + 1}}, () => new Int32Array(n + 1));
            for (let i = 1; i <= m; i++)
                for (let j = 1; j <= n; j++)
                    dp[i][j] = oldB[i-1].key === newB[j-1].key
                        ? dp[i-1][j-1] + 1 : Math.max(dp[i-1][j], dp[i][j-1]);
            const ops = [];
            let i = m, j = n;
            while (i > 0 || j > 0) {{
                if (i > 0 && j > 0 && oldB[i-1].key === newB[j-1].key) {{
                    ops.unshift({{t:'=', b: newB[j-1]}}); i--; j--;
                }} else if (j > 0 && (i === 0 || dp[i][j-1] >= dp[i-1][j])) {{
                    ops.unshift({{t:'+', b: newB[j-1]}}); j--;
                }} else {{
                    ops.unshift({{t:'-', b: oldB[i-1]}}); i--;
                }}
            }}
            return ops;
        }}

        function renderBlockDiff(ops) {{
            return ops.map(op => {{
                if (op.t === '=') return op.b.html;
                if (op.t === '+') return '<div style="background:#d4edda;border-radius:3px;padding:0 4px;margin:2px 0;">' + op.b.html + '</div>';
                return '<div style="background:#f8d7da;color:#721c24;text-decoration:line-through;border-radius:3px;padding:0 4px;margin:2px 0;opacity:0.8;">' + op.b.html + '</div>';
            }}).join('');
        }}

        async function fetchOld(sha) {{
            if (cache[sha]) return;
            try {{
                const r = await fetch(`https://raw.githubusercontent.com/${{repo}}/${{sha}}/${{filePath}}`);
                const text = await r.text();
                const doc = new DOMParser().parseFromString(text, 'text/html');
                const old = doc.querySelector('.content');
                cache[sha] = old ? old.innerHTML : '';
            }} catch (e) {{
                cache[sha] = '';
            }}
        }}

        async function showContent(pos) {{
            contentEl.style.opacity = '0';
            await new Promise(r => setTimeout(r, 150));
            if (pos === versions.length) {{
                contentEl.innerHTML = currentHTML;
            }} else {{
                const sha = versions[pos].sha;
                await fetchOld(sha);
                if (diffToggle.checked && cache[sha]) {{
                    const ops = blockDiff(getBlocks(cache[sha]), getBlocks(currentHTML));
                    contentEl.innerHTML = ops ? renderBlockDiff(ops) : currentHTML;
                }} else {{
                    contentEl.innerHTML = cache[sha] || currentHTML;
                }}
            }}
            activePos = pos;
            contentEl.style.opacity = '1';
        }}

        setLabel(versions.length);
        bar.style.display = 'block';

        slider.addEventListener('input', () => setLabel(parseInt(slider.value)));
        slider.addEventListener('change', async () => {{
            const pos = parseInt(slider.value);
            if (pos === activePos) return;
            await showContent(pos);
        }});
        diffToggle.addEventListener('change', () => showContent(activePos));
    }})();
    </script>
</body>
</html>'''

def main():
    if len(sys.argv) < 2:
        print("Usage: ./publish.py <markdown-or-tex-file> [title]")
        sys.exit(1)
        
    input_file = sys.argv[1]
    is_tex = input_file.endswith('.tex')
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    title, date, category, nodes, links = get_frontmatter(content, is_tex=is_tex)
    
    if not title:
        title = title_from_filename(input_file)
        
    if len(sys.argv) >= 3:
        title = sys.argv[2]
        
    if is_tex:
        html_content = latex_to_html_make4ht(input_file)
    else:
        html_content, category = markdown_to_html(content)
        
    full_html = create_essay_html(title, html_content, category=category, date=date)
    
    output_filename = filename_from_title(title)
    output_file = Path('essays') / output_filename
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_html)
        
    print(f"✓ Created: {output_file}")
    
    # Update JSON network graph metadata
    essays_json_path = 'essays.json'
    if os.path.exists(essays_json_path):
        with open(essays_json_path, 'r', encoding='utf-8') as f:
            try:
                essays = json.load(f)
            except:
                essays = []
    else:
        essays = []
        
    # Update entry if exists, else append
    essay_data = {
        "title": title,
        "url": f"essays/{output_filename}",
        "date": date,
        "category": category or "",
        "nodes": nodes,
        "links": links
    }
    
    # Remove old entry matching the url
    essays = [e for e in essays if e.get("url") != essay_data["url"]]
    essays.append(essay_data)
    
    with open(essays_json_path, 'w', encoding='utf-8') as f:
        json.dump(essays, f, indent=4)

    print(f"✓ Updated essays.json metadata network")

    # Embed essays data directly in articles.html so it works without a server
    articles_path = 'articles.html'
    if os.path.exists(articles_path):
        with open(articles_path, 'r', encoding='utf-8') as f:
            articles_html = f.read()
        essays_js = json.dumps(essays, indent=4)
        new_block = f'    <!-- ESSAYS-DATA-START -->\n    <script id="essays-data">\n    window.ESSAYS_DATA = {essays_js};\n    </script>\n    <!-- ESSAYS-DATA-END -->'
        updated = re.sub(
            r'    <!-- ESSAYS-DATA-START -->.*?<!-- ESSAYS-DATA-END -->',
            new_block,
            articles_html,
            flags=re.DOTALL
        )
        with open(articles_path, 'w', encoding='utf-8') as f:
            f.write(updated)
        print(f"✓ Embedded essay data into articles.html")

if __name__ == '__main__':
    main()
