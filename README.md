# Obsidian-Stitch

Live App: <https://vizkidd.github.io/obsidian-stitch>

Obsidian-Stitch Vault Stitcher is a client-side web application designed to compile, organize, and stitch an entire Obsidian Markdown vault—or selected folders and clusters—into a single PDF document. It includes an interactive graph view, automatic link resolution, embedded media processing, callouts, and invisible text overlay layers for PDF searchability.The application operates entirely inside the browser using Pyodide (Python WebAssembly). No vault files, images, or documents are ever uploaded to an external server.

## Key Features

- 100% Local & Private Processing: Powered by Python's markdown library running locally in the browser via Pyodide WASM.
- Interactive Graph Network View: Visualizes note connections and reference topology in real time using vis-network.
- Flexible Grouping & Sorting:Grouping Modes: Keep vault folder hierarchies intact or automatically group notes by graph topological clusters.
- Sorting Criteria: Order notes by Name (A-Z), Most Referred (incoming link count), Node Size, Edge Count, Occupancy (edge density), or Degrees of Freedom (independent cycles).
- Full Obsidian Syntax Support:Wikilinks & Embeds: Resolves [[Note Name]], section headers [[Note#Heading]], and alias labels [[Note\|Alias]].
- Nested Note Embeds: Parses ![[Embedded Note]] recursively (with cyclic loop prevention up to depth 6).
- Embedded Media: Renders images (.png, .jpg, .jpeg, .gif, .svg, .webp) and rasterizes embedded .pdf files using PDF.js.
- Obsidian Callouts: Formats callouts ([!tip], [!warning], [!danger], [!quote], etc.) with themed container styling.
- Task Lists & Highlights: Renders checkboxes [x], [-], highlights ==text==, strikethroughs ~~text~~, and #tags.
- Intelligent PDF Engine:Smart Table Layouts: Automatically switches note pages to landscape orientation when wide or ultra-wide markdown tables are detected.
- Searchable Text Layer: Extracts character bounding boxes from DOM nodes to inject an invisible text layer over the PDF canvas, enabling full text selection, copying, and Ctrl+F searchability.
- Interactive Internal Links: Internal [[wikilinks]] translate into functional, clickable page-to-page links inside the PDF.
- PDF Outline & Bookmarks: Automatically builds hierarchical bookmarks (Group \> Note) in the PDF reader's sidebar.
- Graph Cover Page: Generates an A4 visual overview page featuring the graph topology at the start of the exported PDF.
- Theme Options: Supports Obsidian Dark and Obsidian Light themes.

## Application Architecture

``` {style="color: gray"}
[ Obsidian Vault Directory ]
            │
            ▼
 ┌────────────────────────────────────────┐
 │ Browser File System Access / Drag-Drop │
 └──────────────────┬─────────────────────┘
                    │
                    ▼
 ┌────────────────────────────────────────┐
 │ Pyodide WebAssembly (Python Engine)    │
 │ - Parses Frontmatter & Metadata        │
 │ - Resolves Wikilinks & Embed Tree      │
 │ - Builds Graph Nodes & Topological Map │
 │ - Converts Markdown to HTML DOM        │
 └──────────────────┬─────────────────────┘
                    │
         ┌──────────┴──────────┐
         ▼                     ▼
┌──────────────────┐  ┌──────────────────┐
│ Vis Network Graph│  │ Offscreen Stage  │
│ (Visualizing)    │  │ (DOM Rendering)  │
└──────────────────┘  └────────┬─────────┘
                               │
                               ▼
                      ┌──────────────────┐
                      │ PDF Assembly     │
                      │ - html2canvas    │
                      │ - jsPDF Engine   │
                      │ - PDF.js Raster  │
                      │ - Text Layer BBox│
                      └────────┬─────────┘
                               │
                               ▼
                     [ stitched-vault.pdf ]
```

## How it Works

1.  File Ingestion & Indexing When a directory or set of files is selected, the application scans .md notes, PDF documents, and image assets. It strips root folder prefixes while retaining relative directory paths. Frontmatter tags are extracted via regex, and note-to-note references are indexed into a lookup table.

2.  Graph Network Construction The Python runtime processes all incoming link targets ([[link]] and ![[embed]]) to form a directed graph:

Resolved Targets: Mapped directly to vault node IDs.

Missing References: Identified as unresolved nodes with distinct border styling.

Graph Metrics: Computes cluster sizes, total edges, reference frequencies, graph occupancy, and degrees of freedom.

3.  Note Ordering & Drag-and-Drop Management Notes are organized into interactive groups rendered in the UI using SortableJS:

You can drag notes between groups or drag entire group containers to reorder the output.

Unwanted notes or groups can be removed prior to export or restored from the trash buffer.

4.  DOM Stage Rendering & PDF Compilation During PDF generation:

The app renders note HTML inside an offscreen viewport stage (#pdf-render-stage).

Embedded PDFs are rasterized into high-resolution JPEG canvases via PDF.js worker processes.

html2canvas captures the rendered HTML pages at 2x pixel ratio.

extractTextItems() walks the DOM tree to measure relative bounding box coordinates for every rendered word, creating matching invisible text overlay instructions in jsPDF.

Clickable hotspots are added for both external web links and internal jump targets.

## Grouping & Sorting Options

| Option | Description |
|--------------------------|----------------------------------------------|
| Folders Grouping | Retains directory paths as distinct document sections |
| Graph Clusters Grouping | Groups connected components in the link network together into clusters |
| Name (A-Z) | Sorts notes alphabetically by title |
| Most Referred | Sorts notes by incoming link density (most backlinked notes first) |
| Size / Edges / Occupancy | "Orders graph groups by node count, edge density, or structural complexity" |
| Degrees of Freedom | Orders groups by independent cycles in the subgraph (E−V+C) |
| Compact Mode | Eliminates excess whitespace and combines note flows into continuous pages |
| Landscape Pages | Automatically rotates notes containing wide tables onto landscape pages |

## Supported Obsidian Syntax

- Wikilinks: [[Note Name]], [[Note Name\|Custom Label]]
- Section Linking: [[Note Name#Section Title]]
- Embeds: ![[Note Name]], ![[Image.png]], ![[Document.pdf#page=2]]
- Callouts:

```         
> [!info] Note Title
> Content goes here.
```

(Supports tip, success, warning, caution, danger, error, quote, etc.)

- Task Lists: - [ ] Pending item or - [x] Completed item \* Formatting: ==Highlights==, ~~Strikethrough~~, #tags

## Tech Stack & External Libraries

| Component | Library / Framework | Purpose |
|-------------------|----------------------------------|-------------------|
| WASM Runtime | Pyodide v0.25.0 | Executes Python scripts client-side inside WebAssembly |
| Markdown Processing | Python-Markdown | Extensible Python markdown engine running in WASM |
| Graph Visualization | vis-network v9.1.2 | Renders dynamic graph network nodes and edge connections |
| Canvas Capturing | html2canvas v1.4.1 | Converts rendered DOM nodes into image canvases |
| PDF Generation | jsPDF v2.5.1 | "Assembles image canvases, link vectors, text layers, and outlines into a PDF" |
| PDF Rasterization | PDF.js v3.11.174 | Renders embedded .pdf assets into JPEGs for inline inclusion |
| UI Drag and Drop | SortableJS v1.15.0 | Enables reordering of notes and group containers |

## Local Development

Because the application relies on WebAssembly (Pyodide) and Web Workers (PDF.js), it must be served over an HTTP server rather than opened via the <file://> protocol.

1.  Clone the repository

```         
git clone https://github.com/vizkidd/obsidian-stitch.git
cd obsidian-stitch
```

2.  Start a local WASM development server You can start a local server using Python, Node, or any standard static web server:

```         
python build_wasm.py
```

From R

```         
httpuv::runStaticServer("./dist")
```

Note: [app.py](app.py) contains an older non-WASM build that is essentially a developmental artifact
