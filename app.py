import requests
import pymongo
import json
import smtplib
import bson
from flask import Flask, request, jsonify
from flask_restplus import Api, Resource, fields
from flask_pymongo import PyMongo
from datetime import datetime, timedelta
from bson.json_util import dumps, RELAXED_JSON_OPTIONS
from bson import json_util
from mailjet_rest import Client

flask_app = Flask(__name__)

flask_app.config["MONGO_URI"] = "mongodb+srv://viscient:P!nkUnic0rn@viscient-cluster-dmqxq.gcp.mongodb.net/viscient-licensing?retryWrites=true"
mongoClient = PyMongo(flask_app)

app = Api(app = flask_app, 
		  version = "1.0", 
		  title = "Viscient Licensing BackEnd", 
		  description = "Thin layer to provide endpoints for the Front End")

licensing = app.namespace('licensing', description='Endpoints that talks to Viscient Licensing API')
mongo_db_service = app.namespace('mongodbservice', description='Endpoints that talks to MongoDb')

VISCIENT_API_URL = 'https://viscientgateway.ddns.net:8899/VLREST/v1'

model = app.model('Name Model', 
        {
        'name': fields.String(required = True, 
                description="Name of the person", 
                help="Name cannot be blank.")
        })

credential_model = app.model('Credential Model', 
                    {
                    'username': fields.String(required = True, 
                            description="Username to fetch MongoDb", 
                            help="Username cannot be blank."),
                    'password': fields.String(required = False, 
                            description="Password used in conjunction with username", 
                            help="Optional.")
                    })

activation_extension_model = app.model('Activation or Extension Model', 
                            {
                            'username': fields.String(required = True, 
                                    description="Username to used to activate/extend"),
                            'domainName': fields.String(required = True, 
                                    description="Domain name used in conjunction with username"),
                            'numberOfDays': fields.Integer(required = True, 
                                    description="Number of days expired for the domain"),
                            'accountType': fields.String(required = True, 
                                    description="Admin or User")
                            })

increment_model = app.model('Increment Credit Model', 
                    {
                    'username': fields.String(required = True, 
                            description="Username to fetch MongoDb"),
                    'increment_value': fields.Integer(required = True, 
                            description="Number of credit to add to the respective user")
                    })
                            

@mongo_db_service.route("/login")
class MainClass(Resource):
    @app.doc(responses={ 200: 'OK', 400: 'Invalid Argument', 500: 'Internal Error' })
    @app.expect(credential_model)
    def post(self):
        try: 
            username = request.json['username']
            password = request.json['password']

            user = mongoClient.db.credentials.find_one({ "username": username, "password": password })

            if(user is None):
                return {
                    "username": username,
                    "statusCode": 404,
                    "message": 'No such user found',
                    "accountType": ''
                }
                
            accountType = user['accountType']

            return {
                "username": username,
                "statusCode": 200,
                "message": "User found",
                "accountType": accountType
            }
        except KeyError as e:
            mongo_db_service.abort(400, e.__doc__, status = "Could not save information", statusCode = "400")
        except Exception as e:
            mongo_db_service.abort(500, e.__doc__, status = "Exception from the method", statusCode = "500")

@mongo_db_service.route("/history")
class MainClass(Resource):
    @app.doc(responses={ 200: 'OK', 400: 'Invalid Argument', 500: 'Internal Error' },
            params= {        
                    'username': 'Specify the username to fetch its history in MongoDb',
                    'accountType': 'User or Admin'
                    })
    def get(self):
        try:
            username = request.args.get('username')
            accountType = request.args.get('accountType')

            histories = None
            if(accountType == 'admin'):
                histories = mongoClient.db.history.find({}).sort( 'dateCreated', pymongo.DESCENDING )
            else:
                histories = mongoClient.db.history.find({'username': username}).sort( 'dateCreated', pymongo.DESCENDING )
            
            if(histories == None):
                return {
                    "statusCode": 404,
                    "message": "No such user found in History collection",
                    "username": username
                }

            historyDetails = []
            for history in histories:
                historyDetail = {
                    'username': history['username'],
                    'actionType': history['actionType'],
                    'domainName': history['domainName'],
                    'dateCreated': history['dateCreated'].isoformat(),
                    'dateExpired': history['dateExpired'].isoformat(),
                }
                historyDetails.append(historyDetail)
            
            return jsonify(historyDetails=historyDetails, statusCode=200)
        except KeyError as e:
            mongo_db_service.abort(400, e.__doc__, status = "Could not save information", statusCode = "400")
        except Exception as e:
            mongo_db_service.abort(500, e.__doc__, status = "Exception from the method", statusCode = "500")

