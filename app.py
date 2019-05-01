import pymongo
from flask import Flask, request
from flask_restplus import Api, Resource, fields

flask_app = Flask(__name__)
app = Api(app = flask_app, 
		  version = "1.0", 
		  title = "Viscient Licensing BackEnd", 
		  description = "Thin layer to provide endpoints for the Front End")

licensing = app.namespace('licensing', description='Endpoints that talks to Viscient Licensing API')
mongo_db_service = app.namespace('mongodbservice', description='Endpoints that talks to MongoDb')

list_of_names = {}

model = app.model('Name Model', 
		  {'name': fields.String(required = True, 
					 description="Name of the person", 
					 help="Name cannot be blank.")})

credential_model = app.model('Credential Model', 
                {
                    'username': fields.String(required = True, 
                            description="Username to fetch MongoDb", 
                            help="Username cannot be blank."),
                    'password': fields.String(required = False, 
                            description="Password used in conjunction with username", 
                            help="Optional.")
                })

@mongo_db_service.route("/login")
class MainClass(Resource):

    # @app.doc(responses={ 200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error' }, 
	# 		 params={ 'username': 'Specify the username to fetch Paid Licenses data' })
    # def get(self, username):
    #     try:
    #         client = pymongo.MongoClient("mongodb+srv://viscient:P!nkUnic0rn@viscient-cluster-dmqxq.gcp.mongodb.net/?retryWrites=true")
    #         database = client["viscient-licensing"]
    #         collection = database["credentials"]

    #         #myquery = {}

    #         query = collection.find({ "username": username })
    #         print(query.count())

    #         return {
    #             "status": str(query[0])
    #         }
    #     except KeyError as e:
    #         name_space.abort(500, e.__doc__, status = "Could not retrieve information", statusCode = "500")
    #     except Exception as e:
    #         name_space.abort(400, e.__doc__, status = "Could not retrieve information", statusCode = "400")

    @app.doc(responses={ 200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error' })
    @app.expect(credential_model)
    def post(self):
        try:
            username = request.json['username']
            password = request.json['password']

            client = pymongo.MongoClient("mongodb+srv://viscient:P!nkUnic0rn@viscient-cluster-dmqxq.gcp.mongodb.net/?retryWrites=true")
            database = client["viscient-licensing"]
            collection = database["credentials"]

            query = collection.find({ "username": username, "password": password })

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

@licensing.route("/<int:id>")
class MainClass(Resource):

	@app.doc(responses={ 200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error' }, 
			 params={ 'id': 'Specify the Id associated with the person' })
	def get(self, id):
		try:
			name = list_of_names[id]
			return {
				"status": "Person retrieved",
				"name" : list_of_names[id]
			}
		except KeyError as e:
			name_space.abort(500, e.__doc__, status = "Could not retrieve information", statusCode = "500")
		except Exception as e:
			name_space.abort(400, e.__doc__, status = "Could not retrieve information", statusCode = "400")

	@app.doc(responses={ 200: 'OK', 400: 'Invalid Argument', 500: 'Mapping Key Error' }, 
			 params={ 'id': 'Specify the Id associated with the person' })
	@app.expect(model)		
	def post(self, id):
		try:
			list_of_names[id] = request.json['name']
			return {
				"status": "New person added",
				"name": list_of_names[id]
			}
		except KeyError as e:
			name_space.abort(500, e.__doc__, status = "Could not save information", statusCode = "500")
		except Exception as e:
			name_space.abort(400, e.__doc__, status = "Could not save information", statusCode = "400")

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