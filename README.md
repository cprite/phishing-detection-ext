<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a name="readme-top"></a>

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![GPL-2.0 license][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]


<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/cprite/phishing-detection-ext">
    <img src="images/logo.png" alt="Logo" width="200" height="200">
  </a>

  <p align="center">
    <br />
    <br />
    <br />
    <a href="https://github.com/cprite/phishing-detection-ext/issues">Report Bug</a>
    ·
    <a href="https://github.com/cprite/phishing-detection-ext/issues">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#disclaimer">[!] Disclaimer</a></li>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#retrain-the-model">Retrain the Model</a></li>
      </ul>
    </li>
    <li><a href="#how-it-works">How It Works</a></li>
    <li><a href="#model-performance">Model Performance</a></li>
    <li><a href="#contributing">Contributing</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

**No Phishing** is a self-contained Chrome extension that detects phishing URLs in real time. The classifier is a **K-Nearest-Neighbours model implemented in pure JavaScript** — no companion server, no ONNX, no WebAssembly, no data sent anywhere. It achieves **89.4% test accuracy** on 11 browser-computable features, and because KNN is instance-based it **learns in the browser**: your corrections become new data points that immediately affect future predictions.

### Disclaimer
This extension is intended as a supplementary tool for online safety. While it demonstrates high accuracy, it is not infallible. As the developer, I am not a certified cybersecurity professional, and the extension could make errors. Users are advised to exercise caution and judgment. By using "No Phishing," you acknowledge and accept responsibility for your online safety.

### Built With

