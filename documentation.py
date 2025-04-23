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
        