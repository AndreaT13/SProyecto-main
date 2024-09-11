from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import pymysql
from flask import Flask, render_template, request, redirect, url_for, flash, session

pymysql.install_as_MySQLdb()

app = Flask(__name__)

# Configuración de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost:3306/seminario'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo de la tabla de usuarios
class Usuario(db.Model):
    _tablename_ = 'usuarios'
    id_usuario = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    contrasena = db.Column(db.String(100), nullable=False)

# Ruta para el inicio de sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['usuario']
        password = request.form['contrasena']

        user = Usuario.query.filter_by(usuario=username).first()

        if user and user.contrasena == password:
            session['user_id'] = user.id_usuario
            session['username'] = user.usuario
            return redirect(url_for('layout'))
        else:
            flash('Usuario o contraseña incorrectos')

    return render_template('Login.html')

@app.route('/login')
def login_page():
    return render_template('Login.html')

@app.route('/')
def home():
    return render_template('layout.html', tab='informacion')

@app.route('/pedidos')
def tab1():
    return render_template('layout.html', tab='pedidos')

if __name__ == '__main__':
    app.run(debug=True)