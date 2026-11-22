# Q - Peek

A small review page for design work. One `index.html` (plain HTML, CSS and JavaScript: no build step, no dependencies, no external requests) is driven by a `review.config.json` that a designer fills in. **A new project is a new config.**

Reviewers click through the design, read what changed in each update, and leave comments, either on the whole design or pinned to a spot.

## Run it

Serve the folder (the browser needs HTTP to load the config):

```bash
python3 -m http.server 8000
```

Open <http://localhost:8000/>. Any static host works the same way (GitHub Pages, Netlify, an intranet folder).

**Opened straight from disk (`file://`)?** Browsers block loading the config, so the page shows a **Choose the config file** button. Pick `review.config.json` and it runs from that file. Image and code paths are then read relative to `index.html`, so keep the config in the same folder as the page.

## Share links

| Link | Effect |
| --- | --- |
| `index.html` | Designer view, `review.config.json` |
| `index.html?role=stakeholder` | Starts in Stakeholder view |
| `index.html?role=designer` | Starts in Designer view |
| `index.html?config=other.json` | Loads another config. Image and code paths are relative to *that* file. Must be on the same site. |

`role` only chooses the starting view. It is a view, not a permission: anyone can flip the switch.

## Config reference (`review.config.json`)

The file may contain `// line` and `/* block */` notes and trailing commas. They are stripped before parsing, keeping character positions, so a syntax error is reported at the right line and column.

```jsonc
{
  "project": { "name": "…", "description": "…" },
  "team": [ { "name": "Maya Chen", "role": "UX" }, { "name": "Priya Nair", "role": "Stakeholder" } ],
  "design": { "type": "screens" | "figma" | "code", … },
  "updates": [ { "date": "YYYY-MM-DD", "changes": [ … ], "comments": { "ux": [ … ], "stakeholder": [ … ] } } ]
}
```

- **project**: `name` (also the localStorage key) and `description`.
- **team**: shown in the header and offered as name suggestions in the comment form. Designers are offered the UX names, stakeholders the Stakeholder names.
- **updates**: newest first. Each has a `date`, a list of `changes` (`{ text, screen? }`; a `screen` id makes the change link to that screen) and `comments` split into `ux` and `stakeholder`.

### `design.type: "screens"`

Exported images as a click-through prototype.

```jsonc
"design": { "type": "screens", "flows": [
  { "name": "Sign in", "screens": [
    { "id": "welcome", "name": "Welcome", "image": "example/screens/welcome.svg", "width": 390, "height": 844,
      "hotspots": [ { "x": 32, "y": 700, "width": 326, "height": 52, "target": "sign-in", "label": "Sign in" } ] }
  ] }
] }
```

- `image` is relative to the config file. `width` and `height` are the image's pixel size. A screen is never shown wider than `width`, and everything scales down with it.
- Hotspots are in **image pixels** from the top left. `target` is a screen `id`; `label` is optional (tooltip and screen-reader name).
- Hotspots are invisible until hovered. Clicking elsewhere on the screen flashes them all for a moment.
- "Step n of total" counts across all flows in the order they are listed.

### `design.type: "figma"`

```jsonc
"design": { "type": "figma", "url": "https://www.figma.com/design/FILE_KEY/Name?node-id=0-1" }
```

Paste a normal share link. It is rewritten to `https://embed.figma.com/…` with `embed-host=design-review`. The review layer itself never links out to Figma.

### `design.type: "code"`

```jsonc
"design": { "type": "code", "path": "example/prototype.html" }
```

A local HTML page, relative to the config, shown in an iframe. It must be on the same site as the review page.

To try another type, uncomment the `figma` or `code` line in the shipped config. If a key appears twice the last one wins, so the `screens` block can stay.

### Top bar

Project name, **Update** dropdown (the version history: newest is "Last update: …"), **What changed**, then the preview-size controls, then the **Designer / Stakeholder** switch and **Comments** (with a count).

Preview size, modelled on a design tool's toolbar:

