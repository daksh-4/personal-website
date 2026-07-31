#!/usr/bin/env python3
"""
Migrates all existing essay HTML files to add the diff toggle feature.
Handles two cases:
  - Essays already having <div id="version-bar"> (newer): update HTML + CSS + script
  - Essays with version-bar in CSS/JS but no HTML element (older): add HTML + update CSS + script
Safe to re-run — skips files already updated.
"""
import os, re

essays_dir = 'essays'

# --- CSS to inject (before </style>) ---
NEW_CSS_LINES = (
    '        ins.vc-add { background: #d4edda; text-decoration: none; '
    'border-radius: 2px; padding: 0 1px; }\n'
    '        del.vc-del { background: #f8d7da; color: #721c24; '
    'text-decoration: line-through; border-radius: 2px; padding: 0 1px; }\n'
)

# --- Version bar HTML element ---
NEW_BAR_HTML = (
    '\n    <div id="version-bar">\n'
    '        <input type="range" id="version-slider" min="0" max="0" value="0" step="1">\n'
    '        <div style="display:flex;justify-content:space-between;align-items:center;margin-top:4px;">\n'
    '            <div id="version-label"></div>\n'
    '            <label id="diff-label" style="display:none;font-size:11px;color:#888;'
    'cursor:pointer;user-select:none;"><input type="checkbox" id="diff-toggle" '
    'style="margin-right:4px;cursor:pointer;">highlight changes</label>\n'
    '        </div>\n'
    '    </div>\n'
)

# Matches the old version bar when it exists (without diff-label)
OLD_BAR_RE = re.compile(
    r'<div id="version-bar">\s*'
    r'<input[^>]*>\s*'
    r'<div id="version-label"></div>\s*'
    r'</div>',
    re.DOTALL
)

