# Privacy Policy — No Phishing

_Last updated: 2026-06-18_

No Phishing is built so that **none of your browsing data ever leaves your device.**

## What the extension does

When protection is enabled, for each web page you visit the extension reads:

- the page **URL**, and
- the **number of links** (`<a>` tags) on the page.

From these it computes a small set of numeric features and runs them through a
machine-learning model that is **bundled inside the extension** and executed
locally in your browser (via WebAssembly). The model returns a single
"phishing" / "legitimate" decision. If a page is judged to be phishing, the
extension shows a warning page.

## What the extension does **not** do

- It does **not** send your URLs, page contents, or any other data to any
  server. There is no remote API, no analytics, and no telemetry.
- It does **not** make any network requests of its own.
- It does **not** collect, store, or share any personal information.
- It does **not** use cookies or track you across sites.

The only thing stored is a single on/off setting (`isEnabled`), kept in
Chrome's local extension storage on your device.

## Permissions

- **storage** — remembers whether protection is turned on.
- **offscreen** — runs the local ML model (WebAssembly) in a background document.
- **Access to web pages** (content script on `http`/`https`) — needed to read
  the current page's URL and link count in order to score it locally.

## Contact

Questions: open an issue at https://github.com/cprite/phishing-detection-ext
