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

**No Phishing** is a browser extension that uses machine learning to detect phishing URLs in real time and block them before you land on the page. It achieves **92.7% test accuracy** using a K-Nearest Neighbours classifier trained on 22 URL-derived features. The extension is designed for Google Chrome.

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
* [![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
* [![Google Chrome](https://img.shields.io/badge/Google_chrome-4285F4?style=for-the-badge&logo=Google-chrome&logoColor=white)](https://www.google.com/chrome/)
* [![VScode](https://img.shields.io/badge/VSCode-0078D4?style=for-the-badge&logo=visual%20studio%20code&logoColor=white)](https://code.visualstudio.com/)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started

1. Clone the repo
   ```sh
   git clone https://github.com/cprite/phishing-detection-ext.git
   cd phishing-detection-ext
   ```
2. Install the required dependencies
   ```sh
   pip install -r requirements.txt
   ```
3. Start the local inference server
   ```sh
   python app.py
   ```
   The server runs on `http://127.0.0.1:5030` and must be running for the extension to work.

4. Load the extension in Google Chrome
   - Open Google Chrome and navigate to `chrome://extensions/`.
   - Enable `Developer mode` by toggling the switch in the top-right corner.
   - Click `Load unpacked`.
   - Select the cloned `phishing-detection-ext` directory.
   - The extension will appear in your Chrome toolbar.

5. Activate the extension
   - Click the extension icon in the Chrome toolbar to toggle it **ON**.
   - The extension will now check every page you navigate to against the local server and redirect phishing pages to a warning screen.

### Retrain the Model

The pre-trained artifacts (`saved_models/knn_model.pkl`, `saved_models/scaler.pkl`, `saved_models/feature_names.json`) are committed and ready to use. To retrain from scratch:

1. Download the dataset from Kaggle:  
   [Web page phishing detection dataset](https://www.kaggle.com/datasets/shashwatwork/web-page-phishing-detection-dataset/data)  
   Save it as `raw_data/dataset_phishing.csv`.

2. Install training dependencies (included in `requirements.txt`) and run:
   ```sh
   python train.py
   ```
   This will overwrite the artifacts in `saved_models/` and print the final metrics.

The full training methodology is documented in `cyberguard_phishing_detection.ipynb`.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- HOW IT WORKS -->
## How It Works

The system has two parts:

**Extension (JavaScript)** — A Chrome Manifest V3 extension that fires on every completed page load. It POSTs the current tab's URL to the local Flask server. If the server responds `PHISHING`, the tab is redirected to a built-in warning page.

**Inference server (Python/Flask)** — `app.py` loads three artifacts produced by `train.py`:
- `knn_model.pkl` — a KNN classifier (k=3, Manhattan distance)
- `scaler.pkl` — a MinMaxScaler fitted on the training features
- `feature_names.json` — the ordered list of 22 features the model expects

On each `/check_url` request, `libs/features_comp.py` extracts 22 features from the URL (lexical features from the URL string, content features from the fetched page, and WHOIS features), scales them, and returns the classifier's decision.

**Feature selection** — The full Kaggle dataset has 87+ raw features. Training screens them down to 22 via four passes:
1. Remove highly correlated pairs (|r| > 0.75)
2. Remove near-zero variance features (var < 0.005)
3. Remove weak linear correlation with the target (|r| < 0.023)
4. Remove low Random Forest importance (< 0.005)

Three features available in the dataset (`web_traffic`, `google_index`, `page_rank`) are excluded at inference time because they require third-party APIs the extension cannot call.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MODEL PERFORMANCE -->
## Model Performance

Results on the held-out test set (20% split, stratified, `random_state=42`):

| Model               | Test Accuracy | CV Accuracy (5-fold) |
|---------------------|--------------|----------------------|
| KNN (k=3, manhattan) | **92.65%**  | 91.63% ± 0.67%      |
| Logistic Regression  | 89.79%       | 89.63% ± 0.18%      |

KNN classification report (test set, 1 919 samples):

|              | Precision | Recall | F1-score | Support |
|--------------|-----------|--------|----------|---------|
| Legitimate   | 0.91      | 0.94   | 0.93     | 975     |
| Phishing     | 0.94      | 0.91   | 0.92     | 944     |
| **Accuracy** |           |        | **0.93** | 1 919   |

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