* [![Python](https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue)](https://www.python.org)
* [![JavaScript](https://img.shields.io/badge/JavaScript-323330?style=for-the-badge&logo=javascript&logoColor=F7DF1E)](https://www.javascript.com/)
* [![HTML](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)](https://html.spec.whatwg.org/)
* [![Jupyter](https://img.shields.io/badge/Jupyter-F37626.svg?&style=for-the-badge&logo=Jupyter&logoColor=white)](https://jupyterlab.readthedocs.io/en/stable)
* [![Pandas](https://img.shields.io/badge/Pandas-2C2D72?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
* [![NumPy](https://img.shields.io/badge/Numpy-777BB4?style=for-the-badge&logo=numpy&logoColor=white)](https://numpy.org/)
* [![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
* [![Google Chrome](https://img.shields.io/badge/Google_chrome-4285F4?style=for-the-badge&logo=Google-chrome&logoColor=white)](https://www.google.com/chrome/)
* [![VScode](https://img.shields.io/badge/VSCode-0078D4?style=for-the-badge&logo=visual%20studio%20code&logoColor=white)](https://code.visualstudio.com/)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started

No Python, no server, no setup. Just load the extension:

1. Clone the repo
   ```sh
   git clone https://github.com/cprite/phishing-detection-ext.git
   ```
2. Load the extension in Google Chrome
   - Open Google Chrome and navigate to `chrome://extensions/`.
   - Enable **Developer mode** (top-right toggle).
   - Click **Load unpacked** and select the cloned `phishing-detection-ext` directory.
   - The extension appears in your Chrome toolbar.

3. Activate the extension
   - Click the extension icon and toggle it **ON**.
   - The extension will now score every page you visit locally and redirect phishing pages to a warning screen.

### Rebuild the Seed Model

The seed dataset (`saved_models/seed_model.json` — scaled training points, labels and frozen scaler parameters) is committed and ready to use. To regenerate it:

1. Download the dataset from Kaggle:  
   [Web page phishing detection dataset](https://www.kaggle.com/datasets/shashwatwork/web-page-phishing-detection-dataset/data)  
   Save it as `raw_data/dataset_phishing.csv`.

2. Install build dependencies and run:
   ```sh
   pip install -r requirements.txt
   python export_model.py
   ```
   This overwrites `saved_models/seed_model.json` and prints the KNN accuracy.

The original 22-feature KNN baseline and browser feature-selection rationale are documented in `cyberguard_phishing_detection.ipynb`.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- HOW IT WORKS -->
## How It Works

Everything runs locally in your browser. No server, no network calls, no data leaves your device.

**Content script** (`extension/content.js`) — injected into every http/https page at `document_idle`. Sends the current URL and hyperlink count (`document.querySelectorAll('a').length`) to the service worker.

**Service worker** (`extension/background.js`) — receives the page report, extracts 11 features via `extension/features.js`, scales them with the frozen scaler and classifies with `extension/knn.js` over the merged seed + feedback dataset (`extension/storage.js`). If phishing, it redirects the tab to the built-in warning page.

**KNN classifier** (`extension/knn.js`) — a pure-JS port of scikit-learn's `KNeighborsClassifier(n_neighbors=3, metric="manhattan")` plus `MinMaxScaler.transform`. Classification is a majority vote of the 3 nearest seed points. Verified to match scikit-learn's predictions on 99.95% of the test set.

**Seed dataset** (`saved_models/seed_model.json`) — the scaled training points, labels and frozen scaler parameters, exported by `export_model.py`. ~7 700 points from the [Hannousse & Yahiouche dataset](https://www.kaggle.com/datasets/shashwatwork/web-page-phishing-detection-dataset/data) (≈9 600 samples after cleaning).

**Trusted sites** — clicking **Proceed** on a warning adds that page's hostname to a local trusted list (`chrome.storage.local`). Pages on a trusted hostname are **never blocked**, but in the open-source build they are still scored silently in the background: a trusted host is treated as ground truth, so if the model ever flags one as phishing that verdict is fed back as a `legitimate` point automatically (no warning, no prompt). Manage (and remove) trusted sites from the extension popup. The list never leaves your device.

**Vercel lookalike detector** (`extension/lookalike.js`) — a deterministic rule that runs alongside the KNN. The lexical model has a blind spot on short, clean-looking phishing hosted on free deploy platforms (e.g. `messenger-clone-delta-two.vercel.app`, `toki-gov-tr-17.vercel.app`). When a hostname is on a Vercel deploy domain (`*.vercel.app`, legacy `*.now.sh`) **and** its subdomain impersonates a known brand or carries a credential-harvest keyword (`login`, `verify`, `secure`, `giris`, …), the page is forced to a PHISHING verdict regardless of the KNN vote, and the warning shows the reason. Brand matching is label-boundary aware so ambiguous short tokens don't false-fire (`ups` inside `startups`, `gov` inside `governance`). On a 25-URL live sample this lifted overall accuracy from 84% to 92% and phishing recall from 73% to 87% with no new false positives.

**The 11 features** — 10 lexical features derived from the URL string (length, character counts, digit ratio, suspicious-token hits) plus the page hyperlink count. WHOIS lookups, redirect-history probes, and word-length features that require a public-suffix-aware tokenizer are all omitted — they either cannot be computed client-side or cannot be reproduced in JS with exact parity to the training data. Feature formulas are verified to produce 800/800 exact-match parity with the training dataset columns.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- SELF-LEARNING -->
## Self-Learning (open-source build)

KNN is instance-based — it classifies by comparing against stored points — so **adding a labelled point *is* retraining**. There's no offline step and no model file to rebuild: corrections take effect on the very next page you visit.

Your corrections are saved as scaled feature points in `chrome.storage.local` (`feedback_points`) and merged with the seed dataset at every inference. Two triggers (open-source build only):

- Clicking **Proceed** on a warning adds the page as a `legitimate` point (a false positive the model got wrong).
- Visiting a **trusted** host that the model flags as phishing adds it as a `legitimate` point automatically and silently — the trusted list is the source of truth, so a flag there is a correction signal.
- The popup's **Mark this site as phishing** button adds the current tab as a `phishing` point (a page the model missed).

Everything stays on your device. (This is **disabled in the Chrome Web Store build** — see [Builds](#builds).)

<a name="builds"></a>
### Builds

The **repository is the open-source build** (`extension/config.js` → `IS_OSS_BUILD = true`): the self-learning features above are included.

The **Chrome Web Store build** strips them. Generate it with:

```sh
python build_cws.py
```

This writes `dist/cws/` (load it to verify) and `dist/no-phishing-cws.zip` (upload it). It flips `IS_OSS_BUILD = false` — hiding the "Mark as phishing" button and stopping "Proceed" from adding points, so the store build never collects feedback — and leaves the Python scripts, dataset and docs out of the package.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MODEL PERFORMANCE -->
## Model Performance

Results on the held-out test set (20% split, stratified, `random_state=42`):

| Model | Features | Test Accuracy | Phishing Precision | Phishing Recall |
|-------|----------|:---:|:---:|:---:|
| KNN (k=3, manhattan) — previous server build | 22 (incl. WHOIS) | 92.65% | 93.98% | 90.89% |
| **KNN (k=3, manhattan) in JS — this build** | **11 (browser-only)** | **89.42%** | **88.55%** | **90.15%** |

The browser build trades ~3 points of accuracy for two things the server build can't offer: it runs entirely client-side (no server, no ONNX, no WebAssembly), and it **learns from your corrections in real time** — every "Proceed" or "Mark as phishing" becomes a new KNN point. The JS classifier reproduces scikit-learn's predictions on 99.95% of the test set.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/cprite/phishing-detection-ext.svg?style=for-the-badge
[contributors-url]: https://github.com/cprite/phishing-detection-ext/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/cprite/phishing-detection-ext.svg?style=for-the-badge
[forks-url]: https://github.com/cprite/phishing-detection-ext/network/members
[stars-shield]: https://img.shields.io/github/stars/cprite/phishing-detection-ext.svg?style=for-the-badge
[stars-url]: https://github.com/cprite/phishing-detection-ext/stargazers
[issues-shield]: https://img.shields.io/github/issues/cprite/phishing-detection-ext.svg?style=for-the-badge
[issues-url]: https://github.com/cprite/phishing-detection-ext/issues
[license-shield]: https://img.shields.io/github/license/cprite/phishing-detection-ext.svg?style=for-the-badge
[license-url]: https://github.com/cprite/phishing-detection-ext/blob/master/LICENSE.md
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/niknmirosh
