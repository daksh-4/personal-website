#!/bin/bash
# Run this script whenever you add a new essay to automatically update the essays list
# Usage: ./update-essays.sh

cd "$(dirname "$0")"

echo "[" > essays.json

first=true
for file in essays/*.html; do
    if [ -f "$file" ]; then
        # Extract title from the <title> tag or <h1> tag
        title=$(grep -o '<title>[^<]*</title>' "$file" | sed 's/<title>//;s/<\/title>//;s/ - Daksh Mehta//')
        
        if [ -z "$title" ]; then
            # Fallback: use filename without extension
            title=$(basename "$file" .html | sed 's/-/ /g')
        fi
        
        if [ "$first" = true ]; then
            first=false
        else
            echo "," >> essays.json
        fi
        
        printf '    { "title": "%s", "url": "%s" }' "$title" "$file" >> essays.json
    fi
done

echo "" >> essays.json
echo "]" >> essays.json

echo "✓ Updated essays.json with $(ls essays/*.html 2>/dev/null | wc -l | tr -d ' ') essays"
