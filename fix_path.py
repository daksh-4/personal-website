with open("publish.py", "r") as f:
    text = f.read()

text = text.replace('os.path.abspath(input_file)', 'input_file')
with open("publish.py", "w") as f:
    f.write(text)
