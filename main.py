# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


#required libraries
import os
from logging import exception

from flask import Flask, jsonify, request
app = Flask(__name__)

#import plotly.express as px
#import numpy as np
import pandas as pd
#import plotly.graph_objects as go
#import matplotlib.pyplot as plt
#import seaborn as sns
#import operator as op
#from mlxtend.frequent_patterns import apriori
#from mlxtend.frequent_patterns import association_rules

for dirname, _, filenames in os.walk('Groceries_dataset.csv'):
    for filename in filenames:
        print(os.path.join(dirname, filename))
#!pip install apriori

app = Flask(__name__)

data = pd.read_csv('Groceries_dataset.csv')
# Converting Date column into correct datatype which is datetime
data.columns = ['memberID', 'Date', 'itemName']
data.Date = pd.to_datetime(data.Date)
data.memberID = data['memberID'].astype('str')
@app.route('/')
def welcome():
    return jsonify("welcome to the page")

@app.route("/api/top_users", methods = ['GET'])
def api_top_users():
    try:
        user_item = data.groupby(pd.Grouper(key='memberID')).size().reset_index(name='count') \
            .sort_values(by='count', ascending=False)
        top_25 = user_item.memberID.count() / 4
        top_25 = round(top_25)
        user_items = user_item.reset_index()
        user_items = user_items.iloc[:top_25]
        result = user_items.to_json(orient='index')
        return result
    except exception as e:
        return jsonify(e)


@app.route('/api/segments', methods = ['GET'])
def api_segments():
    try:
        # Finding last purchase date of each customer
        Recency = data.groupby(by='memberID')['Date'].max().reset_index()
        Recency.columns = ['memberID', 'LastDate']
        # Finding last date for our dataset
        last_date_dataset = Recency['LastDate'].max()
        # Calculating Recency by subtracting (last transaction date of dataset) and (last purchase date of each customer)
        Recency['Recency'] = Recency['LastDate'].apply(lambda x: (last_date_dataset - x).days)

        # Frequency of the customer visits
        Frequency = data.drop_duplicates(['Date', 'memberID']).groupby(by=['memberID'])['Date'].count().reset_index()
        Frequency.columns = ['memberID', 'Visit_Frequency']

        # need to add a column with price
        Monetary = data.groupby(by="memberID")['itemName'].count().reset_index()
        Monetary.columns = ['memberID', 'Monetary']
        # I assumed each item has equal price and price is 10
        Monetary['Monetary'] = Monetary['Monetary'] * 10

        # Combining all scores into one DataFrame
        RFM = pd.concat([Recency['memberID'], Recency['Recency'], Frequency['Visit_Frequency'], Monetary['Monetary']],
                        axis=1)

        # 5-5 score = the best customers
        RFM['Recency_quartile'] = pd.qcut(RFM['Recency'], 5, [5, 4, 3, 2, 1])
        RFM['Frequency_quartile'] = pd.qcut(RFM['Visit_Frequency'], 5, [1, 2, 3, 4, 5])

        RFM['RF_Score'] = RFM['Recency_quartile'].astype(str) + RFM['Frequency_quartile'].astype(str)

        segt_map = {  # Segmentation Map [Ref]
            r'[1-2][1-2]': 'hibernating',
            r'[1-2][3-4]': 'at risk',
            r'[1-2]5': 'can\'t loose',
            r'3[1-2]': 'about to sleep',
            r'33': 'need attention',
            r'[3-4][4-5]': 'loyal customers',
            r'41': 'promising',
            r'51': 'new customers',
            r'[4-5][2-3]': 'potential loyalists',
            r'5[4-5]': 'champions'
        }

        RFM['RF_Segment'] = RFM['RF_Score'].replace(segt_map, regex=True)
        RFM.head()
        x = RFM.RF_Segment.value_counts()
        result = x.to_json(orient='index')
        return result
    except exception as e:
        return "error occured"



port = os.getenv('PORT',8080)
if __name__ == '__main__':
    app.run(host="0.0.0.0",port=port)


