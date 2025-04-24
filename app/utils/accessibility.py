"""
Accessibility module.
Provides utilities for improving application accessibility.
"""

import streamlit as st
import logging
import re
from bs4 import BeautifulSoup

def add_accessibility_features():
    """Add accessibility enhancements to the Streamlit UI."""
    # Add accessibility CSS
    st.markdown("""
    <style>
    /* Improve contrast */
    .stTextInput input, .stSelectbox select, .stMultiselect div[data-baseweb="select"] {
        background-color: #ffffff !important;
        color: #111111 !important;
    }
    
    /* Increase button contrast */
    button[kind="primary"] {
        background-color: #0366d6 !important;
        color: white !important;
    }
    
    /* Focus indicators */
    button:focus, input:focus, select:focus, textarea:focus, 
    div[data-baseweb="select"]:focus-within {
        outline: 3px solid #ffab00 !important;
        outline-offset: 2px !important;
    }
    
    /* Ensure adequate text size */
    .stMarkdown p, .stMarkdown li {
        font-size: 1rem !important;
        line-height: 1.5 !important;
    }
    
    /* Improve form labels */
    label, div[data-testid="stWidgetLabel"] {
        font-weight: 600 !important;
        margin-bottom: 4px !important;
    }
    
    /* Add more spacing between elements */
    div[data-testid="column"] > div {
        margin-bottom: 1rem !important;
    }
    
    /* Make error messages more accessible */
    div.stAlert {
        padding: 1rem !important;
        border-radius: 0.5rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

def check_color_contrast(foreground, background):
    """
    Calculate color contrast ratio to ensure WCAG compliance.
    
    Args:
        foreground: Foreground color in hex format (#RRGGBB)
        background: Background color in hex format (#RRGGBB)
        
    Returns:
        tuple: (ratio, passes_AA, passes_AAA)
    """
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def get_luminance(rgb):
        r, g, b = [c/255.0 for c in rgb]
        r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
        g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
        b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    
    # Convert to RGB
    fg_rgb = hex_to_rgb(foreground)
    bg_rgb = hex_to_rgb(background)
    
    # Calculate luminance
    fg_luminance = get_luminance(fg_rgb)
    bg_luminance = get_luminance(bg_rgb)
    
    # Calculate contrast ratio
    ratio = (max(fg_luminance, bg_luminance) + 0.05) / (min(fg_luminance, bg_luminance) + 0.05)
    
    # Check against WCAG 2.1 standards
    passes_aa = ratio >= 4.5  # Standard text
    passes_aaa = ratio >= 7.0  # Enhanced standard
    
    return ratio, passes_aa, passes_aaa

def make_markdown_accessible(markdown_text):
    """
    Improve accessibility of markdown content.
    
    Args:
        markdown_text: Original markdown text
        
    Returns:
        str: Improved markdown text
    """
    # Ensure headings have proper hierarchy
    lines = markdown_text.split('\n')
    in_code_block = False
    min_heading_level = 6  # Track minimum heading level used
    
    # First pass - find minimum heading level
    for i, line in enumerate(lines):
        # Skip code blocks
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            continue
            
        if in_code_block:
            continue
            
        # Check for headings
        if line.strip().startswith('#'):
            level = 0
            for char in line:
                if char == '#':
                    level += 1
                else:
                    break
                    
            if level < min_heading_level:
                min_heading_level = level
    
    # Second pass - adjust heading hierarchy if needed
    if min_heading_level > 1:
        # We need to adjust all headings
        adjustment = min_heading_level - 1
        
        in_code_block = False
        for i, line in enumerate(lines):
            # Skip code blocks
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                continue
                
            if in_code_block:
                continue
                
            # Adjust headings
            if line.strip().startswith('#'):
                level = 0
                for j, char in enumerate(line):
                    if char == '#':
                        level += 1
                    else:
                        break
                        
                # Create new heading with adjusted level
                new_level = max(1, level - adjustment)
                lines[i] = '#' * new_level + line[level:]
    
    # Add alt text to images
    in_code_block = False
    for i, line in enumerate(lines):
        # Skip code blocks
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            continue
            
        if in_code_block:
            continue
            
        # Check for images without alt text
        if '![' in line:
            images = re.findall(r'!\[(.*?)\]\((.*?)\)', line)
            for alt_text, url in images:
                if not alt_text:
                    # Auto-generate basic alt text from URL
                    file_name = url.split('/')[-1].split('.')[0].replace('-', ' ').replace('_', ' ')
                    new_img_tag = f'![Image: {file_name}]({url})'
                    line = line.replace(f'![]({url})', new_img_tag)
            lines[i] = line
    
    return '\n'.join(lines)

def run_accessibility_checks(html_content):
    """
    Perform basic accessibility checks on HTML content.
    
    Args:
        html_content: HTML string to check
        
    Returns:
        dict: Accessibility issues found
    """
    issues = {
        "critical": [],
        "warnings": [],
        "info": []
    }
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Check for images without alt text
        images = soup.find_all('img')
        for img in images:
            if not img.get('alt'):
                issues["critical"].append(f"Image missing alt text: {img.get('src', 'unknown')}")
                
        # Check for heading hierarchy
        headings = []
        for i in range(1, 7):
            headings.extend([(i, h) for h in soup.find_all(f'h{i}')])
            
        headings.sort(key=lambda x: x[1].sourceline)  # Sort by source line number
        
        prev_level = 0
        for level, heading in headings:
            if level > prev_level + 1 and prev_level > 0:
                issues["warnings"].append(f"Heading hierarchy skipped from h{prev_level} to h{level}")
            prev_level = level
            
            # Check for empty headings
            if not heading.get_text().strip():
                issues["critical"].append(f"Empty heading: h{level}")
                
        # Check for links
        links = soup.find_all('a')
        for link in links:
            # Check for empty links
            if not link.get_text().strip() and not link.find_all('img'):
                issues["critical"].append(f"Empty link: {link.get('href', 'unknown')}")
                
            # Check for generic link text
            text = link.get_text().strip().lower()
            if text in ['click here', 'here', 'link', 'more']:
                issues["warnings"].append(f"Generic link text: '{text}' for {link.get('href', 'unknown')}")
                
        # Check for form labels
        inputs = soup.find_all(['input', 'select', 'textarea'])
        for input_el in inputs:
            input_id = input_el.get('id')
            if input_id:
                label = soup.find('label', attrs={'for': input_id})
                if not label:
                    issues["critical"].append(f"Missing label for input: {input_id}")
            elif input_el.get('type') != 'hidden':
                issues["warnings"].append("Input without ID may be inaccessible")
                
        # Check for color contrast (simplified)
        elements_with_color = soup.find_all(style=re.compile(r'color:|background-color:'))
        for element in elements_with_color:
            issues["info"].append(f"Element with custom colors should be checked for contrast: {element.name}")
            
    except Exception as e:
        logging.error(f"Error running accessibility checks: {str(e)}")
        issues["critical"].append(f"Error running accessibility checks: {str(e)}")
        
    return issues

def show_accessibility_dashboard():
    """Show admin interface for accessibility testing."""
    st.subheader("Accessibility Testing")
    
    # Check current page
    st.info("This tool performs basic accessibility checks on your Streamlit app.")
    
    # Test color contrast
    st.subheader("Color Contrast Checker")
    
    col1, col2 = st.columns(2)
    with col1:
        foreground = st.color_picker("Foreground Color", "#000000")
    with col2:
        background = st.color_picker("Background Color", "#FFFFFF")
        
    ratio, passes_aa, passes_aaa = check_color_contrast(foreground, background)
    
    st.write(f"Contrast Ratio: {ratio:.2f}:1")
    
    if passes_aaa:
        st.success("✅ Passes WCAG AAA (Enhanced)")
    elif passes_aa:
        st.warning("✅ Passes WCAG AA (Minimum)")
    else:
        st.error("❌ Fails WCAG Contrast Requirements")
        
    # Sample text display
    st.markdown(
        f"""
        <div style="padding: 20px; background-color: {background}; color: {foreground}; border-radius: 5px;">
            <h3 style="color: {foreground};">Sample Heading</h3>
            <p style="color: {foreground};">This is sample text with the selected colors. Can you read this easily?</p>
            <a href="#" style="color: {foreground};">Sample Link</a>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Markdown accessibility checker
    st.subheader("Markdown Accessibility Checker")
    
    sample_markdown = st.text_area(
        "Enter Markdown to check",
        """### Sample Heading
        
This is a paragraph with a [link](https://example.com).

![]

1. List item one
2. List item two

#### Another heading
        """
    )
    
    if st.button("Check Markdown"):
        improved_markdown = make_markdown_accessible(sample_markdown)
        
        if improved_markdown != sample_markdown:
            st.success("Markdown has been improved for accessibility")
            st.subheader("Improved Markdown")
            st.code(improved_markdown)
            st.subheader("Preview")
            st.markdown(improved_markdown)
        else:
            st.success("No accessibility issues found in markdown")
    
    # HTML accessibility checker
    st.subheader("HTML Accessibility Checker")
    
    sample_html = st.text_area(
        "Enter HTML to check",
        """<div>
  <h1>Main Heading</h1>
  <p>This is a paragraph with a <a href="https://example.com">link</a>.</p>
  <img src="image.jpg">
  <h3>Skipped heading level</h3>
  <form>
    <input type="text">
    <button>Submit</button>
  </form>
</div>"""
    )
    
    if st.button("Check HTML"):
        issues = run_accessibility_checks(sample_html)
        
        if not any(issues.values()):
            st.success("No accessibility issues found")
        else:
            if issues["critical"]:
                st.error(f"Critical Issues: {len(issues['critical'])}")
                for issue in issues["critical"]:
                    st.write(f"❌ {issue}")
                    
            if issues["warnings"]:
                st.warning(f"Warnings: {len(issues['warnings'])}")
                for issue in issues["warnings"]:
                    st.write(f"⚠️ {issue}")
                    
            if issues["info"]:
                st.info(f"Information: {len(issues['info'])}")
                for issue in issues["info"]:
                    st.write(f"ℹ️ {issue}")
    
    # Accessibility resources
    st.subheader("Accessibility Resources")
    
    st.markdown("""
    - [WCAG 2.1 Guidelines](https://www.w3.org/TR/WCAG21/)
    - [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
    - [A11Y Project Checklist](https://www.a11yproject.com/checklist/)
    - [Streamlit Accessibility Tips](https://discuss.streamlit.io/t/accessibility-of-streamlit-apps/4517)
    """)