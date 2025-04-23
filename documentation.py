#!/usr/bin/env python3
"""
Documentation generator for Faculty Conference Travel System.
This script generates documentation for the entire project.
"""

import os
import sys
import inspect
import importlib
import pkgutil
import markdown
import re
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Output directory for documentation
DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")

# CSS for HTML documentation
CSS = """
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.6;
    color: #333;
    max-width: 900px;
    margin: 0 auto;
    padding: 20px;
}
h1, h2, h3, h4 {
    color: #1e88e5;
}
code {
    background-color: #f5f5f5;
    padding: 2px 5px;
    border-radius: 3px;
    font-family: monospace;
}
pre {
    background-color: #f5f5f5;
    padding: 15px;
    border-radius: 5px;
    overflow-x: auto;
}
.method {
    margin-bottom: 20px;
    border-left: 3px solid #1e88e5;
    padding-left: 15px;
}
.class {
    margin-bottom: 30px;
    border: 1px solid #ddd;
    border-radius: 5px;
    padding: 20px;
    background-color: #fafafa;
}
.module {
    margin-bottom: 40px;
}
table {
    border-collapse: collapse;
    width: 100%;
}
th, td {
    border: 1px solid #ddd;
    padding: 8px;
}
th {
    background-color: #f2f2f2;
    text-align: left;
}
.toc {
    background-color: #f9f9f9;
    padding: 15px;
    border-radius: 5px;
    margin-bottom: 20px;
}
.toc ul {
    list-style-type: none;
    padding-left: 20px;
}
.toc li {
    margin-bottom: 5px;
}
a {
    color: #1e88e5;
    text-decoration: none;
}
a:hover {
    text-decoration: underline;
}
"""

def ensure_docs_dir():
    """Ensure the documentation directory exists."""
    if not os.path.exists(DOCS_DIR):
        os.makedirs(DOCS_DIR)
    
    # Create css file
    with open(os.path.join(DOCS_DIR, "style.css"), "w") as f:
        f.write(CSS)

def get_modules():
    """Get all modules in the app package."""
    import app
    modules = []
    
    for finder, name, is_pkg in pkgutil.walk_packages(app.__path__, "app."):
        try:
            module = importlib.import_module(name)
            modules.append(module)
        except (ImportError, AttributeError) as e:
            print(f"Error importing {name}: {e}")
    
    return modules

def parse_docstring(docstring):
    """Parse a docstring into its components."""
    if not docstring:
        return {"description": "", "params": [], "returns": None}
    
    # Clean up docstring
    docstring = inspect.cleandoc(docstring)
    
    # Extract description
    parts = docstring.split("\n\n", 1)
    description = parts[0]
    
    # Parse parameters and return value
    params = []
    returns = None
    
    if len(parts) > 1:
        param_section = re.findall(r"Args:(.*?)(?:Returns:|$)", parts[1], re.DOTALL)
        if param_section:
            param_text = param_section[0].strip()
            param_items = re.findall(r"(\w+):(.*?)(?=\n\w+:|$)", param_text, re.DOTALL)
            for name, desc in param_items:
                params.append({"name": name.strip(), "description": desc.strip()})
        
        return_section = re.findall(r"Returns:(.*?)$", parts[1], re.DOTALL)
        if return_section:
            returns = return_section[0].strip()
    
    return {
        "description": description,
        "params": params,
        "returns": returns
    }

def document_function(function, level=3):
    """Generate documentation for a function."""
    heading = "#" * level
    doc = []
    
    # Function name and signature
    signature = str(inspect.signature(function))
    doc.append(f'{heading} `{function.__name__}{signature}`\n')
    
    # Parse docstring
    docstring_info = parse_docstring(function.__doc__)
    
    # Description
    if docstring_info["description"]:
        doc.append(docstring_info["description"] + "\n")
    
    # Parameters
    if docstring_info["params"]:
        doc.append("**Parameters:**\n")
        doc.append("| Name | Description |")
        doc.append("| ---- | ----------- |")
        for param in docstring_info["params"]:
            doc.append(f"| `{param['name']}` | {param['description']} |")
        doc.append("")
    
    # Return value
    if docstring_info["returns"]:
        doc.append("**Returns:**\n")
        doc.append(docstring_info["returns"] + "\n")
    
    return "\n".join(doc)

