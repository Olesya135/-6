import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, Product, Order, OrderItem

app = Flask(__name__)

# Настройки для Windows
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-123-windows')

# Используем SQLite для Windows
database_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'shop.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация базы данных
db.init_app(app)

# Создание таблиц в контексте приложения
with app.app_context():
    db.create_all()
    # Проверяем и добавляем тестовые данные
    if Product.query.count() == 0:
        products = [
            Product(name='Ноутбук', price=55000.0, description='Мощный игровой ноутбук', stock=10),
            Product(name='Мышь', price=1500.0, description='Беспроводная мышь', stock=50),
            Product(name='Клавиатура', price=2500.0, description='Механическая клавиатура', stock=30),
        ]
        db.session.add_all(products)
        db.session.commit()

@app.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)

@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    cart = session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    session['cart'] = cart
    flash(f'Товар "{product.name}" добавлен в корзину')
    return redirect(url_for('index'))

@app.route('/cart')
def cart():
    cart_items = []
    total = 0
    cart = session.get('cart', {})
    for product_id, quantity in cart.items():
        product = Product.query.get(int(product_id))
        if product:
            subtotal = product.price * quantity
            total += subtotal
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal
            })
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/update_cart', methods=['POST'])
def update_cart():
    cart = session.get('cart', {})
    for key in list(cart.keys()):
        qty = request.form.get(f'qty_{key}')
        if qty and qty.isdigit() and int(qty) > 0:
            cart[key] = int(qty)
        else:
            del cart[key]
    session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        address = request.form['address']

        cart = session.get('cart', {})
        if not cart:
            flash('Корзина пуста')
            return redirect(url_for('index'))

        order = Order(customer_name=name, customer_email=email, customer_address=address)
        db.session.add(order)
        db.session.flush()

        total = 0
        for product_id, quantity in cart.items():
            product = Product.query.get(int(product_id))
            if product and product.stock >= quantity:
                item_total = product.price * quantity
                total += item_total
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=quantity,
                    price=product.price
                )
                db.session.add(order_item)
                product.stock -= quantity
            else:
                db.session.rollback()
                flash(f'Товар "{product.name}" недоступен в нужном количестве')
                return redirect(url_for('cart'))

        order.total = total
        db.session.commit()

        session.pop('cart', None)
        flash('Заказ успешно оформлен!')
        return redirect(url_for('index'))

    return render_template('checkout.html')

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)