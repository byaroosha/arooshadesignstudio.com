#!/usr/bin/env python3
"""Build design-review.html from figma.json + shots/<id>.png.
Usage: python3 build.py [shots_dir]
"""
import json, os, re, sys, html

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'shots')
data = json.load(open(os.path.join(HERE, 'figma.json')))
FILE_KEY = data['fileKey']

def slug(nid): return nid.replace(':', '-')
def norm(s): return re.sub(r'\s+', ' ', s).strip().lower()

# Map available image files by normalized basename and by node id.
img_by_name, img_by_id = {}, {}
if os.path.isdir(SHOTS):
    for f in os.listdir(SHOTS):
        if not f.lower().endswith('.png'): continue
        base = os.path.splitext(f)[0]
        img_by_name[norm(base)] = f
        img_by_id[base] = f

ROW_TOL = 1500  # canvas px; rows are ~4700 apart

def build_section(sec):
    screens = sorted(sec['screens'], key=lambda s: (s['y'], s['x']))
    # rows by y
    rows = []
    for s in screens:
        for r in rows:
            if abs(r['y'] - s['y']) < ROW_TOL: r['screens'].append(s); break
        else: rows.append({'y': s['y'], 'screens': [s]})
    rows.sort(key=lambda r: r['y'])
    groups = []  # ordered sub-flows
    for r in rows:
        labels = sorted([l for l in sec['labels'] if abs(l['y'] - r['y']) < ROW_TOL], key=lambda l: l['x'])
        flows = sorted([f for f in sec['flows'] if abs((f['y'] + 525) - r['y']) < ROW_TOL], key=lambda f: f['x'])
        for s in sorted(r['screens'], key=lambda s: s['x']):
            lab = max([l for l in labels if l['x'] <= s['x']] or [None], key=lambda l: l['x'] if l else -1)
            flo = max([f for f in flows if f['x'] <= s['x']] or [None], key=lambda f: f['x'] if f else -1)
            key = (flo['id'] if flo else '', lab['id'] if lab else '')
            g = next((g for g in groups if g['key'] == key), None)
            if not g:
                g = {'key': key, 'flow': flo['name'] if flo else sec['name'], 'flowStatus': (flo or {}).get('status', ''), 'label': lab['text'] if lab else '', 'screens': []}
                groups.append(g)
            g['screens'].append(s)
    # pin notes to nearest screen in their row
    notes = []
    for n in sec['notes']:
        cx = n['x'] + n['w'] / 2
        cand = [r for r in rows if -1200 < (r['y'] - n['y']) < 4000]  # note sits above or beside its row
        row = min(cand or rows, key=lambda r: abs(r['y'] - n['y']))
        scr = min(row['screens'], key=lambda s: abs((s['x'] + s['w'] / 2) - cx))
        fx = (cx - scr['x']) / scr['w']
        notes.append({'id': n['id'], 'kind': n['kind'], 'date': n.get('date'), 'text': n['text'], 'screen': scr['id'], 'fx': round(min(0.94, max(0.06, fx)), 3), 'fy': 0.06})
    out = {'id': sec['id'], 'name': sec['name'].replace('Action - ', ''), 'status': sec['status'], 'ticket': sec['ticket'], 'groups': [], 'notes': notes}
    step = 0
    for g in groups:
        gs = []
        for s in g['screens']:
            step += 1
            f = img_by_id.get(slug(s['id'])) or img_by_name.get(norm(s['name']))
            # Images are published alongside the page as img/<node-id>.webp (already in the live artifact).
            gs.append({'id': s['id'], 'name': re.sub(r'\s+', ' ', s['name']), 'w': s['w'], 'h': s['h'], 'step': step, 'img': ('shots/' + f) if f else ('img/' + slug(s['id']) + '.webp')})
        out['groups'].append({'flow': g['flow'], 'flowStatus': g['flowStatus'], 'label': g['label'], 'screens': gs})
    return out

SECTIONS = [build_section(s) for s in sorted(data['sections'], key=lambda s: s['y'])]
all_dates = sorted({n['date'] for s in SECTIONS for n in s['notes'] if n.get('date')}, reverse=True)
UPDATES = [{'id': 'u' + d.replace('-', ''), 'date': d} for d in all_dates]
missing = [s['name'] for sec in SECTIONS for g in sec['groups'] for s in g['screens'] if not s['img']]
print(f"sections={len(SECTIONS)} screens={sum(len(g['screens']) for sec in SECTIONS for g in sec['groups'])} notes={sum(len(s['notes']) for s in SECTIONS)} updates={[u['date'] for u in UPDATES]} missing_images={len(missing)}")
for m in missing: print('  missing:', m)

# Hotspots: screen id -> list of [x, y, w, h, label, target screen id] in frame pixels, read from the text/button bounds in the Figma file.
HOTSPOTS = {
 # Renew Program (clinic)
 '1:2913': [[1190,690,150,60,'Renew Program (overflow menu)','1:4256']],
 '1:4256': [[1030,350,390,42,'Search for a diagnosis','1:6385'],[757,927,260,50,'Modify Information','1:3724']],
 '1:6385': [[416,390,390,300,'Pick a diagnosis from the results','1:5849']],
 '1:5849': [[634,1625,300,40,'I hereby e-Sign','1:5313']],
 '1:5313': [[1037,1735,260,50,'Submit','1:6667']],
 '1:3724': [[757,927,260,50,'Modify Information','1:7065']],
 '1:7065': [[720,3014,260,50,'Submit order','1:7386'],[797,3074,106,60,'Cancel (back to Monitoring To-Do’s)','1:2913']],
 '1:7386': [[792,496,117,60,'Close (back to Monitoring To-Do’s)','1:2913']],
 # Renew Program (Quest draw)
 '1:3317': [[1226,630,150,60,'Renew Program (overflow menu)','1:4781']],
 '1:4781': [[1030,350,390,42,'Search for a diagnosis','1:6521'],[757,927,260,50,'Modify Information','1:3724']],
 '1:6521': [[423,1676,260,50,'Submit','1:6667']],
 # Schedule and Renew
 '1:8084': [[1132,690,240,60,'Mark Scheduled and Renew (overflow menu)','1:14140']],
 '1:14140': [[897,927,260,50,'Continue','1:14621'],[634,640,240,40,'Cancel the last draw','1:8939']],
 '1:14621': [[634,306,260,38,'Yes, renew program','1:15075'],[634,336,260,38,'No, don’t renew','1:8486']],
 '1:15075': [[1030,556,390,42,'Search for a diagnosis','1:17272'],[757,927,260,50,'Modify Information','1:9874'],[634,336,260,38,'No, don’t renew','1:8486']],
 '1:17272': [[416,600,390,300,'Pick a diagnosis from the results','1:16168']],
 '1:16168': [[634,1831,300,40,'I hereby e-Sign','1:15616'],[757,1941,260,50,'Modify Information','1:9874']],
 '1:15616': [[1037,1941,260,50,'Submit','1:13749']],
 '1:8486': [[897,927,260,50,'Submit','1:13295'],[634,306,260,38,'Yes, renew program','1:15075']],
 '1:13295': [[897,927,260,50,'Submit','1:17440']],
 '1:8939': [[634,680,380,50,'Select reason for cancellation','1:11412'],[634,546,300,40,'Mark the last draw as scheduled','1:14140']],
 '1:11412': [[664,660,362,220,'Pick a cancellation reason','1:11887']],
 '1:11887': [[897,927,260,50,'Continue','1:12367']],
 '1:12367': [[897,927,260,50,'Continue','1:12842']],
 '1:12842': [[634,306,260,38,'Yes, renew program','1:16720'],[634,336,260,38,'No, don’t renew','1:9420']],
 '1:16720': [[1037,1941,260,50,'Submit','1:17851'],[757,1941,260,50,'Modify Information','1:10416']],
 '1:9420': [[897,927,260,50,'Submit','1:10958']],
 '1:10958': [[897,927,260,50,'Submit','1:18242']],
 '1:9874': [[757,927,260,50,'Modify Information','1:18633']],
 '1:18633': [[720,2930,260,50,'Submit order','1:19276'],[797,2990,106,60,'Cancel (back to Monitoring To-Do’s)','1:8084']],
 '1:19276': [[792,496,117,60,'Close (back to Monitoring To-Do’s)','1:8084']],
 '1:10416': [[757,927,260,50,'Modify Information','1:18950']],
 '1:18950': [[720,2952,260,50,'Submit order','1:19376'],[797,3012,106,60,'Cancel (back to Monitoring To-Do’s)','1:8084']],
 '1:19376': [[792,496,117,60,'Close (back to Monitoring To-Do’s)','1:8084']],
}
known = {s['id'] for sec in SECTIONS for g in sec['groups'] for s in g['screens']}
bad = [(k, t) for k, hs in HOTSPOTS.items() for h in hs for t in [h[5]] if k not in known or t not in known]
if bad: print('BAD HOTSPOT IDS', bad)

