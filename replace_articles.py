import sys

with open("articles.html", "r") as f:
    text = f.read()

head_insertion = """
    <script src="https://unpkg.com/force-graph"></script>
    <style>
        .view-btn {
            background: #fff; border: 1px solid #ccc; padding: 5px 10px; cursor: pointer; border-radius: 3px; font-size: 13px; margin-right: 5px;
        }
        .view-btn:hover { background: #eee; }
        .view-btn.active { background: #ddd; font-weight: bold; }
        #graph-container {
            width: 100%;
            height: 500px;
            border: 1px solid #ccc;
            margin-top: 20px;
            background: #fff;
            display: none;
        }
    </style>
"""

# replace </style> to insert new styles and script
text = text.replace("</style>", head_insertion + "\n</style>")

buttons_html = """
        <div style="margin-bottom: 20px;">
            <button id="btn-list" class="view-btn active" onclick="toggleView('list')">List View</button>
            <button id="btn-graph" class="view-btn" onclick="toggleView('graph')">Graph View</button>
        </div>
        
        <div id="graph-container"></div>
        <div id="list-container">
"""

# replace <ul id="essay-list" class="essay-list">
# We will wrap the lists in #list-container
text = text.replace('<ul id="essay-list" class="essay-list">', buttons_html + '\n        <ul id="essay-list" class="essay-list">')

# replace footer to close the list-container
text = text.replace('<hr>\n        \n        <div class="footer">', '</div>\n        <hr>\n        \n        <div class="footer">')

script_insertion = """
        let myGraph = null;

        function toggleView(view) {
            document.getElementById('btn-list').classList.toggle('active', view === 'list');
            document.getElementById('btn-graph').classList.toggle('active', view === 'graph');
            document.getElementById('list-container').style.display = (view === 'list') ? 'block' : 'none';
            document.getElementById('graph-container').style.display = (view === 'graph') ? 'block' : 'none';
            
            if (view === 'graph' && myGraph !== null) {
                // Resize graph to fit container if it just became visible
                myGraph.width(document.getElementById('graph-container').clientWidth);
            }
        }

        function buildGraph(essays) {
            const nodes = [
                { id: "tools", group: "core", val: 5 },
                { id: "work", group: "core", val: 5 },
                { id: "reflections", group: "core", val: 5 }
            ];
            const links = [];
            
            // Add essays as nodes and connect them to their central nodes
            essays.forEach(essay => {
                // Skip if doesn't have at least one valid node
                if (!essay.nodes || essay.nodes.length === 0) return;
                
                nodes.push({
                    id: essay.url,
                    name: essay.title,
                    group: "essay",
                    val: 1,
                    url: essay.url
                });
                
                essay.nodes.forEach(centralNode => {
                    links.push({
                        source: essay.url,
                        target: centralNode
                    });
                });
            });

            myGraph = ForceGraph()(document.getElementById('graph-container'))
                .graphData({ nodes, links })
                .nodeId('id')
                .nodeVal('val')
                .nodeLabel('name')
                .nodeAutoColorBy('group')
                .linkDirectionalParticles(2)
                .linkDirectionalParticleSpeed(d => 0.005)
                .onNodeClick(node => {
                    if (node.url) window.location.href = node.url;
                });
        }
"""

text = text.replace("loadEssays();", "loadEssays();\n" + script_insertion)

# we need to inject buildGraph(essays); into loadEssays
text = text.replace("if (!essays || essays.length === 0) {", "buildGraph(essays);\n                if (!essays || essays.length === 0) {")

with open("articles.html", "w") as f:
    f.write(text)

