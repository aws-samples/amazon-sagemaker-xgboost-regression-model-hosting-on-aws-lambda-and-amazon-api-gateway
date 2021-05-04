"""
Copyright 2021 Amazon.com, Inc. or its affiliates.  All Rights Reserved.
SPDX-License-Identifier: MIT-0
"""
from io import StringIO
import json
import os
import pandas as pd
import pickle
import xgboost as xgb


## Load the model object from the pickle file
model_pickle_file_path = os.environ.get('MODEL_PICKLE_FILE_PATH')
print('Loading the model object from the pickle file \'{}\'...'.format(model_pickle_file_path))
with open(model_pickle_file_path, 'rb') as model_pickle_file:
    model = pickle.load(model_pickle_file)
print('Completed loading the model object from the pickle file.')


## Perform prediction
def predict(pred_x_csv):
    print('Performing prediction...')
    pred_x_df = pd.read_csv(StringIO(pred_x_csv), sep=',', header=None)
    pred_x = xgb.DMatrix(pred_x_df.values)
    print('Completed performing prediction.')
    return model.predict(pred_x)[0]


## Parse input data for various scenarios (supported response content-type - 'text/plain' or 'application/json'):
## 1. Direct invocation of the Lambda function
## 2. As the backend of a HTTP API on Amazon API Gateway
## 3. As the backend of a REST API on Amazon API Gateway
def parse_request_data(event):
    print('Parsing request data...')
    # Set default
    response_content_type = 'application/json'
    try:
        # Try to parse as direct invocation
        pred_x_csv = event['pred_x_csv']
        invocation_type = 'direct_or_api_gateway'
        try:
            response_content_type = event['response_content_type'].strip()
            if response_content_type is None:
                response_content_type = 'application/json'
            elif len(response_content_type) == 0:
                response_content_type = 'application/json'
            elif response_content_type != 'text/plain':
                response_content_type = 'application/json'
        except KeyError:
            pass
    except KeyError:
        invocation_type = 'api_gateway'
        # Parse as HTTP API or REST API on Amazon API Gateway
        pred_x_csv = json.loads(event['body'])['pred_x_csv']
    print('Completed parsing request data.')
    return invocation_type, response_content_type, pred_x_csv


## Format the response based on the specified content-type ('text/plain' or 'application/json')
def format_response_data(response_content_type, return_raw_data):
    print('Formatting response data...')
    if response_content_type == 'text/plain':
        return_data = return_raw_data
    else:
        return_data = {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "Predicted value": return_raw_data
            })
        }
    print('Completed formatting response data.')
    return return_data


## The handler function
def handler(event, context):
    print('Executing the handler() function...')
    # Parse the request data
    invocation_type, response_content_type, pred_x_csv = parse_request_data(event)
    print('Invocation type = {}'.format(invocation_type))
    print('Response content type = {}'.format(response_content_type))
    # Perform prediction
    pred_y = predict(pred_x_csv)
    print('Predicted value = {}'.format(pred_y))
    # Format the response data
    return_data = format_response_data(response_content_type, str(pred_y))
    print('Completed executing the handler() function.')
    return return_data