- **Device**: Auto, Phone (402×874), Tablet (834×1194), Desktop (1440×900); editing a number shows Custom. **⇄** swaps width and height.
- **Fit**: on = scale down to the available space; off = actual size (the design area scrolls sideways inside its own box). The percentage is the current scale.
- `screens`: the width caps how wide the screen is shown. A screen is never shown wider than its own `width`, and its height follows the image, so the height field and ⇄ are disabled.
- `figma` / `code`: the frame becomes exactly width × height and is scaled to fit. Pins are percent of the frame, so they stay in place.
- Hidden on phones (the phone is the device). Not remembered between visits.

## Comments

```jsonc
{ "id": "u1-ux-1", "author": "Maya Chen", "role": "UX", "date": "2026-11-19",
  "text": "…", "category": "Accessibility", "status": "open",
  "screen": "sign-in", "x": 50, "y": 43,      // optional pin: x/y are percent from the top left
  "resolvedIn": "2026-11-20",                   // optional, shown for resolved comments
  "dismissed": false }                          // optional
```

- `category`: Accessibility, Design system, Content, Flow or General.
- `status`: `open`, `progress` or `resolved`.
- `screen` (screens type only) says where the pin lives. For `figma` and `code`, `x`/`y` are positions on the frame.
- `id` must be unique.

### Config check

If something does not add up (unknown screen id, missing size, duplicate id, a missing image, …) the page still loads and lists what to look at under the header, **in Designer view only**. A config that cannot be parsed gets an error screen with the line and column.

## Comments

Open them with the speech-bubble icon. The panel takes width from the design (full screen on phones).

- Tabs: **Insight from UX** and **Stakeholder feedback**, with counts; ←/→ move between tabs. Category chips filter the list and the markers.
- Numbered markers appear on the design for pinned comments of the tab and filter in view, only while the panel is open. Click a marker to select its comment and the other way round.
- **Designer view** posts on the UX tab and sees a status select on every comment (Resolved shows "Resolved in {date}"), **Dismiss**, and a collapsed **Dismissed (n)** list with **Restore**. **Stakeholder view** posts on the Stakeholder tab and never sees those controls.
- Form: name (team suggestions), category, text, and *General* or *Specific spot*. **Pick a spot**, then click or tap the design. Post stays disabled until the form is valid. A draft survives switching views.
- **Copy** puts the selected update's unresolved comments (open and in progress, both tabs, dismissed left out) on the clipboard as a Markdown list.
- **Reset saved comments** asks for confirmation inside the panel (not with `confirm()`), then clears everything saved in this browser.

When a comment is marked Resolved in the UI, "Resolved in" is set to the date of the newest update (or the comment's own `resolvedIn` if it has one).

## How comments are saved

Posted comments, status changes and dismissals are stored in **this browser only** (`localStorage`, key `design-review:<project name>`), separately for each update. They are **not shared** with other people or devices, and the config file is never modified.

To keep them: press **Copy**, paste the list into your notes, and move what matters into the config as comments of that update (or `resolvedIn` / `dismissed` flags). Then **Reset** to start clean.

## Known limits

- An older update is shown over **today's design**. Q - Peek does not keep a snapshot per update, so pins and hotspots of an old update can sit slightly off if the design has changed since.
- For `figma` and `code`, markers are positions on the frame (percent of the iframe), **not pinned to elements**. They drift if the frame is scaled or scrolls internally. The review layer cannot see inside the iframe.
- Pinning by keyboard is not possible: "Pick a spot" needs a pointer or touch. Comments can be posted without a pin.
- On phones the comments panel covers the design, so markers are not visible while it is open; "Pick a spot" slides the panel away while you tap.
- The Figma embed and `?config=` URLs must be reachable by the viewer; `?config=` must be on the same site as the page.
- Opened from disk, paths resolve against `index.html`, not the picked config file.
- Storage is per browser profile; private windows or blocked storage fall back to memory with a notice in the panel.

## Files

| File | |
| --- | --- |
| `index.html` | The whole app |
| `review.config.json` | Example config (screens, with commented-out figma and code examples) |
| `example/screens/*.svg` | Three placeholder screens |
| `example/prototype.html` | Local page for the `code` example |
| `tests/` | Playwright end-to-end suite (`python3 -m http.server 8765`, then `node tests/peek.test.js`) |

`img/` and `src/` belong to the previous Monitoring Program Renewal page that used to live in this repository (see git history before this change). Q - Peek does not use them.
