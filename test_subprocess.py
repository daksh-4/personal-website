import subprocess
import os

print(os.path.abspath("drafts/template.tex"))
result = subprocess.run(["make4ht", "-u", "drafts/template.tex"], capture_output=True, text=True)
print("Code:", result.returncode)
print("Stderr:", result.stderr)
