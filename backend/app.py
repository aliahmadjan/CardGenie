import json
from flask import Flask, request, jsonify
import pickle
import pandas as pd
import re
import os
import numpy as np

from datetime import datetime  , timedelta
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.security import check_password_hash , generate_password_hash

# ...

app = Flask(__name__)
app.debug = True
CORS(app)

# Replace the connection string with your own MongoDB connection string
client = MongoClient('mongodb+srv://aliahmadjan:12345@cluster0.j5u9lxj.mongodb.net/LearnLive?retryWrites=true&w=majority&ssl=true')
db = client['BusinessCardReader']
users = db['users']
card_details = db['card_details']

@app.route('/signup', methods=['POST'])
def adduser():
    name = request.json.get('name')
    password = request.json.get('password')
   

    if not name or not isinstance(password, str):    
        return jsonify({'error': 'Please Fill All the Fields'}), 422

    user = users.find_one({'name': name})
    if user:
        return jsonify({'error': 'Invalid Credentials'})

    # password_hash = generate_password_hash(password)
    user_dict = {
        'name': name,
        'password': password
    }
    users.insert_one(user_dict)

    return jsonify({'message': 'User added successfully'})

@app.route('/login', methods=['POST'])
def verify_login():
    name = request.json.get('name')
    password = request.json.get('password')

    user = users.find_one({'name': name})
    if not user or user['password'] != password:
        return jsonify({'message': 'Invalid Credentials'}), 401

    return jsonify({'message': 'Login successful'}) , 200

@app.route('/carddetails' , methods = ['POST'])
def post_card_details():
    name = request.json.get('name')
    role = request.json.get('role')
    company = request.json.get('company')
    phone = request.json.get('phone')
    email = request.json.get('email')
    website = request.json.get('website')
    address = request.json.get('address')

    # Store the information in a database or perform any other desired operations
    card_details_dict = {
        'name': name,
        'role': role,
         'company' :company,
         'phone' : phone,
         'email' : email,
         'website' : website,
         'address': address
    }
    card_details.insert_one(card_details_dict)


    return jsonify({'message': 'Card Details Stored Successfully'}) , 200


@app.route('/getcarddetails', methods = ['GET'])
def get_card_details():
    result = card_details.find({})
    card_details_list = []
    for card in result:
        card_details_list.append({
            'name': card['name'],
            'role': card['role'],
            'company': card['company'],
            'phone': card['phone'],
            'email': card['email'],
            'website': card['website'],
            'address': card['address']
        })

    return jsonify(card_details_list), 200




# run the app
if __name__ == '__main__':
    print("working")
    app.run(debug=True)
    print("working")
