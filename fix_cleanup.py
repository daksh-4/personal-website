with open("publish.py", "r") as f:
    text = f.read()

cleanup_str = """
        return html_content

def title_from_filename(filepath):
"""

new_cleanup_str = """
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
"""

text = text.replace(cleanup_str, new_cleanup_str)

with open("publish.py", "w") as f:
    f.write(text)

