from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import pymysql
from flask import request, redirect, url_for, flash, session
from sqlalchemy import DECIMAL

pymysql.install_as_MySQLdb()
app = Flask(__name__, static_folder='static')
app.secret_key = 'ANGIESECRETA'

# Configuración de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost:3306/seminario'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo de la tabla de usuarios
class Usuarios(db.Model):
    __tablename__ = 'usuarios'  # corregido
    id_usuario = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    contrasena = db.Column(db.String(100), nullable=False)

# Modelo de la tabla de clientes
class Clientes(db.Model):
    __tablename__ = 'clientes'  # corregido
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    nit = db.Column(db.String(20), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    direccion = db.Column(db.String(200), nullable=False)

# Modelo de la tabla de productos
class Productos(db.Model):
    __tablename__ = 'productos'
    id = db.Column(db.Integer, primary_key=True)
    producto = db.Column(db.String(50))  # Nombre del producto
    precio = db.Column(db.Float)  # Precio del producto



# Ruta para el inicio de sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['usuario']
        password = request.form['contrasena']

        user = Usuarios.query.filter_by(usuario=username).first()

        if user and user.contrasena == password:
            session['user_id'] = user.id_usuario
            session['username'] = user.usuario
            return redirect(url_for('home'))
        else:
            flash('Usuario o contraseña incorrectos')

    return render_template('Login.html')

@app.route('/')
def home():
    return render_template('layout.html', tab='informacion')

@app.route('/pedidos')
@app.route('/informacion')
def tab1(tab=None):
    if tab is None:
        tab = 'pedidos'
    if tab == 'informacion':
        return render_template('layout.html', tab=tab)
    elif tab == 'pedidos' and 'user_id' not in session:
        return redirect(url_for('login'))

    # Obtener clientes y productos de la base de datos
    clientes = Clientes.query.all()
    productos = Productos.query.all()  # Obtener productos

    # Pasar clientes y productos a la plantilla
    return render_template('layout.html', tab=tab, clientes=clientes, productos=productos)

@app.route('/logout')
def logout():
    # Clear the user's session
    session.clear()
    # Redirect to the login page
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
