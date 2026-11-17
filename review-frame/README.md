# Design review frame

One page, `index.html`, that wraps any design in a weekly review layer: an update picker, a "What changed" list, a click-through prototype or embedded design, and a comments panel for UX insight and stakeholder feedback.

Everything a designer fills in lives in `review.config.json`. A new project is a new config. There is no build step and no dependency.

This copy is published at `https://arooshadesignstudio.com/review-frame/`. Edit `review.config.json` in this folder and the page changes a minute or two after the commit reaches `main`.

## Files

| Path | What it is |
| --- | --- |
| `index.html` | The review page. You should not need to edit it. |
| `review.config.json` | The project: name, team, design, updates, comments. Ships filled in with a placeholder example. |
| `example/screens/` | Three placeholder screens used by the example config. |
| `example/prototype.html` | A placeholder coded prototype, used by the `code` example in the config. |

## Run it

Serve the folder and open it:

```bash
python3 -m http.server 8000
```

Then open `http://localhost:8000`. On the site it is served by GitHub Pages straight from this folder.

If you double-click `index.html` instead, the browser will not let the page read the config by itself. The page then shows a "Choose the config file" button; pick `review.config.json` and it runs.

## Start a new project

1. Copy this folder (or keep it and replace the example).
2. Edit `review.config.json`: project name and description, team, design, and one entry under `updates`.
3. Each week, add a new entry at the top of `updates` with the date, what changed, and any comments.

The lines starting with `//` in the config are notes. The page skips them, along with trailing commas. Other JSON tools may reject the file because of them; delete the notes if you need strict JSON.

## Config reference

### `project`

```json
"project": { "name": "Checkout redesign", "description": "One line about the project." }
```

### `team`

```json
"team": [ { "name": "Ana Ruiz", "role": "UX" }, { "name": "Priya Shah", "role": "Stakeholder" } ]
```

`role` is `"UX"` or `"Stakeholder"`. The team is listed in the header and offered as name suggestions in the comment form.

### `design`

`type` picks one of three sources. Keep exactly one `design` block (if two are left in the file, the last one wins).

**`"screens"`**: exported images shown as a click-through prototype.

```json
"design": {
  "type": "screens",
  "flows": [
    {
      "name": "Sign in",
      "screens": [
        {
          "id": "welcome",
          "name": "Welcome",
          "image": "screens/01-welcome.png",
          "width": 1440,
          "height": 900,
          "hotspots": [
            { "x": 120, "y": 440, "width": 220, "height": 56, "target": "sign-in", "label": "Get started" }
          ]
        }
      ]
    }
  ]
}
```

- `flows` are the sub-flows shown as chips. Screens run in the order written, across all sub-flows; "Step n of total" counts across the whole list.
- `id` must be unique. `image` is a path relative to the config file. `width` and `height` are the image size in pixels.
- `hotspots` are optional. Each is a rectangle in image pixels plus `target`, the id of the screen it leads to. `label` is optional and is used as the tooltip.
- A screen is never shown wider than its `width`, so export at 1x or expect a 2x export to display large.

**`"figma"`**: a Figma prototype or file in an iframe.

```json
"design": { "type": "figma", "url": "https://embed.figma.com/proto/FILE_KEY/FILE_NAME?node-id=1-2&embed-host=design-review" }
```

Use the address from Figma's embed code (the part inside `src="…"`), not the whole `<iframe>` snippet. A normal `figma.com` share link is also accepted and is rewritten to the `embed.figma.com` form. Viewers need access to the Figma file. This path was built without a live Figma file to test against, so check your first embed.

**`"code"`**: a local HTML page in an iframe.

```json
"design": { "type": "code", "path": "prototype/index.html" }
```

### `updates`

Newest first. Each update has its own "What changed" list and its own comments.

```json
"updates": [
  {
    "date": "2026-11-09",
    "changes": [
      { "text": "Labels now sit above the fields.", "screen": "sign-in" },
      { "text": "Spacing aligned to the design system." }
    ],
    "comments": {
      "ux": [],
      "stakeholder": []
    }
  }
]
```

Write dates as `YYYY-MM-DD`. `screen` on a change is optional; with the `screens` type it must be a screen id and makes the line a link to that screen.

### Comments

```json
{
  "id": "ux-2",
  "author": "Jordan Lee",
  "role": "UX",
  "date": "2026-11-09",
  "text": "Error text still needs a contrast check.",
  "category": "Accessibility",
  "status": "progress",
  "screen": "sign-in",
  "x": 64.5,
  "y": 35.5
}
```

- `category`: `Accessibility`, `Design system`, `Content`, `Flow` or `General`.
- `status`: `open`, `progress` or `resolved`.
- `screen`, `x`, `y` are optional and pin the comment to a spot. `x` and `y` are percent of the screen, from the top left. Leave them out for a general comment. With the `figma` and `code` types there is no `screen`; `x` and `y` are percent of the frame.
- Two more optional fields: `"resolvedIn": "2026-11-09"` sets the date in "Resolved in …" (it defaults to the update's date), and `"dismissed": true` files the comment under Dismissed for everyone.
- Ids must be unique within an update. Saved status changes and dismissals are attached to the id.

If something in the config does not add up (an unknown screen id, a missing size, a duplicate id), the page still loads and lists what to check under the header. That list is shown in Designer view only.

## How it behaves

- **Top bar**: project name, Update picker, What changed, then the Designer / Stakeholder switch beside the comments button and its count.
- **Screens**: sub-flow chips, breadcrumb, Back, Next and Restart. Left and right arrow keys do the same as Back and Next. Hotspots are invisible until hovered; clicking elsewhere on the screen flashes them. Back returns to where you came from.
- **Comments panel**: two tabs with counts, category filters, numbered markers for pinned comments. Markers show while the panel is open, for the tab and filter in view.
- **Stakeholder view**: a form on the Stakeholder feedback tab. No status controls, no Dismiss, no Dismissed section.
- **Designer view**: the same form on the Insight from UX tab, plus a status select and Dismiss on every comment, and a collapsed Dismissed section with Restore.
- **Copy** puts the unresolved comments of the selected update (open and in progress, both tabs, dismissed ones left out) on the clipboard as a Markdown list.

## Where comments are saved

Comments posted on the page, status changes and dismissals are saved in the browser's `localStorage`, under a key made from the project name. They survive a refresh, and **Reset** clears them. Comments written in the config are never changed by the page.

This means they are not shared. A stakeholder's comment stays in that stakeholder's browser, and a designer's dismissal is not seen by anyone else. To make something permanent for everyone, copy it into `review.config.json` (the Copy button gives you the text).

Renaming the project starts a fresh, empty save, because the key is the project name.

## Links you can share

- `index.html?role=stakeholder` opens in Stakeholder view (`?role=designer` for Designer view). The switch is still on the page; it is a view, not a permission.
- `index.html?config=other.config.json` loads a different config from the same site, so one copy of the page can serve several projects. Image and prototype paths are read relative to that config file.

## Limits worth knowing

- The design is the current one for every update. Picking an older update shows that update's notes and comments over today's design.
- With the `figma` and `code` types, a marker is a position on the frame, not on a particular screen or element inside the prototype. It will not follow the prototype as it changes screen or as the window changes size. Use the `screens` type when pins need to be exact.
- There are no links back to Figma in the review layer and no present mode. Figma's own embed may show its own controls inside the frame; those come from the embed link.
- The page asks search engines not to index it. That is a request, not access control: anyone with the address can open it.
