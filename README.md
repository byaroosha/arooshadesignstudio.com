# Aroosha — AI works

A single self-contained webpage (`index.html`). No build step, no dependencies — everything (logo, fonts link, styles, scripts) is inside the one file.

---

## 1. Put it on GitHub

1. Create a new **public** repository (private repos need a paid plan for Pages).
2. Click **Add file → Upload files**, drag in `index.html` and `.nojekyll`, then **Commit**.
   - `.nojekyll` tells GitHub Pages to serve the files exactly as-is.

## 2. Turn on GitHub Pages

1. In the repo: **Settings → Pages**.
2. **Source:** "Deploy from a branch" → branch `main` → folder `/ (root)` → **Save**.
3. Wait ~1 minute. Your site is live at:
   `https://<your-username>.github.io/<repo-name>/`

## 3. Connect your custom domain

1. Buy a domain (~$10–15/yr) — e.g. Namecheap, Cloudflare, Porkbun.
2. In **Settings → Pages → Custom domain**, type your domain (e.g. `yourdomain.com`) and **Save**.
   GitHub adds a `CNAME` file to the repo automatically — don't create one by hand.
3. At your domain registrar's DNS settings, add these records:

   **Apex domain (`yourdomain.com`) — four A records:**
   ```
   185.199.108.153
   185.199.109.153
   185.199.110.153
   185.199.111.153
   ```
   (Optional IPv6 — four AAAA records:)
   ```
   2606:50c0:8000::153
   2606:50c0:8001::153
   2606:50c0:8002::153
   2606:50c0:8003::153
   ```

   **`www` subdomain — one CNAME record:**
   ```
   Name: www   →   Value: <your-username>.github.io
   ```
   GitHub recommends setting up BOTH apex + www; it auto-redirects between them.

4. Back in **Settings → Pages**, tick **Enforce HTTPS** once the certificate is ready
   (can take a few minutes to a few hours).

> DNS changes can take up to 24 hours to fully propagate. If the domain doesn't
> resolve immediately, that's normal — give it time.

## 4. Updating later

Edit `index.html`, then **Upload files** over the old one (or push the change).
GitHub Pages redeploys automatically within a minute or two.

---

### Switching hosts is easy
Because the site lives in this repo, you can connect the SAME repo to Netlify,
Vercel, or Cloudflare Pages anytime ("Import from GitHub") and they'll auto-deploy
on every change. GitHub stays your single source of truth.
