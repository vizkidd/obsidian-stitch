# Obsidian-Stitch

🌐 Obsidian Vault Stitcher & PDF Exporter (WASM) A high-performance, 100% client-side Web Application that parses an entire Obsidian vault, visualizes its inter-note graph, allows custom page sequencing, and exports a unified, beautifully styled PDF document complete with interactive links, authentic Obsidian typography, smart table auto-scaling, and vault transclusions.

Powered by Pyodide (WebAssembly), all Markdown processing, graph extraction, and frontmatter parsing run directly inside your web browser—no servers, no APIs, and total privacy for your vault data.

✨ Features 🔒 100% Client-Side & Private: Powered by Pyodide (Python in WebAssembly). Your markdown files, images, and notes never leave your machine.

🕸️ Vault Graph View:

Automatically parses internal wikilinks ([[Note]]) to construct a dynamic, physics-simulated network graph using vis-network.

Exported to Page 1 of the PDF in a strict 1:1 aspect ratio (no oval distortion or stretched text).

🎨 Obsidian Dark & Light Themes: Complete color scheme matching Obsidian's native dark and light modes.

📄 Drag-and-Drop Sequence Builder: Re-order document pages easily before exporting using SortableJS.

🔗 Dual-Type Interactive PDF Hyperlinks:

Internal Wikilinks: Clickable links inside the generated PDF jump directly to the target note page.

External Web Links: Converts URLs (<https://>...) into clickable web links inside the PDF.

🏷️ Frontmatter & Tag Badges: Automatically extracts YAML metadata (e.g., tags: [...]) and renders them as #tag pills styled with JetBrains Mono.

🖼️ Image Embeds & Note Transclusions: Supports image embeds (![[image.png]]) and inline note transclusions (![[Embedded Note]]).

📊 Smart Auto-Scaling Tables: Dynamically analyzes table column counts to adjust font size and cell padding (wide-table / ultra-wide-table), preventing text cutoff or vertical character squishing.

🚫 Zero Canvas Glitches: Slices continuous multi-page documents with background canvas tiling, eliminating blank trailing white boxes and underline clipping on font descenders.
