import os
import glob
import re

os.chdir("src")

count = 0
for filepath in glob.glob("**/*.jsx", recursive=True):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 1. Add missing backtick to the start if it currently has `fetch(${`
    # (Since some might already be modified correctly, but my previous replace missed the backtick)
    # The erroneous string: fetch(${import.meta.env.VITE_API_URL || ''}/api
    # Replace with: fetch(`${import.meta.env.VITE_API_URL || ''}/api
    content = content.replace("fetch(${import.meta.env.VITE_API_URL || ''}/api", "fetch(`${import.meta.env.VITE_API_URL || ''}/api")
    
    # 2. Replace the trailing single quote with a backtick.
    # The string now looks like: fetch(`${import.meta.env.VITE_API_URL || ''}/api/xxx'
    # We match it and change the `'` to ``` 
    pattern = r"(fetch\(`\$\{import\.meta\.env\.VITE_API_URL \|\| ''\}/api[^']*)'"
    new_content = re.sub(pattern, r"\1`", content)
    
    if new_content != content or count == 0:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        count += 1
        print(f"Fixed {filepath}")

print(f"Done fixing {count} files.")
