from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify
import mysql.connector, os
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import os
from PIL import UnidentifiedImageError, Image
from tensorflow.keras.applications.mobilenet import preprocess_input
from werkzeug.utils import secure_filename
import threading
import os
import pandas as pd
from transformers import pipeline


app = Flask(__name__)
app.secret_key = 'newsentiment' 


mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    port="3306",
    database='newsentiment'
)

mycursor = mydb.cursor()

def executionquery(query,values):
    mycursor.execute(query,values)
    mydb.commit()
    return

def retrivequery1(query,values):
    mycursor.execute(query,values)
    data = mycursor.fetchall()
    return data

def retrivequery2(query):
    mycursor.execute(query)
    data = mycursor.fetchall()
    return data



@app.route('/')
def index():


    return render_template('index.html')

@app.route('/about')
def about():

    return render_template('about.html')


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        c_password = request.form['c_password']

        if password == c_password:
            query = "SELECT email FROM users"
            email_data = retrivequery2(query)
            email_data_list = []
            for i in email_data:
                email_data_list.append(i[0])

            if email not in email_data_list:
                query = "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)"
                values = (name, email, password)
                executionquery(query, values)

                return render_template('login.html', message="Successfully Registered!")
            return render_template('register.html', message="This email ID is already exists!")
        return render_template('register.html', message="Conform password is not match!")
    return render_template('register.html')


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']

        query = "SELECT email FROM users"
        email_data = retrivequery2(query)
        email_data_list = []
        for i in email_data:
            email_data_list.append(i[0])

        if email in email_data_list:
            query = "SELECT * FROM users WHERE email = %s"
            values = (email,)
            password__data = retrivequery1(query, values)
            if password == password__data[0][3]:
                session["user_email"] = email
                session["user_id"] = password__data[0][0]
                session["user_name"] = password__data[0][1]

                return redirect("/home")
            return render_template('login.html', message= "Invalid Password!!")
        return render_template('login.html', message= "This email ID does not exist!")
    return render_template('login.html')



@app.route('/home')
def home():
    
    return render_template('home.html')




########################################################################################################################
############################################## PREDICTION SECTION #####################################################
########################################################################################################################

# Load the sampled CSV
df = pd.read_csv('amazon_reviews.csv')

# Initialize the sentiment analysis pipeline
sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model="distilbert/distilbert-base-uncased-finetuned-sst-2-english",
    revision="714eb0f",
    truncation=True,
    max_length=512
)

# Route for the prediction page
@app.route('/prediction', methods=['GET', 'POST'])
def prediction():
    # Get top 5 products by review count for product cards
    popular_products = df['asin'].value_counts().head(10).index.tolist()
    return render_template('prediction.html', products=popular_products)

# Route to fetch reviews for a product
@app.route('/get_reviews', methods=['POST'])
def get_reviews():
    product = request.json['product']
    reviews = df[df['asin'] == product]['reviewText'].dropna().tolist()
    return jsonify({'reviews': reviews[:100]})  # Limit to 200 reviews for performance

# Route to analyze sentiments
@app.route('/analyze_sentiments', methods=['POST'])
def analyze_sentiments():
    product = request.json['product']
    reviews = df[df['asin'] == product]['reviewText'].dropna().tolist()[:200]  # Limit to 50 reviews
    if not reviews:
        return jsonify({'error': 'No reviews found for this product'})
    
    # Perform sentiment analysis
    sentiments = sentiment_pipeline(reviews)
    positive = sum(1 for s in sentiments if s['label'] == 'POSITIVE') / len(sentiments) * 100
    negative = sum(1 for s in sentiments if s['label'] == 'NEGATIVE') / len(sentiments) * 100
    result = f"Positive: {positive:.2f}%, Negative: {negative:.2f}%"
    return jsonify({'sentiment': result})


if __name__ == '__main__':
    app.run(debug = True)