@mongo_db_service.route("/user_counter")
class MainClass(Resource):
    @app.doc(responses={ 200: 'OK', 400: 'Invalid Argument', 500: 'Internal Error' },
            params= { 'username': 'Specify the username to fetch its history in MongoDb' })
    def get(self):
        try:
            username = request.args.get('username')

            user = mongoClient.db.credentials.find_one({ "username": username })

            if(user is None):
                return {
                    "username": username,
                    "statusCode": 404,
                    "message": 'No such user found',
                    "poc_counter": 0
                }

            counter = user['pocLicenseCounter']

            return {
                "username": username,
                "statusCode": 200,
                "message": 'User found along with its counter',
                "poc_counter": counter
            }
        except KeyError as e:
            mongo_db_service.abort(400, e.__doc__, status = "Could not save information", statusCode = "400")
        except Exception as e:
            mongo_db_service.abort(500, e.__doc__, status = "Exception from the method", statusCode = "500")

@mongo_db_service.route("/all_user")
class MainClass(Resource):
    @app.doc(responses={ 200: 'OK', 400: 'Invalid Argument', 500: 'Internal Error' })
    def get(self):
        try:
            users = mongoClient.db.credentials.find({"accountType": "user"})

            if(users.count() < 1):
                return "empty database"

            userList = list(users)
            userDetails = []
            for user in userList:
                userDetail = {
                    'username': user['username'],
                    'pocLicenseCounter': user['pocLicenseCounter'],
                    'accountType': user['accountType']
                }
                userDetails.append(userDetail)
            
            return jsonify(userDetails=userDetails, statusCode=200)

        except KeyError as e:
            mongo_db_service.abort(400, e.__doc__, status = "Could not save information", statusCode = "400")
        except Exception as e:
            mongo_db_service.abort(500, e.__doc__, status = "Exception from the method", statusCode = "500")

@mongo_db_service.route("/increment_user_credit")
class MainClass(Resource):
    @app.doc(responses={ 200: 'OK', 400: 'Invalid Argument', 500: 'Internal Error' })
    @app.expect(increment_model)
    def post(self):
        try: 
            username = request.json['username']
            increment_value = request.json['increment_value']

            increment_response = inc_poc_license(username, 'user', increment_value)

            if(increment_response is None):
                return {
                    "username": username,
                    "statusCode": 500,
                    "increment_response": 500,
                    "message": 'Error incrementing user credit'
                }

            return {
                "username": username,
                "statusCode": 200,
                "increment_response": increment_response,
                "message": "Successfully increment credit to user"
            }
        except KeyError as e:
            mongo_db_service.abort(400, e.__doc__, status = "Could not save information", statusCode = "400")
        except Exception as e:
            mongo_db_service.abort(500, e.__doc__, status = "Exception from the method", statusCode = "500")

