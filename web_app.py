from flask import Flask, render_template, redirect, url_for, request, flash, session, abort, jsonify, session
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from models import sample_products
from models import User
import json
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shopping.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'dev-secret'
app.config['JSON_SORT_KEYS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(200), nullable=True)
    stock = db.Column(db.Integer, default=50)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', lazy=True)


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product_name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    qty = db.Column(db.Integer, nullable=False)
    product = db.relationship('Product')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def init_db():
    db.create_all()
    # ensure `image` column exists for older DBs
    try:
        cols = [r[1] for r in db.session.execute("PRAGMA table_info('product')").all()]
        if 'image' not in cols:
            with db.engine.begin() as conn:
                conn.execute("ALTER TABLE product ADD COLUMN image TEXT")
        if 'stock' not in cols:
            with db.engine.begin() as conn:
                conn.execute("ALTER TABLE product ADD COLUMN stock INTEGER DEFAULT 50")
    except Exception:
        pass
    if User.query.filter_by(username='admin').first() is None:
        admin = User(username='admin', password_hash=generate_password_hash('adminpass'), is_admin=True)
        db.session.add(admin)
    if Product.query.count() == 0:
        for p in sample_products:
            db.session.add(Product(id=p['id'], name=p['name'], price=p['price'], image=p.get('image'), stock=50))
    db.session.commit()


# Initialize DB on startup (avoid using `before_first_request` decorator)


def cart_count():
    c = session.get('cart', {})
    return sum(c.values())


# === API ENDPOINTS FOR MOBILE APP ===

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.get_json(force=True)
        username = data.get('username')
        password = data.get('password')

        user = User.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401

        # Store user id in session
        session['user_id'] = user.id

        return jsonify({
            'status': 'success',
            'message': 'Login successful',
            'user_id': user.id
        }), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
@app.route('/api/products', methods=['GET'])
def api_products():
    """Return all products as JSON for mobile app"""
    products = Product.query.order_by(Product.id).all()
    return jsonify([
        {
            'id': p.id,
            'name': p.name,
            'price': p.price,
            'stock': p.stock,
            'image': p.image
        }
        for p in products
    ])


@app.route('/api/products/<int:product_id>', methods=['GET'])
def api_product_detail(product_id):
    """Return specific product details as JSON"""
    product = Product.query.get_or_404(product_id)
    return jsonify({
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'stock': product.stock,
        'image': product.image
    })

@app.route('/api/cart', methods=['GET'])
@login_required
def api_cart():
    """Return current cart as JSON"""
    cart = session.get('cart', {})
    items = []
    total = 0.0
    for pid, qty in cart.items():
        p = Product.query.get(int(pid))
        if p:
            items.append({
                'id': p.id,
                'name': p.name,
                'price': p.price,
                'qty': qty,
                'image': p.image,
                'stock': p.stock
            })
            total += p.price * qty
    return jsonify({'items': items, 'total': total})

@app.route('/api/cart/save', methods=['POST'])
def api_cart_save():
    """Save guest cart to server (no login required)"""
    data = request.get_json() or {}
    cart = data.get('cart', {})
    if not isinstance(cart, dict):
        return jsonify({'success': False, 'message': 'Invalid cart format'}), 400
    
    # Store in session
    session['guest_cart'] = cart
    return jsonify({'success': True, 'message': 'Cart saved', 'cart': cart})

@app.route('/api/cart/load', methods=['GET'])
def api_cart_load():
    """Load guest cart from server (no login required)"""
    cart = session.get('guest_cart', {})
    items = []
    total = 0.0
    for pid, qty in cart.items():
        try:
            p = Product.query.get(int(pid))
            if p:
                items.append({
                    'id': p.id,
                    'name': p.name,
                    'price': p.price,
                    'qty': qty,
                    'image': p.image,
                    'stock': p.stock
                })
                total += p.price * qty
        except Exception:
            continue
    return jsonify({'success': True, 'items': items, 'total': total, 'cart': cart})

@app.route('/api/cart/add', methods=['POST'])
@login_required
def api_cart_add():
    """Add product to cart"""
    data = request.get_json() or {}
    product_id = data.get('product_id')
    qty = int(data.get('qty', 1))
    product = Product.query.get_or_404(product_id)

    if product.stock < qty:
        return jsonify({'success': False, 'message': f'{product.name} only has {product.stock} in stock'}), 400

    cart = session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + qty
    session['cart'] = cart
    return jsonify({'success': True, 'message': f'Added {qty} x {product.name} to cart', 'cart': cart})


@app.route('/api/cart/remove', methods=['POST'])
@login_required
def api_cart_remove():
    """Remove product from cart"""
    data = request.get_json() or {}
    product_id = str(data.get('product_id'))
    cart = session.get('cart', {})
    if product_id in cart:
        cart.pop(product_id)
        session['cart'] = cart
        return jsonify({'success': True, 'message': 'Removed product from cart', 'cart': cart})
    return jsonify({'success': False, 'message': 'Product not in cart'}), 400


@app.route('/api/checkout', methods=['POST'])
def api_checkout():
    try:
        #print(session.cookies)
        
        # 0. Check if user is logged in
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'Login required'
            }), 401

        # 1. Get cart from JSON payload
        data = request.get_json(force=True) or {}
        cart = data.get('cart', {})

        if not cart:
            return jsonify({
                'status': 'error',
                'message': 'Cart is empty'
            }), 400

        total = 0.0
        order_items = []

        # 2. Check stock and calculate total
        for pid_str, qty in cart.items():
            try:
                pid = int(pid_str)
            except ValueError:
                return jsonify({
                    'status': 'error',
                    'message': f'Invalid product id: {pid_str}'
                }), 400

            p = Product.query.get(pid)
            if not p:
                return jsonify({
                    'status': 'error',
                    'message': f'Product {pid} not found'
                }), 404

            if p.stock < qty:
                return jsonify({
                    'status': 'error',
                    'message': f'{p.name} only has {p.stock} in stock'
                }), 400

            total += p.price * qty
            order_items.append((p, qty))

        # 3. Create order with logged-in user
        order = Order(user_id=user_id, total=total)
        db.session.add(order)
        db.session.commit()

        # 4. Add order items and decrement stock
        for p, qty in order_items:
            oi = OrderItem(
                order_id=order.id,
                product_id=p.id,
                product_name=p.name,
                price=p.price,
                qty=qty
            )
            db.session.add(oi)
            p.stock -= qty

        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Order placed successfully',
            'order_id': order.id,
            'total': total
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Database error: {str(e)}'
        }), 500

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }), 500