# Set EMPTY_MIDDLE = False once the Figma screens should show again; everything else stays wired up.
EMPTY_MIDDLE = True
DATA_JS = json.dumps({'fileKey': FILE_KEY, 'updates': UPDATES, 'sections': SECTIONS, 'hotspots': HOTSPOTS, 'empty': EMPTY_MIDDLE}, ensure_ascii=False)

PAGE = r'''<title>Monitoring Program Renewal Review</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* Layout: fixed review bar; a scrolling stage that lists the Figma screens of one flow in order; a side panel that takes width from the stage. */
:root{
  /* Palette from the Wireframe Component Library: UX Base grays, UX Accents */
  --bg:#EEF0F7; --surface:#FFFFFF; --surface-2:#F6F8FD; --fg:#1B202B; --muted:#737D94; --border:#CDD2DF; --border-strong:#A2ABBE;
  --accent:#5BADF1; --accent-soft:#B9DBFC; --accent-fg:#1B202B; --on-color:#1B202B;
  --ux:#6CD860; --ux-soft:#DAFEDC; --stake:#8280F7; --stake-soft:#D2D1FC;
  --ok:#6CD860; --ok-soft:#DAFEDC; --warn:#F8D65B; --warn-soft:#FCEEB5; --bad:#EC5F59; --bad-soft:#F5BBBA;
  --font-ui:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif; --font-mono:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace;
  --shadow:0 8px 24px rgba(16,18,24,.10);
}
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]){
  --bg:#1B202B; --surface:#2F3647; --surface-2:#3A4254; --fg:#EEF0F7; --muted:#A2ABBE; --border:#4C5466; --border-strong:#737D94;
  --accent:#5BADF1; --accent-soft:rgba(91,173,241,.28); --accent-fg:#1B202B; --on-color:#1B202B;
  --ux:#6CD860; --ux-soft:#DAFEDC; --stake:#8280F7; --stake-soft:#D2D1FC;
  --ok:#6CD860; --ok-soft:#DAFEDC; --warn:#F8D65B; --warn-soft:#FCEEB5; --bad:#EC5F59; --bad-soft:#F5BBBA;
  --shadow:0 8px 24px rgba(0,0,0,.45); color-scheme:dark } }
:root[data-theme="dark"]{
  --bg:#1B202B; --surface:#2F3647; --surface-2:#3A4254; --fg:#EEF0F7; --muted:#A2ABBE; --border:#4C5466; --border-strong:#737D94;
  --accent:#5BADF1; --accent-soft:rgba(91,173,241,.28); --accent-fg:#1B202B; --on-color:#1B202B;
  --ux:#6CD860; --ux-soft:#DAFEDC; --stake:#8280F7; --stake-soft:#D2D1FC;
  --ok:#6CD860; --ok-soft:#DAFEDC; --warn:#F8D65B; --warn-soft:#FCEEB5; --bad:#EC5F59; --bad-soft:#F5BBBA;
  --shadow:0 8px 24px rgba(0,0,0,.45); color-scheme:dark }

html,body{height:100%}
body{margin:0;background:var(--bg);color:var(--fg);font-family:var(--font-ui);font-size:14px;line-height:1.45;overflow:hidden}
body::before{content:"";position:fixed;inset:0 0 auto;height:env(safe-area-inset-top,0px);z-index:10;background:var(--surface)}
*,*::before,*::after{box-sizing:border-box}
button,select,input,textarea{font:inherit;color:inherit}
button{cursor:pointer}
a{color:inherit}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
#app{height:100%;display:flex;flex-direction:column}

#bar{position:sticky;top:env(safe-area-inset-top,0px);z-index:5;background:var(--surface);border-bottom:1px solid var(--border);
  padding-block:8px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));
  display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.bar-group{display:flex;align-items:center;gap:6px;min-width:0;flex-wrap:wrap}
.bar-spacer{flex:1}
.brand{font-weight:600;white-space:nowrap}
.brand small{color:var(--muted);font-weight:400;margin-left:6px}
.seg{display:inline-flex;border:1px solid var(--border);border-radius:8px;overflow:hidden;background:var(--surface-2)}
.seg button{border:0;background:transparent;padding:6px 10px;color:var(--muted);font-weight:500;line-height:1}
.seg button[aria-pressed="true"]{background:var(--fg);color:var(--bg)}
.seg button + button{border-left:1px solid var(--border)}
.ctl{border:1px solid var(--border);background:var(--surface-2);border-radius:8px;padding:6px 10px;line-height:1.2;min-height:32px;display:inline-flex;align-items:center;gap:6px;text-decoration:none}
select.ctl{padding-right:28px;appearance:none;-webkit-appearance:none;background-image:linear-gradient(45deg,transparent 50%,var(--muted) 50%),linear-gradient(135deg,var(--muted) 50%,transparent 50%);background-position:calc(100% - 14px) 55%,calc(100% - 9px) 55%;background-size:5px 5px;background-repeat:no-repeat;max-width:260px}
.ctl:hover{border-color:var(--border-strong)}
.ctl[aria-pressed="true"]{background:var(--accent-soft);border-color:var(--accent);color:var(--fg)}
.icon-btn{position:relative;width:36px;height:32px;padding:0;justify-content:center}
.icon-btn svg{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.badge{position:absolute;top:-6px;right:-6px;min-width:18px;height:18px;padding:0 5px;border-radius:9px;background:var(--accent);color:var(--accent-fg);font-size:11px;font-weight:600;display:flex;align-items:center;justify-content:center;font-variant-numeric:tabular-nums}
.menu-wrap{position:relative}
.menu{position:absolute;top:calc(100% + 6px);left:0;z-index:20;background:var(--surface);border:1px solid var(--border);border-radius:10px;box-shadow:var(--shadow);min-width:300px;max-width:min(420px,90vw);padding:8px}
.menu h4{margin:6px 6px 4px;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:600}
.changes{list-style:none;margin:0;padding:0}
.changes li{padding:8px 6px;border-top:1px solid var(--border);display:flex;flex-direction:column;gap:3px;cursor:pointer;border-radius:6px}
.changes li:hover{background:var(--surface-2)}
.changes li:first-child{border-top:0}
.changes .where{font-size:12px;color:var(--muted)}
.changes .empty{color:var(--muted);padding:8px 6px}

#main{flex:1;display:flex;min-height:0;position:relative}
#stage{flex:1;min-width:0;overflow:auto;padding-block:20px 60px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
.stage-inner{max-width:1040px;margin:0 auto;display:flex;flex-direction:column;gap:18px}
.flow-head{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap}
.flow-head h1{margin:0;font-size:20px;font-weight:600;text-wrap:balance}
.flow-head .status{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:var(--on-color);background:var(--ok-soft);padding:2px 8px;border-radius:999px}
.flow-head .meta{color:var(--muted);font-size:12px}
.subnav{display:flex;gap:6px;flex-wrap:wrap;position:sticky;top:0;z-index:2;background:var(--bg);padding-block:6px;margin-block:-6px}
.subnav a{font-size:12px;border:1px solid var(--border);background:var(--surface);border-radius:999px;padding:4px 10px;text-decoration:none;color:var(--muted)}
.subnav a:hover{color:var(--fg);border-color:var(--border-strong)}
.subnav a[aria-current="true"]{background:var(--fg);color:var(--bg);border-color:var(--fg)}
.group{display:flex;flex-direction:column;gap:14px;scroll-margin-top:60px}
.group-head{display:flex;flex-direction:column;gap:2px;padding-top:12px;border-top:1px solid var(--border)}
.group-head .flow{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:600}
.group-head h2{margin:0;font-size:16px;font-weight:600}
.screen{border:1px solid var(--border);border-radius:10px;background:var(--surface);overflow:hidden;scroll-margin-top:70px;position:relative}
.screen-head{display:flex;align-items:center;gap:10px;padding:8px 12px;border-bottom:1px solid var(--border);font-size:13px;flex-wrap:wrap}
.screen-head .step{font-family:var(--font-mono);font-size:12px;color:var(--muted);font-variant-numeric:tabular-nums}
.screen-head .name{font-weight:500;flex:1;min-width:0}
.screen-head a{font-size:12px;color:var(--muted);text-decoration:none;white-space:nowrap}
.screen-head a:hover{color:var(--fg);text-decoration:underline}
.shot{position:relative;background:var(--surface-2)}
.shot img{display:block;width:100%;height:auto;max-width:100%}
.shot .ph{display:flex;align-items:center;justify-content:center;color:var(--muted);font-size:13px;text-align:center;padding:16px}
.screen.hl{outline:2px solid var(--accent);outline-offset:2px;box-shadow:0 0 0 6px var(--accent-soft)}
.screen.picking .shot{cursor:crosshair}
.pin{position:absolute;transform:translate(-50%,-50%);z-index:3;min-width:22px;height:22px;padding:0 6px;border-radius:11px;background:var(--accent);color:var(--accent-fg);border:2px solid var(--surface);font:600 11px/18px var(--font-ui);display:flex;align-items:center;justify-content:center;box-shadow:0 1px 4px rgba(0,0,0,.35);cursor:pointer;font-variant-numeric:tabular-nums}
.pin.stake{background:var(--stake);color:var(--on-color)}
.pin.on{transform:translate(-50%,-50%) scale(1.25);outline:3px solid var(--accent-soft)}
.pin.draft{background:var(--fg);color:var(--bg)}
.hint{position:absolute;left:50%;bottom:16px;transform:translateX(-50%);z-index:6;background:var(--fg);color:var(--bg);padding:8px 14px;border-radius:999px;font-size:13px;box-shadow:var(--shadow);max-width:calc(100% - 32px);text-align:center}

#panel{width:400px;flex:0 0 400px;border-left:1px solid var(--border);background:var(--surface);display:flex;flex-direction:column;min-height:0}
#panel[hidden]{display:none}
.panel-head{padding:12px 14px;border-bottom:1px solid var(--border);display:flex;align-items:flex-start;gap:8px}
.panel-head h2{margin:0;font-size:15px;font-weight:600}
.panel-head .sub{color:var(--muted);font-size:12px;margin-top:2px}
.panel-head .grow{flex:1;min-width:0}
.x{border:1px solid transparent;background:transparent;border-radius:6px;width:30px;height:30px;display:inline-flex;align-items:center;justify-content:center;color:var(--muted)}
.x:hover{background:var(--surface-2);color:var(--fg)}
.tabs{display:flex;border-bottom:1px solid var(--border);padding:0 8px}
.tabs button{border:0;background:transparent;padding:10px 8px;color:var(--muted);font-weight:500;border-bottom:2px solid transparent;margin-bottom:-1px;display:flex;align-items:center;gap:6px}
.tabs button[aria-selected="true"]{color:var(--fg);border-bottom-color:var(--fg)}
.count{font-size:11px;background:var(--surface-2);border:1px solid var(--border);border-radius:999px;padding:0 6px;line-height:16px;font-variant-numeric:tabular-nums}
.chips{display:flex;gap:6px;flex-wrap:wrap;padding:10px 14px 0}
.chip{border:1px solid var(--border);background:transparent;border-radius:999px;padding:3px 10px;font-size:12px;color:var(--muted)}
.chip[aria-pressed="true"]{background:var(--fg);color:var(--bg);border-color:var(--fg)}
.panel-body{flex:1;overflow:auto;min-height:0;padding:12px 14px;display:flex;flex-direction:column;gap:10px}
.empty{color:var(--muted);font-size:13px;padding:18px 6px;text-align:center;border:1px dashed var(--border);border-radius:8px}
.comment{border:1px solid var(--border);border-radius:10px;padding:10px 12px;background:var(--surface);display:grid;grid-template-columns:auto 1fr;gap:6px 10px}
.comment.linked{cursor:pointer}
.comment.linked:hover{border-color:var(--border-strong)}
.comment.selected{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}
.comment.dim{opacity:.6}
.comment.new{border-left:3px solid var(--accent)}
.num{width:22px;height:22px;border-radius:50%;background:var(--surface-2);border:1px solid var(--border);display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:600;font-variant-numeric:tabular-nums;grid-row:1 / span 3}
.num.on{background:var(--accent);color:var(--accent-fg);border-color:var(--accent)}
.num.general{background:transparent;border-style:dashed;color:var(--muted)}
.c-meta{display:flex;align-items:center;gap:6px;flex-wrap:wrap;font-size:12px;color:var(--muted)}
.c-meta b{color:var(--fg);font-weight:600}
.pill{font-size:11px;font-weight:600;padding:1px 7px;border-radius:999px;line-height:16px;white-space:nowrap}
.pill{color:var(--on-color)}
.pill.ux{background:var(--ux-soft)} .pill.stake{background:var(--stake-soft)}
.pill.open{background:var(--surface-2);color:var(--muted);border:1px solid var(--border)} .pill.progress{background:var(--warn)} .pill.resolved{background:var(--ok)}
.pill.newpill{background:var(--accent-soft)}
.c-text{font-size:13.5px;line-height:1.45;grid-column:2;white-space:pre-line}
.c-tags{grid-column:2;display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.tag{font-size:11px;border:1px solid var(--border);border-radius:5px;padding:1px 6px;color:var(--muted);background:var(--surface-2);max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.tag.area{color:var(--fg);border-color:var(--border-strong)}
.c-actions{grid-column:2;display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin-top:2px}
.c-actions select{font-size:12px;padding:3px 24px 3px 8px;min-height:26px;border-radius:6px}
.link-btn{border:0;background:transparent;color:var(--muted);font-size:12px;padding:3px 6px;border-radius:6px;text-decoration:underline;text-underline-offset:2px}
.link-btn:hover{color:var(--fg);background:var(--surface-2)}
details.dismissed{border-top:1px solid var(--border);padding-top:8px;margin-top:4px}
details.dismissed summary{cursor:pointer;color:var(--muted);font-size:12px;font-weight:600;padding:4px 0}
details.dismissed .list{display:flex;flex-direction:column;gap:8px;margin-top:8px}
.cform{border-top:1px solid var(--border);padding:12px 14px;display:flex;flex-direction:column;gap:8px;background:var(--surface-2)}
.cform h3{margin:0;font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:600}
.cform input,.cform textarea,.cform select{width:100%;border:1px solid var(--border);background:var(--surface);border-radius:8px;padding:8px 10px}
.cform textarea{min-height:64px;resize:vertical}
.cform .two{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.cform .foot{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.btn{border:1px solid var(--border);background:var(--surface);border-radius:8px;padding:7px 12px;font-weight:500;line-height:1.2}
.btn:hover{border-color:var(--border-strong)}
.btn.primary{background:var(--fg);color:var(--bg);border-color:var(--fg)}
.btn.primary:disabled{opacity:.45;cursor:not-allowed}
.btn.small{padding:4px 8px;font-size:12px}
.area-pick{display:flex;align-items:center;gap:6px;flex-wrap:wrap}
.area-pick .tag.area{padding:4px 8px;font-size:12px}
.toast{color:var(--fg);font-size:12px}
.panel-foot{border-top:1px solid var(--border);padding:8px 14px;display:flex;justify-content:space-between;align-items:center;gap:8px;font-size:12px;color:var(--muted)}
/* Prototype view */
.proto{display:grid;grid-template-columns:minmax(0,1fr);gap:18px;align-items:start}
.rail{position:sticky;top:0;max-height:calc(100vh - 120px);overflow:auto;border:1px solid var(--border);border-radius:10px;background:var(--surface);padding:6px;display:flex;flex-direction:column;gap:2px}
.rail .rg{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:600;padding:10px 8px 4px}
.rail button{border:0;background:transparent;text-align:left;padding:6px 8px;border-radius:6px;display:flex;gap:8px;align-items:flex-start;font-size:12.5px;line-height:1.3;color:var(--fg)}
.rail button:hover{background:var(--surface-2)}
.rail button[aria-current="step"]{background:var(--accent-soft);font-weight:500}
.rail button .n{font-family:var(--font-mono);font-size:11px;color:var(--muted);flex:none;padding-top:1px;font-variant-numeric:tabular-nums}
.rail button .cnt{margin-left:auto;flex:none;font-size:11px;background:var(--surface-2);border:1px solid var(--border);border-radius:999px;padding:0 5px;line-height:15px}
.proto-main{display:flex;flex-direction:column;gap:10px;min-width:0}
.crumb{display:flex;align-items:center;gap:6px;flex-wrap:wrap;font-size:12px;color:var(--muted)}
.crumb b{color:var(--fg);font-weight:500}
.crumb .sep{opacity:.5}
.proto-nav{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.proto-nav .spacer{flex:1}
.hot{position:absolute;border-radius:6px;cursor:pointer;background:transparent;border:2px solid transparent;z-index:2;padding:0}
.hot:hover,.hot:focus-visible{border-color:var(--accent);background:var(--accent-soft)}
.screen.show-hot .hot,.screen.flash .hot{border-color:var(--accent);background:var(--accent-soft)}
.hot .lbl{position:absolute;left:0;bottom:calc(100% + 4px);background:var(--fg);color:var(--bg);font-size:11px;padding:2px 6px;border-radius:4px;white-space:nowrap;opacity:0;pointer-events:none;transition:opacity .12s}
.hot:hover .lbl,.hot:focus-visible .lbl{opacity:1}
.screen.flash{animation:none}
@media (prefers-reduced-motion:no-preference){ .screen.flash .hot{animation:hotflash .9s ease} @keyframes hotflash{0%,100%{box-shadow:0 0 0 0 var(--accent-soft)}40%{box-shadow:0 0 0 8px var(--accent-soft)}} }
.end-note{font-size:12.5px;color:var(--muted);border:1px dashed var(--border);border-radius:8px;padding:10px 12px}
.slot{border:2px dashed var(--border-strong);border-radius:12px;background:var(--surface);min-height:420px;aspect-ratio:16/10;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;color:var(--muted);text-align:center;padding:24px}
.slot b{color:var(--fg);font-weight:600;font-size:15px}

body.present #bar,body.present #panel{display:none}
#exit-present{position:fixed;right:max(16px,env(safe-area-inset-right,0px));bottom:calc(16px + env(safe-area-inset-bottom,0px));z-index:30;box-shadow:var(--shadow)}
@media (max-width:760px){ #panel{position:absolute;inset:0;width:100%;flex-basis:100%;border-left:0;z-index:8} .brand small{display:none} select.ctl{max-width:200px} }
@media (prefers-reduced-motion:reduce){ *{scroll-behavior:auto!important} }
</style>

<div id="app">
  <header id="bar">
    <div class="bar-group">
      <span class="brand">Review<small>interactive</small></span>
    </div>
    <div class="bar-group">
      <label class="sr-only" for="flow-select">Flow</label>
      <select id="flow-select" class="ctl"></select>
      <label class="sr-only" for="update-select">Design update</label>
      <select id="update-select" class="ctl"></select>
      <div class="menu-wrap">
        <button type="button" class="ctl" id="changes-btn" aria-expanded="false">What changed</button>
        <div class="menu" id="changes-menu" hidden></div>
      </div>
    </div>
    <div class="bar-spacer"></div>
    <div class="bar-group">
      <div class="seg" role="group" aria-label="Viewing as">
        <button type="button" data-role="designer" aria-pressed="true">Designer</button>
        <button type="button" data-role="stakeholder" aria-pressed="false">Stakeholder</button>
      </div>
      <button type="button" class="ctl icon-btn" id="comments-btn" aria-pressed="false" aria-label="Comments" title="Comments">
        <svg viewBox="0 0 24 24"><path d="M21 12a8 8 0 0 1-8 8H8l-5 3 1.2-4.5A8 8 0 1 1 21 12z"/></svg>
        <span class="badge" id="comments-badge">0</span>
      </button>
    </div>
  </header>
  <div id="main">
    <div id="stage"><div class="stage-inner" id="stage-inner"></div></div>
    <aside id="panel" hidden aria-label="Review panel"></aside>
    <div class="hint" id="hint" hidden></div>
  </div>
</div>

<script>
const DATA = __DATA__;
const CATEGORIES = ['Accessibility','Design system','Content','Flow','General'];
const state = {
  role:'designer', sectionId: DATA.sections[0].id, updateId: DATA.updates[0].id, panel:false, tab:'ux', filter:'All',
  selected:null, picking:false, present:false,
  view:'proto', current:null, showHot:false, history:[],
  form:{ name:'', text:'', category:'General', type:'general', screen:null, fx:null, fy:null },
  posted:{}, edits:{},
};
const STORE_KEY = 'mpr-review-v1';
function load(){ try{ const s = JSON.parse(localStorage.getItem(STORE_KEY) || 'null'); if(s){ state.posted = s.posted || {}; state.edits = s.edits || {}; if(s.role) state.role = s.role; } }catch(e){} }
function save(){ try{ localStorage.setItem(STORE_KEY, JSON.stringify({ posted: state.posted, edits: state.edits, role: state.role })); }catch(e){} }
load();
const $ = (s, r=document) => r.querySelector(s); const $$ = (s, r=document) => Array.from(r.querySelectorAll(s));
function esc(s){ return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function fmtDate(iso){ const [y,m,d] = iso.split('-').map(Number); return new Date(y, m-1, d).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'}); }
function todayIso(){ const d = new Date(); return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0'); }
function sec(){ return DATA.sections.find(s => s.id === state.sectionId); }
function upd(){ return DATA.updates.find(u => u.id === state.updateId); }
function updIdx(){ return DATA.updates.findIndex(u => u.id === state.updateId); }
function screenOf(id){ for(const g of sec().groups){ const s = g.screens.find(s => s.id === id); if(s) return s; } return null; }
function withEdits(c){ return Object.assign({ dismissed:false, resolvedIn:null, status:'open' }, c, state.edits[c.id] || {}); }
function uxBase(){
  // Notes from Figma for this flow. Dated notes only show from their update onward; undated Design Insights are the standing spec.
  const cur = upd().date;
  return sec().notes.filter(n => !n.date || n.date <= cur).map(n => ({
    id:n.id, author:'UX team', role:'UX', date:n.date || null, screen:n.screen, fx:n.fx, fy:n.fy,
    category: n.kind === 'Design Insight' ? 'Design Insight' : 'Flow update', kind:n.kind, text:n.text, isNew: n.date === cur, figma:true
  }));
}
function listFor(tab){
  const key = state.sectionId + '|' + state.updateId;
  const extra = ((state.posted[key] || {})[tab]) || [];
  const base = tab === 'ux' ? uxBase() : [];
  return extra.concat(base).map(withEdits);
}
function visible(tab){ return listFor(tab).filter(c => !c.dismissed); }
function numbered(tab){ return visible(tab).map((c,i) => Object.assign({ n:i+1 }, c)); }
function roleIsDesigner(){ return state.role === 'designer'; }

/* ---------- stage ---------- */
function allScreens(){ return sec().groups.flatMap(g => g.screens.map(s => Object.assign({ group:g }, s))); }
function firstScreen(){ return allScreens()[0].id; }
function ensureCurrent(){ if(!state.current || !screenOf(state.current)) state.current = firstScreen(); }
function shotHtml(sc){
  return `<div class="shot" style="aspect-ratio:${sc.w}/${sc.h}">${sc.img ? `<img src="${esc(sc.img)}" alt="${esc(sc.name)}" width="${sc.w}" height="${sc.h}" loading="lazy">` : `<div class="ph" style="position:absolute;inset:0">Image not exported yet: ${esc(sc.name)}</div>`}<div class="pins"></div>${state.view==='proto' ? (DATA.hotspots[sc.id]||[]).map(h => `<button type="button" class="hot" data-to="${h[5]}" style="left:${h[0]/sc.w*100}%;top:${h[1]/sc.h*100}%;width:${h[2]/sc.w*100}%;height:${h[3]/sc.h*100}%" aria-label="${esc(h[4])}"><span class="lbl">${esc(h[4])}</span></button>`).join('') : ''}</div>`;
}
function renderStage(){
  const s = sec(); const inner = $('#stage-inner');
  if(state.view === 'proto'){ renderProto(inner); applyPins(); applyHighlight(false); return; }
  const nav = s.groups.map((g,i) => `<a href="#g${i}" data-goto-group="${i}">${esc(g.label || g.flow)}</a>`).join('');
  inner.innerHTML = `<div class="flow-head"><h1>${esc(s.name)}</h1><span class="status">${esc(s.status)}</span><span class="meta">${esc(s.ticket)} · ${s.groups.reduce((n,g)=>n+g.screens.length,0)} screens · ${updIdx()===0?'Last update: ':''}${esc(fmtDate(upd().date))}</span></div>
    <nav class="subnav" aria-label="Sub-flows">${nav}</nav>
    ${s.groups.map((g,i) => `<section class="group" id="g${i}"><div class="group-head"><span class="flow">${esc(g.flow)}${g.flowStatus ? ' · ' + esc(g.flowStatus.toLowerCase()) : ''}</span><h2>${esc(g.label || g.flow)}</h2></div>
      ${g.screens.map(sc => `<article class="screen" id="s-${sc.id.replace(':','-')}" data-screen="${sc.id}"><div class="screen-head"><span class="step">${String(sc.step).padStart(2,'0')}</span><span class="name">${esc(sc.name)}</span></div>${shotHtml(sc)}</article>`).join('')}
    </section>`).join('')}`;
  applyPins(); applyHighlight(false);
}
function renderProto(inner){
  ensureCurrent();
  const s = sec(); const list = allScreens(); const idx = list.findIndex(x => x.id === state.current); const sc = list[idx];
  const hs = DATA.hotspots[sc.id] || [];
  const rail = s.groups.map(g => `<div class="rg">${esc(g.label || g.flow)}</div>` + g.screens.map(x => `<button type="button" data-jump="${x.id}"${x.id===state.current?' aria-current="step"':''}><span class="n">${String(x.step).padStart(2,'0')}</span><span>${esc(x.name.replace(/^.*? - /,'') === x.name ? x.name : x.name.replace(/^.*? - /,''))}</span>${(() => { const n = numbered(state.tab).filter(c => c.screen === x.id).length; return n && state.panel ? `<span class="cnt">${n}</span>` : ''; })()}</button>`).join('')).join('');
  inner.innerHTML = `<div class="flow-head"><h1>${esc(s.name)}</h1><span class="status">${esc(s.status)}</span><span class="meta">${esc(s.ticket)} · ${list.length} screens · ${updIdx()===0?'Last update: ':''}${esc(fmtDate(upd().date))}</span></div>
    <nav class="subnav" aria-label="Sub-flows">${s.groups.map((g,i) => `<a href="#" data-jump="${g.screens[0].id}"${g === sc.group ? ' aria-current="true"' : ''}>${esc(g.label || g.flow)}</a>`).join('')}</nav>
    <div class="proto">
      <div class="proto-main">
        <div class="crumb"><span>${esc(s.name)}</span><span class="sep">›</span><span>${esc(sc.group.label || sc.group.flow)}</span>${DATA.empty ? '' : `<span class="sep">›</span><b>Step ${sc.step} of ${list.length}</b>`}</div>
        ${DATA.empty ? `<div class="slot"><b>Design goes here</b><span>Connect Figma to load the screens for ${esc(sc.group.label || sc.group.flow)}.</span></div>` : `<div class="proto-nav"><button type="button" class="btn" id="p-back"${state.history.length?'':' disabled'}>← Back</button><button type="button" class="btn" id="p-next"${idx < list.length-1?'':' disabled'}>Next →</button><span class="spacer"></span><span class="note">${hs.length ? hs.length + (hs.length===1?' clickable area':' clickable areas') + ' on this screen' : 'End of this path'}</span><button type="button" class="btn small" id="p-restart">Restart flow</button></div>
        <article class="screen${state.showHot?' show-hot':''}" data-screen="${sc.id}"><div class="screen-head"><span class="step">${String(sc.step).padStart(2,'0')}</span><span class="name">${esc(sc.name)}</span></div>${shotHtml(sc)}</article>
        ${hs.length ? '' : `<div class="end-note">This screen ends the path. Use Back, pick another step on the left, or Restart flow.</div>`}`}
      </div></div>`;
}
function goTo(id, push){ if(!screenOf(id)) return; if(push && state.current && state.current !== id) state.history.push(state.current); state.current = id; render(); $('#stage').scrollTop = 0; }
function applyPins(){
  $$('.pins').forEach(p => p.innerHTML = '');
  if(DATA.empty) return;
  $$('.screen').forEach(el => el.classList.toggle('picking', state.picking));
  const f = state.form;
  if(f.type === 'area' && f.screen && f.fx != null){ const el = $(`[data-screen="${CSS.escape(f.screen)}"] .pins`); if(el) el.innerHTML += `<span class="pin draft" style="left:${f.fx*100}%;top:${f.fy*100}%" title="New comment">+</span>`; }
  if(!state.panel) return;
  numbered(state.tab).forEach(c => { if(!c.screen) return; const el = $(`[data-screen="${CSS.escape(c.screen)}"] .pins`); if(!el) return;
    el.innerHTML += `<button type="button" class="pin${state.tab==='stake'?' stake':''}${c.id===state.selected?' on':''}" data-pin="${c.id}" style="left:${(c.fx??0.5)*100}%;top:${(c.fy??0.06)*100}%" aria-label="Comment ${c.n}">${c.n}</button>`; });
}
function applyHighlight(scroll){
  $$('.screen.hl').forEach(el => el.classList.remove('hl'));
  if(!state.panel || !state.selected) return;
  const c = listFor(state.tab).find(c => c.id === state.selected); if(!c || !c.screen) return;
  if(state.view === 'proto' && c.screen !== state.current){ state.history.push(state.current); state.current = c.screen; renderStage(); renderBar(); }
  const el = $(`[data-screen="${CSS.escape(c.screen)}"]`); if(!el) return; el.classList.add('hl');
  if(scroll) el.scrollIntoView({ block:'start', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
}

/* ---------- bar ---------- */
function renderBar(){
  const fs = $('#flow-select'); fs.innerHTML = DATA.sections.map(s => `<option value="${s.id}">${esc(s.name)}</option>`).join(''); fs.value = state.sectionId;
  const us = $('#update-select'); us.innerHTML = DATA.updates.map((u,i) => `<option value="${u.id}">${i===0?'Last update: ':''}${esc(fmtDate(u.date))}</option>`).join(''); us.value = state.updateId;
  $$('#bar [data-role]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.role === state.role)));
  $('#comments-btn').setAttribute('aria-pressed', String(state.panel));
  $('#comments-badge').textContent = visible('ux').length + visible('stake').length;
  const cur = upd().date; const news = sec().notes.filter(n => n.date === cur);
  const m = $('#changes-menu');
  m.innerHTML = `<h4>${updIdx()===0?'New in the last update':'New on '+esc(fmtDate(cur))}</h4>` + (news.length ? `<ul class="changes">${news.map(n => `<li data-goto-note="${n.id}"><span>${esc(n.text)}</span><span class="where">${esc(n.kind)} · ${esc((screenOf(n.screen)||{}).name || '')}</span></li>`).join('')}</ul>` : `<div class="changes empty">No dated notes on this flow for this update. The screens shown are the current state of the Figma file.</div>`);
}

/* ---------- panel ---------- */
const panel = $('#panel');
function renderPanel(){
  panel.hidden = !state.panel; if(!state.panel) return;
  const uxN = visible('ux').length, stN = visible('stake').length;
  const all = listFor(state.tab); const live = numbered(state.tab); const dismissed = all.filter(c => c.dismissed);
  const cats = state.tab === 'ux' ? ['All','Flow update','Design Insight'].concat(CATEGORIES.filter(c => c !== 'General')) : ['All','General','Specific area'].concat(CATEGORIES.filter(c => c !== 'General'));
  const filtered = live.filter(c => state.filter === 'All' || c.category === state.filter || (state.filter === 'General' && !c.screen) || (state.filter === 'Specific area' && !!c.screen));
  const canPost = (state.tab === 'ux' && roleIsDesigner()) || (state.tab === 'stake' && !roleIsDesigner());
  panel.innerHTML = `<div class="panel-head"><div class="grow"><h2>Comments</h2><div class="sub">${esc(sec().name)} · ${esc(fmtDate(upd().date))} · viewing as ${roleIsDesigner()?'Designer':'Stakeholder'}</div></div>
      <button type="button" class="btn small" id="copy-btn" title="Copy open comments as Markdown">Copy</button><button type="button" class="x" id="panel-close" aria-label="Close panel">✕</button></div>
    <div class="tabs" role="tablist"><button type="button" role="tab" data-tab="ux" aria-selected="${state.tab==='ux'}">Insight from UX <span class="count">${uxN}</span></button><button type="button" role="tab" data-tab="stake" aria-selected="${state.tab==='stake'}">Stakeholder feedback <span class="count">${stN}</span></button></div>
    <div class="chips">${cats.map(c => `<button type="button" class="chip" data-filter="${esc(c)}" aria-pressed="${state.filter===c}">${esc(c)}</button>`).join('')}</div>
    <div class="panel-body">${filtered.length ? filtered.map(c => renderComment(c,false)).join('') : `<div class="empty">${live.length ? 'Nothing in this category.' : (state.tab==='ux' ? 'No insights for this update yet.' : 'No feedback on this update yet.')}</div>`}
      ${(dismissed.length && roleIsDesigner()) ? `<details class="dismissed"><summary>Dismissed (${dismissed.length})</summary><div class="list">${dismissed.map(c => renderComment(Object.assign({n:'·'},c),true)).join('')}</div></details>` : ''}</div>
    ${canPost ? renderForm() : ''}
    <div class="panel-foot"><span>${DATA.empty ? 'Screens are hidden until Figma is connected. ' : 'UX insights come from the Figma file. '}Posts and dismissals are saved in this browser only.</span><button type="button" class="link-btn" id="reset-btn">Reset</button></div>`;
  if(canPost){ $('#f-name').value = state.form.name; $('#f-text').value = state.form.text; syncPost(); }
}
function renderComment(c, isDismissed){
  const linked = !!c.screen, sel = c.id === state.selected && !isDismissed;
  const rolePill = c.role === 'Stakeholder' ? '<span class="pill stake">Stakeholder</span>' : '<span class="pill ux">UX</span>';
  const statusPill = { open:'<span class="pill open">Open</span>', progress:'<span class="pill progress">In progress</span>', resolved:`<span class="pill resolved">Resolved${c.resolvedIn?' in '+esc(fmtDate(c.resolvedIn)):''}</span>` }[c.status];
  const actions = roleIsDesigner() ? (isDismissed ? `<button type="button" class="link-btn" data-restore="${c.id}">Restore</button>`
    : `<label class="sr-only" for="st-${c.id}">Status</label><select class="ctl" id="st-${c.id}" data-status="${c.id}"><option value="open"${c.status==='open'?' selected':''}>Open</option><option value="progress"${c.status==='progress'?' selected':''}>In progress</option><option value="resolved"${c.status==='resolved'?' selected':''}>Resolved</option></select><button type="button" class="link-btn" data-dismiss="${c.id}">Dismiss</button>`) : '';
  const scr = linked ? screenOf(c.screen) : null;
  return `<div class="comment${linked&&!isDismissed?' linked':''}${sel?' selected':''}${isDismissed?' dim':''}${c.isNew?' new':''}" data-comment="${c.id}">
    <div class="num${sel?' on':''}${linked?'':' general'}">${linked?c.n:'·'}</div>
    <div class="c-meta"><b>${esc(c.author)}</b>${rolePill}${c.date?`<span>${esc(fmtDate(c.date))}</span>`:''}${c.isNew?'<span class="pill newpill">New this update</span>':''}${statusPill}</div>
    <div class="c-text">${esc(c.text)}</div>
    <div class="c-tags">${scr?`<span class="tag area" title="${esc(scr.name)}">${String(scr.step).padStart(2,'0')} · ${esc(scr.name)}</span>`:'<span class="tag">General</span>'}${(!scr && c.category === 'General') ? '' : `<span class="tag">${esc(c.category)}</span>`}</div>
    ${actions?`<div class="c-actions">${actions}</div>`:''}</div>`;
}
function renderForm(){
  const f = state.form; const role = state.tab === 'ux' ? 'UX' : 'Stakeholder'; const scr = f.screen ? screenOf(f.screen) : null;
  return `<form class="cform" id="cform"><h3>Add ${role==='UX'?'an insight':'feedback'} as ${role}</h3>
    <div class="two"><div><label class="sr-only" for="f-name">Your name</label><input id="f-name" placeholder="Your name"></div><div><label class="sr-only" for="f-cat">Category</label><select id="f-cat">${CATEGORIES.map(c => `<option${f.category===c?' selected':''}>${c}</option>`).join('')}</select></div></div>
    <label class="sr-only" for="f-text">Comment</label><textarea id="f-text" placeholder="What should change, and why?"></textarea>
    <div class="area-pick">${DATA.empty ? '' : `<div class="seg" role="group" aria-label="Comment type"><button type="button" data-ftype="general" aria-pressed="${f.type==='general'}">General</button><button type="button" data-ftype="area" aria-pressed="${f.type==='area'}">Specific spot</button></div>`}
      ${f.type==='area' ? (scr ? `<span class="tag area" title="${esc(scr.name)}">${String(scr.step).padStart(2,'0')} · ${esc(scr.name)}</span><button type="button" class="link-btn" id="pick-change">Change</button><button type="button" class="link-btn" id="pick-remove">Remove</button>` : `<button type="button" class="btn small" id="pick-area">${state.picking?'Click a spot on a screen…':'Pick a spot on a screen'}</button>`) : ''}</div>
    <div class="foot"><button type="submit" class="btn primary" id="post-btn" disabled>Post</button><span class="toast" id="post-toast"></span></div></form>`;
}
function syncPost(){ const b = $('#post-btn'); if(!b) return; const f = state.form; b.disabled = !(f.name.trim() && f.text.trim() && (f.type === 'general' || f.screen)); }
function render(){ renderStage(); renderBar(); renderPanel(); }
function hint(t){ const h = $('#hint'); h.textContent = t || ''; h.hidden = !t; }
function edit(id, patch){ state.edits[id] = Object.assign({}, state.edits[id] || {}, patch); save(); }
function select(id, scroll){ state.selected = state.selected === id ? null : id; render(); applyHighlight(scroll); const el = $(`[data-comment="${CSS.escape(id)}"]`, panel); if(el && state.selected) el.scrollIntoView({ block:'nearest' }); }

/* ---------- events ---------- */
$('#changes-btn').addEventListener('click', () => { const m = $('#changes-menu'); m.hidden = !m.hidden; $('#changes-btn').setAttribute('aria-expanded', String(!m.hidden)); });
document.addEventListener('click', e => { if(!e.target.closest('.menu-wrap')){ $('#changes-menu').hidden = true; $('#changes-btn').setAttribute('aria-expanded','false'); } });
$('#changes-menu').addEventListener('click', e => { const li = e.target.closest('[data-goto-note]'); if(!li) return; state.panel = true; state.tab = 'ux'; state.filter = 'All'; state.selected = null; select(li.dataset.gotoNote, true); });
$('#bar').addEventListener('click', e => {
  const b = e.target.closest('button[data-role]'); if(b){ state.role = b.dataset.role; state.selected = null; state.picking = false; hint(''); save(); render(); return; }
});
$('#flow-select').addEventListener('change', e => { state.sectionId = e.target.value; state.selected = null; state.picking = false; state.form.screen = null; state.current = null; state.history = []; hint(''); render(); $('#stage').scrollTop = 0; });
document.addEventListener('keydown', e => {
  if(state.view !== 'proto' || e.target.matches('input, textarea, select')) return;
  const list = allScreens(); const i = list.findIndex(x => x.id === state.current);
  if(e.key === 'ArrowRight' && i < list.length - 1) goTo(list[i+1].id, true);
  if(e.key === 'ArrowLeft'){ if(state.history.length) goTo(state.history.pop(), false); else if(i > 0) goTo(list[i-1].id, false); }
});
$('#update-select').addEventListener('change', e => { state.updateId = e.target.value; state.selected = null; state.picking = false; state.form.screen = null; hint(''); render(); });
$('#comments-btn').addEventListener('click', () => { state.panel = !state.panel; state.selected = null; state.picking = false; hint(''); render(); });
document.addEventListener('keydown', e => { if(e.key === 'Escape' && state.picking){ state.picking = false; hint(''); render(); } });
$('#stage').addEventListener('click', e => {
  const pin = e.target.closest('[data-pin]'); if(pin){ if(!state.panel){ state.panel = true; } state.selected = null; select(pin.dataset.pin, false); return; }
  const g = e.target.closest('[data-goto-group]'); if(g){ e.preventDefault(); const t = $('#g'+g.dataset.gotoGroup); if(t) t.scrollIntoView({ block:'start', behavior:'smooth' }); return; }
  const jump = e.target.closest('[data-jump]'); if(jump){ e.preventDefault(); goTo(jump.dataset.jump, true); return; }
  if(e.target.closest('#p-next')){ const list = allScreens(); const i = list.findIndex(x => x.id === state.current); if(i < list.length-1) goTo(list[i+1].id, true); return; }
  if(e.target.closest('#p-back')){ if(state.history.length) goTo(state.history.pop(), false); return; }
  if(e.target.closest('#p-restart')){ state.history = []; goTo(firstScreen(), false); return; }
  if(!state.picking){
    const hot = e.target.closest('.hot'); if(hot){ goTo(hot.dataset.to, true); return; }
    const shot = e.target.closest('.shot'); if(shot && state.view === 'proto'){ const sc = shot.closest('.screen'); sc.classList.remove('flash'); void sc.offsetWidth; sc.classList.add('flash'); setTimeout(() => sc.classList.remove('flash'), 900); }
    return;
  }
  const shot = e.target.closest('.shot'); if(!shot) return;
  const r = shot.getBoundingClientRect(); const f = state.form;
  f.screen = shot.closest('[data-screen]').dataset.screen; f.fx = Math.round(((e.clientX - r.left) / r.width) * 1000) / 1000; f.fy = Math.round(((e.clientY - r.top) / r.height) * 1000) / 1000;
  state.picking = false; hint(''); render();
});
panel.addEventListener('click', e => {
  const t = e.target;
  if(t.closest('#panel-close')){ state.panel = false; state.picking = false; hint(''); render(); return; }
  const tab = t.closest('[data-tab]'); if(tab){ state.tab = tab.dataset.tab; state.selected = null; state.filter = 'All'; state.picking = false; hint(''); render(); return; }
  const chip = t.closest('[data-filter]'); if(chip){ state.filter = chip.dataset.filter; render(); return; }
  const dis = t.closest('[data-dismiss]'); if(dis){ edit(dis.dataset.dismiss, { dismissed:true }); if(state.selected === dis.dataset.dismiss) state.selected = null; render(); return; }
  const res = t.closest('[data-restore]'); if(res){ edit(res.dataset.restore, { dismissed:false }); render(); return; }
  const ft = t.closest('[data-ftype]'); if(ft){ state.form.type = ft.dataset.ftype; if(state.form.type === 'general'){ state.form.screen = null; state.picking = false; hint(''); } render(); return; }
  if(t.closest('#pick-area') || t.closest('#pick-change')){ state.picking = true; hint('Click the spot on a screen this comment is about. Esc to cancel.'); render(); return; }
  if(t.closest('#pick-remove')){ state.form.screen = null; render(); return; }
  if(t.closest('#copy-btn')){ copySummary(t.closest('#copy-btn')); return; }
  if(t.closest('#reset-btn')){ state.posted = {}; state.edits = {}; save(); state.selected = null; render(); return; }
  const cm = t.closest('.comment.linked'); if(cm && !t.closest('select') && !t.closest('button') && !t.closest('a')){ select(cm.dataset.comment, true); }
});
panel.addEventListener('change', e => { const s = e.target.closest('[data-status]'); if(s){ edit(s.dataset.status, { status:s.value, resolvedIn: s.value === 'resolved' ? upd().date : null }); render(); } if(e.target.id === 'f-cat') state.form.category = e.target.value; });
panel.addEventListener('input', e => { if(e.target.id === 'f-name') state.form.name = e.target.value; if(e.target.id === 'f-text') state.form.text = e.target.value; syncPost(); });
panel.addEventListener('submit', e => {
  e.preventDefault(); const f = state.form; if(!(f.name.trim() && f.text.trim() && (f.type === 'general' || f.screen))) return;
  const key = state.sectionId + '|' + state.updateId; const list = state.posted[key] = state.posted[key] || { ux:[], stake:[] };
  const c = { id:'p-'+Date.now(), author:f.name.trim(), role: state.tab === 'ux' ? 'UX' : 'Stakeholder', date: todayIso(), screen: f.type === 'area' ? f.screen : null, fx: f.fx, fy: f.fy, category: f.category, status:'open', text: f.text.trim() };
  list[state.tab].unshift(c); save();
  state.form = { name:f.name, text:'', category:'General', type:'general', screen:null, fx:null, fy:null };
  state.selected = c.screen ? c.id : null; render(); applyHighlight(true); const toast = $('#post-toast'); if(toast) toast.textContent = 'Posted.';
});
function copySummary(btn){
  const lines = [`# ${sec().name} · ${fmtDate(upd().date)}`, ''];
  [['Insight from UX','ux'],['Stakeholder feedback','stake']].forEach(([title, tab]) => { const list = visible(tab); lines.push(`## ${title} (${list.length})`);
    list.forEach(c => { const s = c.screen ? screenOf(c.screen) : null; lines.push(`- [${c.status==='resolved'?'x':' '}] ${s?'**'+s.name+'** · ':''}${c.text.replace(/\n/g,' ')} _(${c.author}, ${c.category})_`); }); lines.push(''); });
  const md = lines.join('\n'); const done = () => { btn.textContent = 'Copied'; setTimeout(() => btn.textContent = 'Copy', 1500); };
  const fb = () => { const ta = document.createElement('textarea'); ta.value = md; ta.style.position = 'fixed'; ta.style.opacity = '0'; document.body.appendChild(ta); ta.select(); try{ document.execCommand('copy'); done(); }catch(e){ btn.textContent = 'Copy failed'; } document.body.removeChild(ta); };
  if(navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(md).then(done).catch(fb); else fb();
}
render();
</script>
'''
out = PAGE.replace('__DATA__', DATA_JS)
open(os.path.join(HERE, '..', 'index.html'), 'w').write(out)
print('wrote', len(out), 'bytes')
