from libs.features_comp import *
from tensorflow.keras.models import load_model
from sklearn.preprocessing import StandardScaler
import pandas as pd
import numpy as np

functions = ['length_url', 'length_hostname', 'ip', 'nb_dots', 'nb_hyphens', 'nb_at', 'nb_qm', 'nb_and', 'nb_or', 'nb_eq', 'nb_underscore', 'nb_tilde', 'nb_percent', 'nb_slash', 'nb_star', 'nb_colon', 'nb_comma', 'nb_semicolon', 'nb_dollar', 'nb_space', 'nb_www', 'nb_com', 'nb_dslash', 'http_in_path', 'https_token', 'ratio_digits_url', 'ratio_digits_host', 'punycode', 'port', 'tld_in_path', 'tld_in_subdomain', 'abnormal_subdomain', 'nb_subdomains', 'prefix_suffix', 'random_domain', 'shortening_service', 'path_extension', 'nb_redirection', 'nb_external_redirection', 'length_words_raw', 'char_repeat', 'shortest_words_raw', 'shortest_word_host', 'shortest_word_path', 'longest_words_raw', 'longest_word_host', 'longest_word_path', 'avg_words_raw', 'avg_word_host', 'avg_word_path', 'suspecious_tld', 'nb_hyperlinks', 'ratio_intHyperlinks', 'ratio_extHyperlinks', 'ratio_nullHyperlinks', 'nb_extCSS', 'ratio_intRedirection', 'ratio_extRedirection', 'ratio_intErrors', 'ratio_extErrors', 'login_form', 'external_favicon', 'links_in_tags', 'submit_email', 'ratio_intMedia', 'ratio_extMedia', 'sfh', 'iframe', 'popup_window', 'safe_anchor', 'onmouseover', 'right_clic', 'empty_title', 'domain_in_title', 'domain_with_copyright', 'whois_registered_domain', 'domain_registration_length', 'domain_age', 'google_index']


def get_features(url, functions=functions):
    features = []
    
    # Call each function with an  URL
    for function in functions:
        result = globals()[function](url)
        
        if result == True:
            result = 1
        elif result == False or result == None:
            result = 0
            
        features.append(result)
        
    return features


def prob(features):
    
    # preprocessed features
    features = list(map(float, features))
    features_array = np.array(features).reshape(1, -1)
    
    scaler = StandardScaler()
    features_preproc = scaler.fit_transform(features_array)
    
    # load pre-trained model
    model = load_model('saved_models/model_91.h5')
    
    # predict
    probability = model.predict(features_preproc)[0][0]
    return probability


def get_class(prob):
    if prob > 0.5:
        return 'PHISHING'
    return 'LEGITIMATE'



""" TESTING SECTION """
# url = str(input('Enter url:\n'))

# features = get_features(url)
# probability = prob(features)
# prediction = get_class(probability)

# print(f'The url {url} is {prediction}')

    
