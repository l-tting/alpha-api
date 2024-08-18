from flask import Flask,render_template,redirect,url_for,request,jsonify,session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func,select

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



@app.route('/',methods=['GET','POST'])
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
        products = db.session.execute(db.select(Product).order_by(Product.name)).scalars()
        for product in products:
            prods = [{
                
                "name":product.name,
                "buying_price":product.buying_price,
                "selling_price":product.selling_price,
                "stock_quantity":product.stock_quantity

            }]
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
        for sale in sales:
            sall =[{
                'product': sale.product.name,
                'quantity':sale.quantity
            }]
        return jsonify({"sales":sall}),200

if __name__ == '__main__':
    app.run(debug=True)