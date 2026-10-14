import os
import re
from flask import Flask, render_template, request, send_file, jsonify
import markdown
from weasyprint import HTML

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

WIKILINK_RE = re.compile(r'(?<!!)\[\[(.*?)\]\]')
EMBED_RE = re.compile(r'!\[\[(.*?)\]\]')
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp')

# Obsidian Official Color Schemes for PDF Document Rendering
PDF_THEME_PALETTES = {
    'dark': {
        'bg': '#1e1e20',
        'text': '#dcddde',
        'title': '#ffffff',
        'accent': '#7f6df2',
        'border': '#38383e',
        'th_bg': '#2a2a2e',
        'tr_even_bg': '#252528',
        'code_bg': '#252529',
        'quote_bg': '#25252a',
        'muted': '#888888',
    },
    'light': {
        'bg': '#ffffff',
        'text': '#222222',
        'title': '#111111',
        'accent': '#6c31e8',
        'border': '#cccccc',
        'th_bg': '#f0f0f5',
        'tr_even_bg': '#fafafa',
        'code_bg': '#f6f8fa',
        'quote_bg': '#fcfbfe',
        'muted': '#777777',
    }
}

def sanitize_filename(filename):
    clean_path = filename.replace('\\', '/')
    return os.path.basename(clean_path)

def extract_links(markdown_content):
    return WIKILINK_RE.findall(markdown_content)

def resolve_embeds(content, processed_files=None):
    if processed_files is None:
        processed_files = set()

    def embed_replacement(match):
        target = match.group(1).split('|')[0].strip()
        
        if target.lower().endswith(IMAGE_EXTENSIONS):
            return f"![{target}]({target})"
            
        md_target = target if target.endswith('.md') else f"{target}.md"
        filepath = os.path.join(UPLOAD_FOLDER, md_target)
        
        if os.path.exists(filepath) and filepath not in processed_files:
            processed_files.add(filepath)
            with open(filepath, 'r', encoding='utf-8') as f:
                return resolve_embeds(f.read(), processed_files)
                
        return f"> *Missing embed: {target}*"

    return EMBED_RE.sub(embed_replacement, content)

def analyze_table_columns(markdown_content):
    max_cols = 0
    for line in markdown_content.splitlines():
        if '|' in line:
            cols = [c.strip() for c in line.split('|') if c.strip()]
            if len(cols) > max_cols:
                max_cols = len(cols)
    return max_cols

