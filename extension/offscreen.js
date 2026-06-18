/*
 * offscreen.js — runs onnxruntime-web (WASM) inside an offscreen document.
 *
 * Loads the bundled model once, then answers {action:"classify"} messages from
 * the service worker with a PHISHING / OK decision plus the phishing score.
 * Everything is local: model and WASM are packaged in the extension, no network.
 */

// onnxruntime-web must load its .wasm/.mjs from the bundled vendor folder,
// never from a CDN (Chrome Web Store forbids remotely hosted code).
ort.env.wasm.wasmPaths = chrome.runtime.getURL("extension/vendor/");
ort.env.wasm.numThreads = 1; // no SharedArrayBuffer / cross-origin isolation needed

// Create the inference session once; classify() awaits it so early messages queue.
const sessionPromise = (async () => {
  const url = chrome.runtime.getURL("saved_models/model.onnx");
  const buffer = await (await fetch(url)).arrayBuffer();
  return ort.InferenceSession.create(buffer, { executionProviders: ["wasm"] });
})();

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.target !== "offscreen" || msg.action !== "classify") return; // not ours
  (async () => {
    try {
      const session = await sessionPromise;
      const input = Float32Array.from(msg.features);
      const tensor = new ort.Tensor("float32", input, [1, input.length]);
      const feeds = {};
      feeds[session.inputNames[0]] = tensor;
      const out = await session.run(feeds);

      // skl2onnx classifier outputs: "label" (int64) + "probabilities".
      const labelName = session.outputNames.includes("label")
        ? "label" : session.outputNames[0];
      const label = Number(out[labelName].data[0]);

      let score = null;
      const probName = session.outputNames.find((n) => n !== labelName);
      if (probName && out[probName].data.length >= 2) {
        score = Number(out[probName].data[1]); // P(phishing)
      }
      sendResponse({ decision: label === 1 ? "PHISHING" : "OK", score });
    } catch (e) {
      // Fail open: never block a page because inference errored.
      sendResponse({ decision: "OK", error: String(e && e.message || e) });
    }
  })();
  return true; // keep the message channel open for the async sendResponse
});
