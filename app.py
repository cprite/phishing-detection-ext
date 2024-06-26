from libs.features_comp import *
from tensorflow.keras.models import load_model
import pandas as pd
import numpy as np
import os
from tqdm import tqdm
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

functions = ['length_url', 'length_hostname', 'ip', 'nb_dots', 'nb_hyphens', 'nb_at', 'nb_qm', 'nb_and', 'nb_or', 'nb_eq', 'nb_underscore', 'nb_tilde', 'nb_percent', 'nb_slash', 'nb_star', 'nb_colon', 'nb_comma', 'nb_semicolon', 'nb_dollar', 'nb_space', 'nb_www', 'nb_com', 'nb_dslash', 'http_in_path', 'https_token', 'ratio_digits_url', 'ratio_digits_host', 'punycode', 'check_port', 'tld_in_path', 'tld_in_subdomain', 'abnormal_subdomain', 'nb_subdomains', 'prefix_suffix', 'random_domain', 'shortening_service', 'path_extension', 'nb_redirection', 'nb_external_redirection', 'length_words_raw', 'char_repeat', 'shortest_words_raw', 'shortest_word_host', 'shortest_word_path', 'longest_words_raw', 'longest_word_host', 'longest_word_path', 'avg_words_raw', 'avg_word_host', 'avg_word_path', 'suspecious_tld', 'nb_hyperlinks', 'ratio_intHyperlinks', 'ratio_extHyperlinks', 'ratio_nullHyperlinks', 'nb_extCSS', 'ratio_intRedirection', 'ratio_extRedirection', 'ratio_intErrors', 'ratio_extErrors', 'login_form', 'external_favicon', 'links_in_tags', 'submit_email', 'ratio_intMedia', 'ratio_extMedia', 'sfh', 'iframe', 'popup_window', 'safe_anchor', 'onmouseover', 'right_clic', 'empty_title', 'domain_in_title', 'domain_with_copyright', 'whois_registered_domain', 'domain_registration_length', 'domain_age', 'google_index']

app = Flask(__name__)
CORS(app)

def get_features(url, functions=functions):

    if url.startswith('chrome://'):
        return [0] * len(functions)  # Return a default feature set or handle as needed

    features = []

    # Call each function with an  URL
    for function in tqdm(functions):
        result = globals()[function](url)

        if result == True:
            result = 1
        elif result == False or result == None:
            result = 0

        features.append(result)

    print(features)

    return features


def prob(features):

    # preprocessed features
    features = list(map(float, features))
    features_array = np.array(features).reshape(1, -1)

    print(features_array)

    # load pre-trained model
    model = load_model('saved_models/model_91.h5')

    # predict
    probability = model.predict(features_array)[0][0]

    print(model.predict(features_array))

    return probability


def get_class(prob):

    print(prob)

    if prob >= 0.5:
        return 'PHISHING'
    elif prob < 0.5:
        return 'LEGITIMATE'


@app.route('/check_url', methods=['POST'])
def check_url():
    data = request.json
    url = data['url']

    print(url)

    # Process the URL
    features = get_features(url)
    probability = prob(features)
    decision = get_class(probability)

    return jsonify({"decision": decision})

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5030))
    app.run(host='0.0.0.0', port=port)

""" TESTING SECTION """
# url = str(input('Enter url:\n'))

# features = get_features(url)
# probability = prob(features)
# prediction = get_class(probability)

# print(f'The url {url} is {prediction}')
