# Monitoring Program Renewal Review

Interactive weekly design review for the Monitoring Program Renewal flows (Schedule and Renew, Renew Program).

- `index.html` is the whole page. Open it in a browser, or serve the folder with GitHub Pages.
- `img/` holds the 40 screen renders exported from Figma (webp, node id in the file name).
- `src/figma.json` is the structure read from the Figma file: sections, sub-flow labels, screens with positions, and the Design Insight notes.
- `src/build.py` turns `figma.json` into `index.html`. Hotspot positions live at the top of that file. Run `python3 src/build.py` from `src/` after editing, then wrap the output as `index.html` (see the header in `index.html`).

Comments posted on the page and dismissals are stored in the viewer's browser only.