@app.route('/api/orders', methods=['GET'])
@login_required
def api_orders():
    """Return all orders for the current user"""
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    results = []
    for o in orders:
        items = [{
            'product_id': i.product_id,
            'product_name': i.product_name,
            'qty': i.qty,
            'price': i.price
        } for i in o.items]
        results.append({
            'order_id': o.id,
            'total': o.total,
            'created_at': o.created_at.isoformat(),
            'items': items
        })
    return jsonify(results)
# === WEB ROUTES ===

@app.route('/')
def index():
    q = request.args.get('q', '').strip()
    products = Product.query.order_by(Product.id).all()
    if q:
        products = [p for p in products if q.lower() in p.name.lower()]
    return render_template('index.html', products=products, cart_count=cart_count(), search_query=q)


@app.route('/add/<int:product_id>')
def add(product_id):
    product = Product.query.get_or_404(product_id)
    if product.stock <= 0:
        flash('Product out of stock', 'danger')
        return redirect(url_for('index'))
    cart = session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    session['cart'] = cart
    flash(f'Added {product.name} to cart', 'success')
    return redirect(url_for('index'))


@app.route('/cart')
def show_cart():
    cart = session.get('cart', {})
    items = []
    total = 0.0
    for pid, qty in cart.items():
        p = Product.query.get(int(pid))
        if p:
            items.append({'id': p.id, 'name': p.name, 'price': p.price, 'qty': qty, 'image': p.image})
            total += p.price * qty
    return render_template('cart.html', items=items, total=total)


