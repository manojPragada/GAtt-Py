from flask import Flask
from flask_restful import Resource, Api, reqparse, abort
from flask_sqlalchemy import SQLAlchemy
import hashlib

app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sqlite.db'
db = SQLAlchemy(app)


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100))
    password = db.Column(db.String(150))


db.create_all()


class CheckUser(Resource):
    task_post_args = reqparse.RequestParser()
    task_post_args.add_argument("user_name", type=str, help="UserName is required!", required=True)
    task_post_args.add_argument("password", type=str, help="Password is required!", required=True)

    def post(self):
        todos = {"status": "1", "message": "Done !"}
        return todos


api.add_resource(CheckUser, '/checkUserLogin')
# api.add_resource()
if __name__ == '__main__':
    app.run(debug=True)