def process_markdown_files(md_files):
    all_md_titles = {filename.replace('.md', ''): filename for filename in md_files}
    
    node_map = {}
    nodes = []
    edges = []

    def get_or_create_node(title):
        if title not in node_map:
            node_id = len(node_map) + 1
            node_map[title] = node_id
            
            is_missing = title not in all_md_titles
            nodes.append({
                "id": node_id, 
                "label": title, 
                "is_missing": is_missing
            })
        return node_map[title]

    for filename in md_files:
        title = filename.replace('.md', '')
        source_id = get_or_create_node(title)
        
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                links = extract_links(f.read())
                
            for link in links:
                target = link.split('|')[0].strip()
                if target:
                    target_id = get_or_create_node(target)
                    edges.append({"from": source_id, "to": target_id})
                    
    return {"nodes": nodes, "edges": edges}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    files = request.files.getlist('files')
    md_files = []
    
    for f in files:
        if not f.filename:
            continue
            
        if '/.' in f.filename.replace('\\', '/') or f.filename.startswith('.'):
            continue

        base_filename = sanitize_filename(f.filename)
        filepath = os.path.join(UPLOAD_FOLDER, base_filename)
        f.save(filepath)
        
        if base_filename.lower().endswith('.md'):
            md_files.append(base_filename)
            
    graph_data = process_markdown_files(md_files)
    return jsonify({"graph": graph_data, "files": md_files})

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    data = request.json
    ordered_files = data.get('ordered_files', [])
    graph_image = data.get('graph_image', None)
    theme_key = data.get('theme', 'dark')
    
    palette = PDF_THEME_PALETTES.get(theme_key, PDF_THEME_PALETTES['dark'])
    
    title_to_id = {}
    for idx, filename in enumerate(ordered_files):
        title = filename.replace('.md', '')
        title_to_id[title] = f"note-{idx+1}"

    # 1. Graph View Page
    combined_body = ""
    if graph_image:
        combined_body += f"""
        <div class="page-section">
            <h1 class="doc-title">Vault Graph View</h1>
            <div class="graph-container">
                <img src="{graph_image}" class="graph-img"/>
            </div>
        </div>
        <div class="page-break"></div>
        """

    # 2. Table of Contents
    combined_body += """
    <div class="page-section">
        <h1 class="doc-title">Table of Contents</h1>
        <ul class="toc-list">
    """
    for idx, filename in enumerate(ordered_files):
        title = filename.replace('.md', '')
        note_id = f"note-{idx+1}"
        combined_body += f'<li><a href="#{note_id}">{title}</a></li>\n'
        
    combined_body += """
        </ul>
    </div>
    <div class="page-break"></div>
    """

    # 3. Note Contents
    for idx, filename in enumerate(ordered_files):
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(filepath):
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        col_count = analyze_table_columns(content)
        
        if col_count >= 7:
            section_class = "page-section landscape-page ultra-wide"
        elif col_count >= 4:
            section_class = "page-section landscape-page wide"
        else:
            section_class = "page-section"

        content = resolve_embeds(content)

        def wikilink_sub(match):
            raw = match.group(1)
            parts = raw.split('|')
            target = parts[0].strip()
            alias = parts[1].strip() if len(parts) > 1 else target
            
            if target in title_to_id:
                return f"[{alias}](#{title_to_id[target]})"
            return alias

        content = WIKILINK_RE.sub(wikilink_sub, content)

        html_note = markdown.markdown(
            content,
            extensions=['tables', 'fenced_code', 'sane_lists', 'attr_list', 'def_list']
        )

        title = filename.replace('.md', '')
        note_id = f"note-{idx+1}"

        combined_body += f"""
        <div class="{section_class}" id="{note_id}">
            <h1 class="note-title">{title}</h1>
            {html_note}
        </div>
        <div class="page-break"></div>
        """

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                size: A4 portrait;
                margin: 1.8cm 1.5cm;
                background-color: {palette['bg']};
                @bottom-right {{
                    content: "Page " counter(page);
                    font-family: sans-serif;
                    font-size: 8pt;
                    color: {palette['muted']};
                }}
            }}

            @page landscape-mode {{
                size: A4 landscape;
                margin: 0.8cm 0.8cm;
                background-color: {palette['bg']};
                @bottom-right {{
                    content: "Page " counter(page);
                    font-family: sans-serif;
                    font-size: 8pt;
                    color: {palette['muted']};
                }}
            }}

            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                font-size: 9.5pt;
                line-height: 1.5;
                background-color: {palette['bg']};
                color: {palette['text']};
            }}

            .page-break {{ page-break-after: always; }}

            .landscape-page {{
                page: landscape-mode;
            }}

            h1, h2, h3, h4, h5, h6 {{
                color: {palette['title']};
            }}

            .doc-title {{
                font-size: 20pt;
                border-bottom: 2px solid {palette['accent']};
                padding-bottom: 6px;
                margin-bottom: 18px;
                color: {palette['title']};
            }}

            .note-title {{
                font-size: 16pt;
                border-bottom: 1px solid {palette['border']};
                padding-bottom: 4px;
                margin-top: 0;
                margin-bottom: 12px;
                color: {palette['title']};
            }}

            .graph-container {{
                background-color: {palette['bg']};
                padding: 10px;
                border-radius: 8px;
                border: 1px solid {palette['border']};
            }}

            .graph-img {{
                width: 100%;
                max-height: 20cm;
                object-fit: contain;
                display: block;
            }}

            .toc-list {{
                list-style: none;
                padding: 0;
                margin: 0;
            }}

            .toc-list li {{
                margin-bottom: 8px;
                font-size: 9.5pt;
            }}

            .toc-list a {{
                text-decoration: none;
                color: {palette['text']};
                display: block;
            }}

            .toc-list a::after {{
                content: leader('. ') target-counter(attr(href), page);
                float: right;
                color: {palette['accent']};
                font-weight: bold;
            }}

            table {{
                width: 100% !important;
                border-collapse: collapse;
                margin: 14px 0;
                table-layout: fixed;
            }}

            th, td {{
                border: 1px solid {palette['border']};
                padding: 6px 7px;
                text-align: left;
                vertical-align: top;
                word-wrap: break-word;
                overflow-wrap: anywhere;
                word-break: break-word;
                hyphens: auto;
                color: {palette['text']};
            }}

            th {{
                background-color: {palette['th_bg']};
                font-weight: bold;
                color: {palette['title']};
            }}

            tr:nth-child(even) {{
                background-color: {palette['tr_even_bg']};
            }}

            tr {{
                page-break-inside: avoid;
            }}

            .landscape-page.wide table {{
                font-size: 6.5pt;
                line-height: 1.25;
            }}
            .landscape-page.wide th, 
            .landscape-page.wide td {{
                padding: 4px 5px;
            }}

            .landscape-page.ultra-wide table {{
                font-size: 5.5pt;
                line-height: 1.15;
            }}
            .landscape-page.ultra-wide th, 
            .landscape-page.ultra-wide td {{
                padding: 2px 3px;
            }}

            img {{
                max-width: 100%;
                height: auto;
                display: block;
                margin: 12px auto;
            }}

            pre, code {{
                background-color: {palette['code_bg']};
                color: {palette['text']};
            }}

            pre {{
                padding: 10px;
                border-radius: 4px;
                font-size: 8pt;
                white-space: pre-wrap;
                word-wrap: break-word;
                border: 1px solid {palette['border']};
            }}

            blockquote {{
                border-left: 3px solid {palette['accent']};
                margin: 10px 0;
                padding: 4px 12px;
                color: {palette['text']};
                background-color: {palette['quote_bg']};
            }}

            a {{
                color: {palette['accent']};
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        {combined_body}
    </body>
    </html>
    """
    
    pdf_path = os.path.join(UPLOAD_FOLDER, 'output.pdf')
    HTML(string=full_html, base_url=os.path.abspath(UPLOAD_FOLDER)).write_pdf(pdf_path)
    
    return jsonify({"status": "success", "download_url": "/download/output.pdf"})

@app.route('/download/<filename>')
def download(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5000)