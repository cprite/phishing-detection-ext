/*
 * config.js — build-time configuration, loaded first in every context
 * (service worker via importScripts, popup/warning pages via <script>).
 *
 * IS_OSS_BUILD gates the open-source self-learning feedback features:
 * feedback collection, the popup's "Mark as phishing" / "Export feedback"
 * buttons, and recording a "legitimate" correction when the user proceeds past
 * a warning. The Chrome Web Store build sets this to false (see build_cws.py),
 * which strips all of the above — the store build never collects feedback.
 */
var IS_OSS_BUILD = true;

// Expose as a global for both service-worker and page contexts.
if (typeof self !== "undefined") self.IS_OSS_BUILD = IS_OSS_BUILD;