def document_class(cls, level=2):
    """Generate documentation for a class."""
    heading = "#" * level
    doc = []
    
    # Class name and bases
    bases = ", ".join([base.__name__ for base in cls.__bases__ if base.__name__ != "object"])
    if bases:
        doc.append(f'{heading} Class `{cls.__name__}` (extends {bases})\n')
    else:
        doc.append(f'{heading} Class `{cls.__name__}`\n')
    
    # Class docstring
    if cls.__doc__:
        doc.append(inspect.cleandoc(cls.__doc__) + "\n")
    
    # Document methods
    methods = inspect.getmembers(cls, predicate=inspect.isfunction)
    if methods:
        method_docs = []
        for name, method in methods:
            # Skip private methods
            if name.startswith("_") and name != "__init__":
                continue
            method_docs.append(document_function(method, level=level+1))
        
        if method_docs:
            doc.append(f'### Methods\n')
            doc.append("\n".join(method_docs))
    
    return "\n".join(doc)

def document_module(module, level=1):
    """Generate documentation for a module."""
    heading = "#" * level
    doc = []
    
    # Module name
    module_name = module.__name__
    doc.append(f'{heading} Module `{module_name}`\n')
    
    # Module docstring
    if module.__doc__:
        doc.append(inspect.cleandoc(module.__doc__) + "\n")
    
    # Document classes
    classes = inspect.getmembers(module, predicate=inspect.isclass)
    classes = [(name, cls) for name, cls in classes if cls.__module__ == module.__name__]
    
    if classes:
        doc.append("## Classes\n")
        class_docs = []
        for name, cls in classes:
            class_docs.append(document_class(cls, level=2))
        doc.append("\n".join(class_docs))
    
    # Document functions
    functions = inspect.getmembers(module, predicate=inspect.isfunction)
    functions = [(name, func) for name, func in functions if func.__module__ == module.__name__]
    
    if functions:
        doc.append("## Functions\n")
        function_docs = []
        for name, func in functions:
            # Skip private functions
            if name.startswith("_"):
                continue
            function_docs.append(document_function(func, level=3))
        doc.append("\n".join(function_docs))
    
    return "\n".join(doc)

def generate_module_docs():
    """Generate documentation for all modules."""
    modules = get_modules()
    
    # Create module index
    index = ["# Faculty Conference Travel System Documentation\n"]
    index.append("## Modules\n")
    
    for module in sorted(modules, key=lambda m: m.__name__):
        # Skip __init__ modules
        if module.__name__.endswith("__init__"):
            continue
        
        # Add to index
        module_name = module.__name__
        module_file = module_name.replace(".", "/") + ".md"
        index.append(f"- [{module_name}]({module_file})")
        
        # Generate module documentation
        doc = document_module(module)
        
        # Save to file
        module_path = os.path.join(DOCS_DIR, module_file)
        os.makedirs(os.path.dirname(module_path), exist_ok=True)
        
        with open(module_path, "w") as f:
            f.write(doc)
    
    # Write index
    with open(os.path.join(DOCS_DIR, "index.md"), "w") as f:
        f.write("\n".join(index))

def generate_html_docs():
    """Convert markdown documentation to HTML."""
    # Get all markdown files
    for root, dirs, files in os.walk(DOCS_DIR):
        for file in files:
            if file.endswith(".md"):
                md_path = os.path.join(root, file)
                html_path = md_path.replace(".md", ".html")
                
                # Read markdown
                with open(md_path, "r") as f:
                    md_content = f.read()
                
                # Convert to HTML
                html_content = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
                
                # Add header and CSS
                html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FTCS Documentation</title>
    <link rel="stylesheet" href="/style.css">
</head>
<body>
    <header>
        <h1>Faculty Conference Travel System</h1>
        <p><a href="/index.html">Back to Index</a></p>
    </header>
    {html_content}
    <footer>
        <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </footer>
</body>
</html>
"""
                # Write HTML
                with open(html_path, "w") as f:
                    f.write(html)

def main():
    """Main entry point for documentation generator."""
    ensure_docs_dir()
    generate_module_docs()
    generate_html_docs()
    print(f"Documentation generated in {DOCS_DIR}")

if __name__ == "__main__":
    main()