@app.route('/remove/<int:product_id>')
def remove(product_id):
    cart = session.get('cart', {})
    cart.pop(str(product_id), None)
    session['cart'] = cart
    return redirect(url_for('show_cart'))


@app.route('/checkout')
def checkout():
    if not current_user.is_authenticated:
        flash('Please log in to checkout', 'danger')
        return redirect(url_for('login'))
    cart = session.get('cart', {})
    total = 0.0
    order_items = []
    for pid, qty in cart.items():
        p = Product.query.get(int(pid))
        if p:
            if p.stock < qty:
                flash(f'{p.name} only has {p.stock} in stock', 'danger')
                return redirect(url_for('show_cart'))
            total += p.price * qty
            order_items.append((p, qty))
    # Create order record
    order = Order(user_id=current_user.id, total=total)
    db.session.add(order)
    db.session.commit()
    # Add order items and decrement stock
    for p, qty in order_items:
        oi = OrderItem(order_id=order.id, product_id=p.id, product_name=p.name, price=p.price, qty=qty)
        db.session.add(oi)
        p.stock -= qty
    db.session.commit()
    session['cart'] = {}
    return render_template('checkout.html', total=total, order_id=order.id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in', 'success')
            return redirect(url_for('index'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash('Username and password required', 'danger')
            return render_template('signup.html')
        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'danger')
            return render_template('signup.html')
        user = User(username=username, password_hash=generate_password_hash(password), is_admin=False)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('Account created and logged in', 'success')
        return redirect(url_for('index'))
    return render_template('signup.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out', 'info')
    return redirect(url_for('index'))


def admin_required(func):
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, 'is_admin', False):
            abort(403)
        return func(*args, **kwargs)

    return wrapper


@app.route('/admin')
@login_required
@admin_required
def admin():
    products = Product.query.order_by(Product.id).all()
    return render_template('admin.html', products=products)


@app.route('/admin/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add():
    if request.method == 'POST':
        name = request.form.get('name')
        price = float(request.form.get('price') or 0)
        stock = int(request.form.get('stock') or 50)
        p = Product(name=name, price=price, stock=stock)
        # handle image upload
        f = request.files.get('image_file')
        if f and f.filename:
            uploads = os.path.join(app.root_path, 'static', 'uploads')
            os.makedirs(uploads, exist_ok=True)
            filename = secure_filename(f.filename)
            path = os.path.join(uploads, filename)
            f.save(path)
            p.image = f'static/uploads/{filename}'
        db.session.add(p)
        db.session.commit()
        flash('Product added', 'success')
        return redirect(url_for('admin'))
    return render_template('product_form.html', action='Add')


@app.route('/admin/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit(product_id):
    p = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        p.name = request.form.get('name')
        p.price = float(request.form.get('price') or 0)
        p.stock = int(request.form.get('stock') or 50)
        # handle image upload
        f = request.files.get('image_file')
        if f and f.filename:
            uploads = os.path.join(app.root_path, 'static', 'uploads')
            os.makedirs(uploads, exist_ok=True)
            filename = secure_filename(f.filename)
            path = os.path.join(uploads, filename)
            f.save(path)
            p.image = f'static/uploads/{filename}'
        db.session.commit()
        flash('Product updated', 'success')
        return redirect(url_for('admin'))
    return render_template('product_form.html', action='Edit', product=p)


@app.route('/admin/delete/<int:product_id>', methods=['POST', 'GET'])
@login_required
@admin_required
def admin_delete(product_id):
    p = Product.query.get_or_404(product_id)
    db.session.delete(p)
    db.session.commit()
    flash('Product deleted', 'info')
    return redirect(url_for('admin'))


@app.route('/orders')
@login_required
def user_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('orders.html', orders=orders)


@app.route('/admin/stock')
@login_required
@admin_required
def admin_stock():
    products = Product.query.order_by(Product.id).all()
    return render_template('stock.html', products=products)


if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
