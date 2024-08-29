from flask import Flask,render_template,redirect,url_for,request,jsonify,session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func,select
from flask_cors import CORS
import sentry_sdk
import jwt
from datetime import datetime,timedelta
from functools import wraps



sentry_sdk.init(
    dsn="https://21e08db32f0ebdc59435ea39220fe306@o4507805034938368.ingest.us.sentry.io/4507805083893760",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for tracing.
    traces_sample_rate=1.0,
    # Set profiles_sample_rate to 1.0 to profile 100%
    # of sampled transactions.
    # We recommend adjusting this value in production.
    profiles_sample_rate=1.0,
)



app =  Flask(__name__)
app.config['SECRET_KEY']='secretkey'
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

CORS(app, resources={
    r"/product/*": {"origins": "http://127.0.0.1:5500"},
    r"/sales/*": {"origins": "http://127.0.0.1:5500"},
    r"/dashboard/*": {"origins": "http://127.0.0.1:5500"}
})



@app.route('/product',methods=['GET','POST'])
def product():
    if request.method == 'POST':
        try:
            data = request.json
            name = data['name']
            buying_price = data['buying_price']
            selling_price = data['selling_price']
            stock_quantity = data['stock_quantity']

            product = Product(name=name,buying_price=buying_price,selling_price=selling_price,stock_quantity=stock_quantity)
            db.session.add(product)
            db.session.commit()
            return jsonify({"message":"product added successfully"}),201
        except Exception as e:
            return jsonify({'error':str(e)}),500
    elif request.method == 'GET':
        products = db.session.execute(db.select(Product).order_by(Product.id)).scalars()
        prods =[]
        for product in products:
            prods.append({
                
                "id":product.id,
                "name":product.name,
                "buying_price":product.buying_price,
                "selling_price":product.selling_price,
                "stock_quantity":product.stock_quantity

            })
        return jsonify({"products": prods}) ,200
    
def token_required(f):
    @wraps(f)
    def decorated(*args,**kwargs):
        #checking if the token exists in the http
        token = request.headers.get("Authorization")
        if token is None:
            return jsonify({"message":"token is missing"})
        try:
            #takes in token ,secret key and the algorithm used to hash
            data = jwt.decode(token,app.config['SECRET_KEY'],algorithms=['HS256'])
            current_user = data['sub']
            return f(current_user,*args,**kwargs)
        except:
            return jsonify({"error":"error decoding token,confirm your secret key"})
    return decorated

@app.route('/sales',methods=['GET','POST'])
@token_required
def sales(current_user):
    if request.method == 'POST':
        try:
            data = request.json
            pid = data['pid']
            quantity = data['quantity']
            sale = Sale(pid=pid,quantity=quantity)
            db.session.add(sale)
            db.session.commit()
            return jsonify({"message":"Sale made successfully"}),201
        except Exception as e:
            return jsonify({"error":str(e)}),500
    elif request.method == 'GET':
        user = db.session.query(User).filter(User.name == current_user).first()

        if not user:
            return jsonify({"message":"user not found"}),404
        sales = db.session.execute(db.select(Sale).order_by(Sale.pid)).scalars()
        sale_data = []
        for sale in sales:
            sale_data.append({
                'id':sale.id,
                'product': sale.pid,
                'quantity':sale.quantity,
                'created_at':sale.created_at,
            })
        return jsonify({"sales":sale_data}),200
    
@app.route('/dashboard') 
def dashboard():
    
    sales_per_day = db.session.query(
        func.date(Sale.created_at).label('date'),
        func.sum(Sale.quantity * Product.selling_price).label('total_sales')
    ).join(Product).group_by(func.date(Sale.created_at)).all()

    profit_per_day = db.session.query(
        func.date(Sale.created_at).label('date'),
        func.sum((Sale.quantity * Product.selling_price)-
                (Sale.quantity * Product.buying_price)).label("profit")
    ).join(Product).group_by(func.date(Sale.created_at)).all()

    sales_data = [{'date':str(day),'total_sales':sales} for day,sales in sales_per_day]
    profit_data =[{'date':str(day),'profit':profit} for day,profit in profit_per_day]

    
    return jsonify({"sales_per_day":sales_data,"profit_per_day":profit_data}),200

# testing sentry  
@app.route('/sentry_error')
def hello_world():
    try:
        division_by_zero = 1 / 0
        return jsonify({"result": division_by_zero})
    except Exception as e:
        sentry_sdk.capture_exception(e)
        return jsonify({"error":str(e)})

@app.route('/user',methods=['GET','POST'])
def users():
    if request.method == 'POST':
        try:
            data = request.json
            name = data['name']
            email = data['email']
            password = data['password']
            user = User(name=name,email=email,password=password)
            db.session.add(user)
            db.session.commit()
            return jsonify({"success":"user added successfully"}),201
        except Exception as e:
            return jsonify({"error adding user":e}),500
    elif request.method == 'GET':
        users = db.session.execute(db.select(User).order_by(User.name)).scalars()
        user_data = []
        for user in users:
            user_data.append({
                "name": user.name,
                "email":user.email,
                "password":user.password
            })
        return jsonify({"users":user_data}),200


    


#creating token
@app.post("/login")
def login_user():
    data = request.json

    u = data['username']
    p = data['password']
    existing_user = db.session.query(User).filter(User.name ==u,User.password==p).first()

    if not existing_user:
        return jsonify({"Login failed": "confirm credentials"}),401
    try :
        access_token = jwt.encode({"sub":u,"exp":datetime.utcnow()+ timedelta(minutes=30)},app.config['SECRET_KEY'])
        return jsonify({"message":"login sucessful","access token":access_token})
    except Exception as e:
        return jsonify({"error creating access token": e})



if __name__ == '__main__':
    app.run(debug=True)