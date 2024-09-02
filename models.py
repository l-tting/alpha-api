from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

app =  Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']= 'postgresql://postgres:6979@localhost/postmandb'
db = SQLAlchemy(app)

class Product(db.Model):
    __tablename__='products'
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String,nullable= False)
    buying_price = db.Column(db.Integer,nullable= False)
    selling_price = db.Column(db.Integer,nullable= False)
    stock_quantity= db.Column(db.Integer,nullable= False)
    sale = db.relationship('Sale',backref='product')


class Sale(db.Model):
    __tablename__ ='sales'
    id = db.Column(db.Integer,primary_key=True)
    pid =db.Column(db.Integer,db.ForeignKey('products.id'))
    quantity = db.Column(db.Integer,nullable= False)
    created_at = db.Column(db.DateTime,server_default = func.now())

class User(db.Model):
    __tablename__= 'users'
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String,nullable=False)
    email = db.Column(db.String,nullable=False)
    password = db.Column(db.String,nullable=False)


with app.app_context():
    db.create_all()