# --- New JS script ---
NEW_SCRIPT = """<script>
    (async function () {
        const repo = 'daksh-4/personal-website';
        const filename = window.location.pathname.split('/').pop() || '';
        if (!filename) return;
        const filePath = 'essays/' + filename;
        const cacheKey = 'vc_' + filename;

        let commits;
        try {
            const cached = sessionStorage.getItem(cacheKey);
            if (cached) commits = JSON.parse(cached);
            else {
                const res = await fetch(`https://api.github.com/repos/${repo}/commits?path=${filePath}&per_page=100`);
                if (!res.ok) return;
                commits = await res.json();
                sessionStorage.setItem(cacheKey, JSON.stringify(commits));
            }
        } catch (e) { return; }

        const versions = commits.filter(c => /^publish:/i.test(c.commit.message.trim())).reverse();
        if (versions.length === 0) return;

        const bar        = document.getElementById('version-bar');
        const slider     = document.getElementById('version-slider');
        const label      = document.getElementById('version-label');
        const diffLabel  = document.getElementById('diff-label');
        const diffToggle = document.getElementById('diff-toggle');
        const contentEl  = document.querySelector('.content');
        const currentHTML = contentEl.innerHTML;
        const cache = {};
        let activePos = versions.length;

        slider.max   = versions.length;
        slider.value = versions.length;

        function fmtDate(iso) {
            return new Date(iso).toLocaleDateString('en-GB', { year: 'numeric', month: 'long', day: 'numeric' });
        }

        function setLabel(pos) {
            if (pos === versions.length) {
                label.textContent = 'Current version';
                diffLabel.style.display = '';
            } else {
                const v = versions[pos];
                const msg = v.commit.message.trim().replace(/^publish:\\s*/i, '');
                label.textContent = fmtDate(v.commit.author.date) + (msg ? ' — ' + msg : '');
                diffLabel.style.display = 'none';
            }
        }

        function getBlocks(html) {
            const d = document.createElement('div');
            d.innerHTML = html;
            return Array.from(d.children).map(el => ({
                html: el.outerHTML,
                key:  el.textContent.replace(/\\s+/g, ' ').trim()
            })).filter(b => b.key);
        }

        function blockDiff(oldB, newB) {
            const m = oldB.length, n = newB.length;
            if (m * n > 100000) return null;
            const dp = Array.from({length: m + 1}, () => new Int32Array(n + 1));
            for (let i = 1; i <= m; i++)
                for (let j = 1; j <= n; j++)
                    dp[i][j] = oldB[i-1].key === newB[j-1].key
                        ? dp[i-1][j-1] + 1 : Math.max(dp[i-1][j], dp[i][j-1]);
            const ops = [];
            let i = m, j = n;
            while (i > 0 || j > 0) {
                if (i > 0 && j > 0 && oldB[i-1].key === newB[j-1].key) {
                    ops.unshift({t:'=', b: newB[j-1]}); i--; j--;
                } else if (j > 0 && (i === 0 || dp[i][j-1] >= dp[i-1][j])) {
                    ops.unshift({t:'+', b: newB[j-1]}); j--;
                } else {
                    ops.unshift({t:'-', b: oldB[i-1]}); i--;
                }
            }
            return ops;
        }

        function renderBlockDiff(ops) {
            return ops.map(op => {
                if (op.t === '=') return op.b.html;
                if (op.t === '+') return '<div style="background:#d4edda;border-radius:3px;padding:0 4px;margin:2px 0;">' + op.b.html + '</div>';
                return '<div style="background:#f8d7da;color:#721c24;text-decoration:line-through;border-radius:3px;padding:0 4px;margin:2px 0;opacity:0.8;">' + op.b.html + '</div>';
            }).join('');
        }

        async function fetchOld(sha) {
            if (cache[sha]) return;
            try {
                const r = await fetch(`https://raw.githubusercontent.com/${repo}/${sha}/${filePath}`);
                const text = await r.text();
                const doc = new DOMParser().parseFromString(text, 'text/html');
                const old = doc.querySelector('.content');
                cache[sha] = old ? old.innerHTML : '';
            } catch (e) {
                cache[sha] = '';
            }
        }

        async function showContent(pos) {
            contentEl.style.opacity = '0';
            await new Promise(r => setTimeout(r, 150));
            if (pos === versions.length) {
                if (diffToggle.checked) {
                    const sha = versions[versions.length - 1].sha;
                    await fetchOld(sha);
                    if (cache[sha]) {
                        const ops = blockDiff(getBlocks(cache[sha]), getBlocks(currentHTML));
                        contentEl.innerHTML = ops ? renderBlockDiff(ops) : currentHTML;
                    } else {
                        contentEl.innerHTML = currentHTML;
                    }
                } else {
                    contentEl.innerHTML = currentHTML;
                }
            } else {
                const sha = versions[pos].sha;
                await fetchOld(sha);
                contentEl.innerHTML = cache[sha] || currentHTML;
            }
            activePos = pos;
            contentEl.style.opacity = '1';
        }

        setLabel(versions.length);
        bar.style.display = 'block';

        slider.addEventListener('input', () => setLabel(parseInt(slider.value)));
        slider.addEventListener('change', async () => {
            const pos = parseInt(slider.value);
            if (pos === activePos) return;
            await showContent(pos);
        });
        diffToggle.addEventListener('change', () => showContent(activePos));
    })();
    </script>"""

OLD_SCRIPT_RE = re.compile(
    r'<script>\s*\(async function \(\) \{.*?\}\)\(\);\s*</script>',
    re.DOTALL
)

updated = skipped = 0

for fname in sorted(os.listdir(essays_dir)):
    if not fname.endswith('.html'):
        continue
    path = os.path.join(essays_dir, fname)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Skip files that don't have version bar at all
    if '#version-bar' not in content and 'version-bar' not in content:
        continue

    # Skip already-updated files (marker = toggle on current, compare vs previous)
    if 'versions[versions.length - 1].sha' in content:
        print(f'  skip  {fname} (already updated)')
        skipped += 1
        continue

    # 1. Add CSS (before </style>)
    if 'ins.vc-add' not in content:
        content = content.replace('    </style>', NEW_CSS_LINES + '    </style>', 1)

    # 2. Version bar HTML: update if present, insert after .date div if absent
    if OLD_BAR_RE.search(content):
        content = OLD_BAR_RE.sub(NEW_BAR_HTML.strip(), content, count=1)
    elif '<div id="version-bar">' not in content:
        # Insert after the date div
        content = re.sub(
            r'(<div class="date">[^<]*</div>)',
            r'\1' + NEW_BAR_HTML,
            content, count=1
        )

    # 3. Replace version script
    if OLD_SCRIPT_RE.search(content):
        content = OLD_SCRIPT_RE.sub(lambda _: NEW_SCRIPT, content, count=1)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'  updated {fname}')
    updated += 1

print(f'\nDone: {updated} updated, {skipped} already up to date.')
