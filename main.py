from flask import Flask,render_template,redirect,url_for,request,jsonify,session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func,select
from flask_cors import CORS
import sentry_sdk



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

with app.app_context():
    db.create_all()

CORS(app, resources={r"/product/*": {"origins": "http://127.0.0.1:5500"}
                     ,r"/sales/*": {"origins": "http://127.0.0.1:5500"},
                     r"/dashboard/*":{"origins":"http://127.0.0.1:5500"}})



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


@app.route('/sales',methods=['GET','POST'])
def sales():
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

    # sales_data=[]
    # profit_data = []
    # for day,sale in sales_per_day:
    #     sales_data.append({
    #         "day":day,
    #         "total_sales":sale
    #     })
    # for day,profit in profit_per_day:
    #     profit_data.append(
    #         {
    #             "day":day,
    #             "profit":profit
    #         }
    #     )
# ,{"profit_day":profit_data}
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
        
    

if __name__ == '__main__':
    app.run(debug=True)