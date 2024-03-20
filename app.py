from flask import Flask
import strawberry
from strawberry.flask.views import GraphQLView
from pymongo import MongoClient
from urllib.parse import quote_plus
from dotenv import load_dotenv
import os
from flask_cors import CORS

# Load environment variables
load_dotenv()

# MongoDB setup
username = os.getenv('DB_USERNAME')
password = os.getenv('DB_PASSWORD')
host = os.getenv('DB_HOST')
db_name = os.getenv('DB_NAME')
encoded_username = quote_plus(username)
encoded_password = quote_plus(password)
uri = f"mongodb+srv://{encoded_username}:{encoded_password}@{host}/{db_name}?retryWrites=true&w=majority"

client = MongoClient(uri)
db = client[db_name]
collection = db.api

app = Flask(__name__)
CORS(app, resources={r"*": {"origins": "*"}})

@strawberry.type
class Message:
    message: str

@strawberry.input
class MessageInput:
    content: str

@strawberry.type
class Query:
    @strawberry.field
    def fetchMessage(self) -> Message:
        # Fetch a message from MongoDB
        document = collection.find_one({}, {'_id': 0, 'message': 1})
        return Message(message=document['message']) if document else Message(message="No message found.")

    @strawberry.field
    def fetchMessages(self) -> list[Message]:
        # Fetch all messages from MongoDB
        documents = collection.find({}, {'_id': 0, 'message': 1})
        return [Message(message=doc['message']) for doc in documents]

@strawberry.type
class Mutation:
    @strawberry.mutation
    def postMessage(self, input: MessageInput) -> Message:
        # Insert a message into MongoDB
        result = collection.insert_one({'message': input.content})
        return Message(message="Message saved successfully." if result.inserted_id else "Failed to save message.")

schema = strawberry.Schema(query=Query, mutation=Mutation)

app.add_url_rule(
    "/graphql", 
    view_func=GraphQLView.as_view(
        "graphql_view", 
        schema=schema, 
        graphiql=True
    )
)

if __name__ == "__main__":
    app.run(debug=True)