import requests
import pymongo
import json
import smtplib
from flask import Flask, request
from flask_restplus import Api, Resource, fields
from flask_pymongo import PyMongo
from datetime import datetime, timedelta

flask_app = Flask(__name__)

flask_app.config["MONGO_URI"] = "mongodb+srv://viscient:P!nkUnic0rn@viscient-cluster-dmqxq.gcp.mongodb.net/viscient-licensing?retryWrites=true"
mongoClient = PyMongo(flask_app)

app = Api(app = flask_app, 
		  version = "1.0", 
		  title = "Viscient Licensing BackEnd", 
		  description = "Thin layer to provide endpoints for the Front End")

licensing = app.namespace('licensing', description='Endpoints that talks to Viscient Licensing API')
mongo_db_service = app.namespace('mongodbservice', description='Endpoints that talks to MongoDb')

list_of_names = {}

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
                            

@mongo_db_service.route("/login")
class MainClass(Resource):
    @app.doc(responses={ 200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error' })
    @app.expect(credential_model)
    def post(self):
        try:
            username = request.json['username']
            password = request.json['password']

            query = mongoClient.db.credentials.find({ "username": username, "password": password })
            print(query)
            customCode = 404
            customMessage = 'No such user found'

            if(query.count() > 0):
                customCode = 200
                customMessage = 'User found'

            return {
                "username": username,
                "statusCode": customCode,
                "message": customMessage
            }
        except KeyError as e:
            mongo_db_service.abort(500, e.__doc__, status = "Could not save information", statusCode = "500")
        except Exception as e:
            mongo_db_service.abort(400, e.__doc__, status = "Could not save information", statusCode = "400")

@licensing.route("/query_licensing/<username>")
class MainClass(Resource):
    @app.doc(responses={ 200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error' }, 
                params={ 'username': 'Specify the username to fetch in Viscient Licensing API' })
    def get(self, username):
        try:
            endpoint = 'https://viscientgateway.ddns.net:8899/VLREST/v1/query_license'
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
            # return {
            # 	"status": "New person added",
            # 	"name": list_of_names[id]
            # }
        except KeyError as e:
            licensing.abort(500, e.__doc__, status = "Could not retrieve information", statusCode = "500")
        except Exception as e:
            licensing.abort(400, e.__doc__, status = "Could not retrieve information", statusCode = "400")

    # @app.doc(responses={ 200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error' }, 
    #             params={ 'id': 'Specify the Id associated with the person' })
    # @app.expect(model)		
    # def post(self, id):
    #     try:
    #         return {
    #             "status": "New person added",
    #             "name": list_of_names[id]
    #         }
    #     except KeyError as e:
    #         licensing.abort(500, e.__doc__, status = "Could not save information", statusCode = "500")
    #     except Exception as e:
    #         licensing.abort(400, e.__doc__, status = "Could not save information", statusCode = "400")

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

            endpoint = f"https://viscientgateway.ddns.net:8899/VLREST/v1/remote_activate_poc?company_name={username}&domain_name={domainName}&number_of_days={numberOfDays}"
            post_url = endpoint
            response = requests.post(post_url, data=None, headers=None)
            parsedResponse = json.loads(response.content)
            responseCode = parsedResponse["code"]
            if(responseCode != 200):
                return {
                    "statusCode": 500,
                    "message": "Error in Activating POC License",
                }

            mongoDbResponse = insert_history(username, "Extend POC", domainName, numberOfDays)
            decrementResponse = decrement_poc_license(username, accountType)
            
            return {
                "statusCode": 200,
                "message": "Success",
                "insertResponse": insertResponse,
                "decrementResponse": decrementResponse
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

            endpoint = f"https://viscientgateway.ddns.net:8899/VLREST/v1/extend_poc_license?company_name={username}&domain_name={domainName}&number_of_days={numberOfDays}"
            post_url = endpoint
            response = requests.post(post_url, data=None, headers=None)
            parsedResponse = json.loads(response.content)
            responseCode = parsedResponse["code"]
            if(responseCode != 200):
                return {
                    "statusCode": 500,
                    "message": "Error in Activating POC License",
                }
            
            insertResponse = insert_history(username, "Extend POC", domainName, numberOfDays)
            decrementResponse = decrement_poc_license(username, accountType)
            #send_email_notification()

            return {
                "statusCode": 200,
                "message": "Success",
                "insertResponse": insertResponse,
                "decrementResponse": decrementResponse
            }
        except KeyError as e:
            licensing.abort(400, e.__doc__, status = "Could not retrieve information", statusCode = "400")
        except Exception as e:
            licensing.abort(500, e.__doc__, status = "Exception from the method", statusCode = "500")


def insert_history(username, actionType, domainName, numberOfDays):
    newHistory = {
                    "username": username,
                    "actionType": actionType,
                    "domainName": domainName,
                    "dateCreated": datetime.utcnow(),
                    "dateExpired": datetime.utcnow() + timedelta(days=numberOfDays)
                }
                
    response = mongoClient.db.history.insert_one(newHistory)
    return 200
    
def decrement_poc_license(username, accountType):
    if(accountType == "admin"):
        return 200
    
    response = mongoClient.db.credentials.find_one_and_update({ "username": username }, {'$inc': {'pocLicenseCounter': -1}})
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


# @app.route('/login', methods=['GET','POST'])
# def login():
#   if request.method == 'POST':
#     #check user details from db
#     login_user()
#   elif request.method == 'GET':
#     #serve login page
#     serve_login_page()

# @app.route('/user', methods=['POST'])
# def get_user():
#   username = request.form['username']
#   password = request.form['password']
#   #login(arg,arg) is a function that tries to log in and returns true or false
#   #status = login(username, password)
#   return username

# @app.route('/')
# def index():
#   return 'Index Page'

# @app.route('/query_license/<company_name>', methods=['POST'])
# def query_license(company_name):
#     endpoint = 'https://viscientgateway.ddns.net:8899/VLREST/v1/query_license'
#     post_url = endpoint
#     response = requests.post(post_url, data=None, headers=None)
#     print(response.content)
#     return response.content

# @app.route('/post/<username>')
# def show_post(username):
#     client = pymongo.MongoClient("mongodb+srv://viscient:P!nkUnic0rn@viscient-cluster-dmqxq.gcp.mongodb.net/?retryWrites=true")
#     database = client["viscient-licensing"]
#     collection = database["credentials"]

#     #myquery = {}

#     query = collection.find({ "username": username })
#     print(query.count())
#     #print(str(mydoc))
    
#     #returns the post, the post_id should be an int
#     return "test"