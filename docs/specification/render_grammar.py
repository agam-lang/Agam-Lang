import sys
import re
from pathlib import Path

def generate_html(ebnf_content):
    # Basic highlighting and formatting
    # We will replace non-terminals with bold blue, and strings with green.
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agam Language Grammar Specification</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 900px; margin: 0 auto; padding: 2rem; }
        h1 { border-bottom: 2px solid #eaecef; padding-bottom: 0.3em; }
        .grammar-block { background: #f6f8fa; border-radius: 6px; padding: 16px; overflow-x: auto; font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace; font-size: 14px; }
        .rule-name { color: #005cc5; font-weight: bold; }
        .string-literal { color: #22863a; }
        .operator { color: #d73a49; }
        .terminal { color: #6f42c1; font-weight: bold; }
        .comment { color: #6a737d; font-style: italic; }
    </style>
</head>
<body>
    <h1>Agam Language Formal Grammar</h1>
    <p>This document specifies the formal EBNF grammar for the Agam programming language. This grammar handles both base (indentation-sensitive) and advance (brace-delimited) syntax modes.</p>
    
    <h2>EBNF Reference</h2>
    <div class="grammar-block">
"""
    
    lines = ebnf_content.split('\n')
    for line in lines:
        if not line.strip():
            html += "<br>\n"
            continue
            
        # Highlight comments
        if line.strip().startswith('//'):
            html += f'<span class="comment">{line}</span><br>\n'
            continue
            
        # Highlight rules
        match = re.match(r'^(\??[a-z_]+)\s*:', line)
        if match:
            rule_name = match.group(1)
            line = line.replace(rule_name + ':', f'<span class="rule-name" id="{rule_name}">{rule_name}</span><span class="operator">:</span>', 1)
        
        # Highlight terminals definition
        match = re.match(r'^([A-Z_]+(\.[0-9]+)?)\s*:', line)
        if match:
            term_name = match.group(1)
            line = line.replace(term_name + ':', f'<span class="terminal" id="{term_name}">{term_name}</span><span class="operator">:</span>', 1)

        # Highlight strings
        line = re.sub(r'("[^"]*")', r'<span class="string-literal">\1</span>', line)
        line = re.sub(r"('[^']*')", r'<span class="string-literal">\1</span>', line)
        
        # Format operators
        line = re.sub(r'([|?*+])', r'<span class="operator">\1</span>', line)
        
        # Use non-breaking spaces for indentation in HTML
        indent = len(line) - len(line.lstrip(' '))
        line = ("&nbsp;" * indent) + line.lstrip(' ')
        
        html += line + "<br>\n"
        
    html += """
    </div>
</body>
</html>
"""
    return html

def main():
    ebnf_path = Path("docs/specification/grammar.ebnf")
    html_path = Path("docs/specification/grammar.html")
    
    if not ebnf_path.exists():
        print(f"Error: {ebnf_path} not found.")
        sys.exit(1)
        
    with open(ebnf_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    html = generate_html(content)
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
        
    print(f"Successfully generated {html_path}")

if __name__ == "__main__":
    main()
