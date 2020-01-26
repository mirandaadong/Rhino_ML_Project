"""
Trains a predictive model pipeline to predict lead score.
And Uses the model to generate lead score for new leads.

Inputs:
    - a CSV formatted file named `train.csv` located in this folder, which is the original dataset (with "is booking" information).
        - This dataset needs to be cleaned using the function `clean_train_data` in utils, before passed into the pipeline to train the model.
    - a CSV formatted file named `input_predict.csv` located in this folder, containing the last 12333 rows of the original dataset but without "is booking" column.
        bnn- This dataset needs to be cleaned using the function `clean_predict_data` in utils, before passed into the pipeline to generate lead score prediction.
Outputs:
Outputs:
    - a file named `output_predict.csv` that contains the same input file plus a new column "lead_score" with the predicted lead score
To run:
    $python predict.py
"""

import pandas as pd

from mlxtend.feature_selection import ColumnSelector
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from category_encoders import OneHotEncoder, BinaryEncoder 
from sklearn.base import BaseEstimator
from sklearn.feature_extraction.text import TfidfVectorizer, HashingVectorizer 
from mlxtend.preprocessing import DenseTransformer
from sklearn.pipeline import make_pipeline, make_union
from imblearn.ensemble import BalancedRandomForestClassifier

from utils import clean_train_data, clean_predict_data

import warnings
warnings.filterwarnings("ignore")


trainset_fname = "train.csv"
input_predictset_fname = "input_predict.csv"
output_predictset_fname = "output_predict.csv"


def train_pipeline(X, y):
    """
    Builds and trains a machine learning pipeline
    """
    
    numerical_col =  ['Num nights', 'Adults', 'Children', 'Session duration', 'Sessions', 
                      'Avg. session length (sec)', 'Avg. pageviews per session', 
                      'Pageviews', 'Hits', 'Created to arrival']
    categorical_col = ['Language', 'Website',  'Enquiry type', 'Enquiry status',
                       'Client budget','Country code','GA source',
                       'GA medium', 'Device', 'Created month']

    binary_col = ['Flights booked', 'User agent', 'User repeat', 'User referral']
    text_col = ['Click path','GA keyword']
    target = ['is booking']


    # Numerical pipeline

    numerical_pipeline = make_pipeline(
        ColumnSelector(cols=numerical_col),
        SimpleImputer(strategy="median"),
        StandardScaler()
    )

    # Categorical pipeline

    categorical_pipeline = make_pipeline(
        ColumnSelector(cols=categorical_col),
        SimpleImputer(strategy="constant",fill_value = 'None'),
        OneHotEncoder()
    )

    # Binary pipeline

    binary_pipeline = make_pipeline(
        ColumnSelector(cols = binary_col),
        SimpleImputer(strategy="most_frequent"),
        BinaryEncoder()
    )

    # Helper transformer for text pipelines

    class ReshapeTransformer(BaseEstimator):
        def __init__(self):
            self.is_fitted = False

        def transform(self, X, y=None):
            return X.reshape(X.shape[0],)

        def fit(self, X, y=None):
            self.is_fitted = True
            return self

        def fit_transform(self, X, y=None):
            return self.transform(X=X, y=y)

    # Text pipelines

    text_pipeline_1 = make_pipeline(    
        ColumnSelector(cols = ['Click path']),
        SimpleImputer(strategy = 'constant',fill_value = ''),
        ReshapeTransformer(),
        HashingVectorizer(n_features = 2**11),
        DenseTransformer()
    )

    text_pipeline_2 = make_pipeline(
        ColumnSelector(cols = ['GA keyword']),
        SimpleImputer(strategy = 'constant',fill_value = ''),
        ReshapeTransformer(),
        TfidfVectorizer(),
        DenseTransformer()
    )

    # Pipeline union

    processing_pipeline = make_union(
        numerical_pipeline,
        categorical_pipeline,
        binary_pipeline,
        text_pipeline_1,
        text_pipeline_2
    )


    estimator =    BalancedRandomForestClassifier(bootstrap=False, class_weight=None,
                     criterion='gini', max_depth=60, max_features='sqrt',
                     max_leaf_nodes=None, min_impurity_decrease=0.0,
                     min_samples_leaf=1, min_samples_split=5,
                     min_weight_fraction_leaf=0.0, n_estimators=472, n_jobs=1,
                     oob_score=False, random_state=None, replacement=False,
                     sampling_strategy='auto', verbose=0, warm_start=False)


    predictive_pipeline = make_pipeline(
        processing_pipeline,
        estimator
    )


    predictive_pipeline.fit(X, y)

    return predictive_pipeline


def main():
    """
    Main function.
    1 .Loads and cleans the training data
    2. Trains a machine learning pipeline
    3. Loads and cleans the input predict data
    4. Adds lead score predictions to the file and saves it
    """
    print("LOAD AND CLEAN THE TRAINING DATA")
    X, y = clean_train_data(trainset_fname)

    print("TRAIN THE MODEL, this step will take some time")
    trained_pipeline = train_pipeline(X, y)

    print("LOAD INPUT DATA")
    input_data = pd.read_csv(input_predictset_fname)

    print("CLEAN INPUT DATA")
    cleaned_input_data = clean_predict_data(input_data)

    print("PREDICTING LEAD SCORE")
    input_data["lead_score"] = trained_pipeline.predict_proba(cleaned_input_data)[:,1]
    
    print("SAVING OUTPUT")
    input_data.to_csv(output_predictset_fname, index=False)



if __name__ == "__main__":
    main()
