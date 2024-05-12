import re
import numpy as np
from tqdm import tqdm
from tensorflow.keras.models import load_model

from validation_features_1 import *
from validation_features_2 import *
from validation_features_3 import *


""" After a user leaves a report on a misclassified website, that URL 
is validated through 3 different models with different features """

def validate_report(url):
    
    probabilities = []

    for i in range(2, 4):
        print(f'----------- Validation model: {i} -----------')

        file_path = f'validation_features_{i}.py'
        with open(file_path, 'r') as file:
            content = file.read()

            pattern = r'def (\w+)\('
            functions = re.findall(pattern, content)

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
            
        features = list(map(float, features))
        features_array = np.array(features).reshape(1, -1)
        
        model = load_model(f'../saved_models/validation_model_{i}.h5')

        probability = model.predict(features_array)[0][0]
        probabilities.append(probability)
           
    mean = np.average(probabilities)
    
    print(probabilities)
    print(mean)
    
    return 'PHISHING' if mean > 0.6 else 'LEGITIMATE'


print(validate_report('https://www.kaggle.com/datasets/sauhardsaini/phishing-url-detection?select=Phishing.csv'))