@licensing.route("/query_licensing")
class MainClass(Resource):
    @app.doc(responses={ 200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error' }, 
                params={ 'username': 'Specify the username to fetch in Viscient Licensing API' })
    def get(self):
        try:
            username = request.args.get('username')
            endpoint = f"{VISCIENT_API_URL}/query_license"
            post_url = endpoint
            response = requests.post(post_url, data=None, headers=None)
            parsedResponse = json.loads(response.content)
            responseCode = parsedResponse["code"]
            if(responseCode != 200):
                return {
                    "statusCode": 500,
                    "license": None,
                    "credit": None
                }

            licenseResponse = parsedResponse["results"]["data"]["license"]
            creditResponse = parsedResponse["results"]["data"]["credit"]
            
            return {
                "statusCode": 200,
                "license": licenseResponse,
                "credit": creditResponse
            }
        except KeyError as e:
            licensing.abort(500, e.__doc__, status = "Could not retrieve information", statusCode = "500")
        except Exception as e:
            licensing.abort(400, e.__doc__, status = "Could not retrieve information", statusCode = "400")

@licensing.route("/activation")
class MainClass(Resource):
    @app.doc(responses={ 200: 'OK', 400: 'Invalid Argument', 500: 'Internal Error' })
    @app.expect(activation_extension_model)
    def post(self):
        try:
            username = request.json['username']
            domainName = request.json['domainName']
            numberOfDays = request.json['numberOfDays']
            accountType = request.json['accountType']

            endpoint = f"{VISCIENT_API_URL}/remote_activate_poc?company_name={username}&domain_name={domainName}&number_of_days={numberOfDays}"
            post_url = endpoint
            response = requests.post(post_url, data=None, headers=None)
            parsedResponse = json.loads(response.content)
            responseCode = parsedResponse["code"]
            if(responseCode != 200):
                return {
                    "statusCode": 500,
                    "message": "Error in Activating POC License",
                }

            insertResult = insert_history(username, "Activate POC", domainName, numberOfDays)
            decrementResponse = inc_poc_license(username, accountType, -1)
            email_notification_response = send_email_mailjet(insertResult["new_history"])
            
            return {
                "statusCode": 200,
                "message": "Success",
                "insertResponse": insertResult["insert_response"],
                "decrementResponse": decrementResponse,
                "email_notification_response": email_notification_response
            }
        except KeyError as e:
            licensing.abort(400, e.__doc__, status = "Could not retrieve information", statusCode = "400")
        except Exception as e:
            licensing.abort(500, e.__doc__, status = "Exception from the method", statusCode = "500")

@licensing.route("/extension")
class MainClass(Resource):
    @app.doc(responses={ 200: 'OK', 400: 'Invalid Argument', 500: 'Internal Error' })
    @app.expect(activation_extension_model)
    def post(self):
        try:
            username = request.json['username']
            domainName = request.json['domainName']
            numberOfDays = request.json['numberOfDays']
            accountType = request.json['accountType']

            endpoint = f"{VISCIENT_API_URL}/extend_poc_license?company_name={username}&domain_name={domainName}&number_of_days={numberOfDays}"
            post_url = endpoint
            response = requests.post(post_url, data=None, headers=None)
            parsedResponse = json.loads(response.content)
            responseCode = parsedResponse["code"]
            if(responseCode != 200):
                return {
                    "statusCode": 500,
                    "message": "Error in Extending POC License",
                }
                
            insertResult = insert_history(username, "Extend POC", domainName, numberOfDays)
            decrementResponse = inc_poc_license(username, accountType, -1)
            email_notification_response = send_email_mailjet(insertResult["new_history"])

            return {
                "statusCode": 200,
                "message": "Success",
                "insertResponse": insertResult["insert_response"],
                "decrementResponse": decrementResponse,
                "email_notification_response": email_notification_response
            }
        except KeyError as e:
            licensing.abort(400, e.__doc__, status = "Could not retrieve information", statusCode = "400")
        except Exception as e:
            licensing.abort(500, e.__doc__, status = "Exception from the method", statusCode = "500")


def insert_history(username, actionType, domainName, numberOfDays):
    new_history = {
                    "username": username,
                    "actionType": actionType,
                    "domainName": domainName,
                    "dateCreated": datetime.utcnow(),
                    "dateExpired": datetime.utcnow() + timedelta(days=numberOfDays)
                }
                
    response = mongoClient.db.history.insert_one(new_history)
    return {
        "insert_response": 200,
        "new_history": new_history
    }
    
def inc_poc_license(username, accountType, inc_value):
    if(accountType == "admin"):
        return 200
    
    response = mongoClient.db.credentials.find_one_and_update({ "username": username }, {'$inc': {'pocLicenseCounter': inc_value}})
    return 200
    
def send_email_notification():
    gmail_user = 'admin@viscientml.com'  
    gmail_password = ''

    sent_from = gmail_user  
    to = ['victorgtav7@gmail.com']  
    subject = 'Test Subject'  
    body = "Test Body"

    email_text = """\  
    From: %s  
    To: %s  
    Subject: %s

    %s
    """ % (sent_from, ", ".join(to), subject, body)

    try:  
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_password) #failed here
        server.sendmail(sent_from, to, email_text)
        server.close()

        print('Email sent!')
    except:  
        print('Error occured')

def send_email_mailjet(new_history):
    api_key = 'a69cb7f74803eeeed3c31b28a62a8642'
    api_secret = '1998b948eba95af112065aa042ceb838'
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')

    construct_message_subject = f'A new "{new_history["actionType"]}" has been triggered from {new_history["username"]}'

    construct_message_body = f'''<h3>Automated Email Notification from Viscient BackEnd</h3>
                                    <p>A new "{new_history["actionType"]}" has occured for "{new_history["username"]}" on "{new_history["domainName"]}".</p>
                                    <p>Date created (UTC): {new_history["dateCreated"]}</p>
                                    <p>Date expired (UTC): {new_history["dateExpired"]}</p>
                                    <br>
                                    <p>Cheers,</p>
                                    <p>Viscient BackEnd via MailJet</p>'''

    data = {
    'Messages': [
                    {
                        "From": {
                                "Email": "admin@viscientml.com",
                                "Name": "Me"
                        },
                        "To": [
                                {
                                        "Email": "admin@viscientml.com",
                                        "Name": "You"
                                }
                        ],
                        "Subject": construct_message_subject,
                        "TextPart": "Greetings from Mailjet!",
                        "HTMLPart": construct_message_body
                    }
            ]
    }
    result = mailjet.send.create(data=data)
    return result.status_code