from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from flask import session
from functools import wraps

app = Flask(__name__)

# Configuración para conectarse a MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/sistema_pedidos'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        contraseña = generate_password_hash(request.form['contraseña'])
        rol = request.form['rol']
        
        # Crear nuevo usuario
        nuevo_usuario = Usuario(nombre=nombre, email=email, contraseña=contraseña, rol=rol)
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        return redirect(url_for('login'))
    
    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        contraseña = request.form['contraseña']
        
        # Buscar usuario en la base de datos
        usuario = Usuario.query.filter_by(email=email).first()
        
        # Verificar la contraseña
        if usuario and check_password_hash(usuario.contraseña, contraseña):
            # Iniciar sesión (puedes usar sesiones para mantener al usuario autenticado)
            return redirect(url_for('home'))
        else:
            return 'Credenciales incorrectas'
    
    return render_template('login.html')

    
@app.route('/productos')
def productos():
    # Obtener todos los productos
    productos = Producto.query.all()
    return render_template('productos.html', productos=productos)


@app.route('/agregar_al_carrito/<int:id_producto>')
def agregar_al_carrito(id_producto):
    producto = Producto.query.get_or_404(id_producto)
    
    # Obtener el carrito de la sesión o crearlo si no existe
    carrito = session.get('carrito', [])
    carrito.append({'id_producto': producto.id_producto, 'nombre': producto.nombre_producto, 'precio': producto.precio})
    
    # Guardar el carrito en la sesión
    session['carrito'] = carrito
    
    return redirect(url_for('ver_carrito'))

@app.route('/ver_carrito')
def ver_carrito():
    carrito = session.get('carrito', [])
    return render_template('carrito.html', carrito=carrito)


@app.route('/confirmar_pedido', methods=['POST'])
def confirmar_pedido():
    carrito = session.get('carrito', [])
    
    if carrito:
        # Crear el pedido
        nuevo_pedido = Pedido(id_usuario=session['id_usuario'], fecha_pedido=datetime.now(), estado_pedido='Pendiente')
        db.session.add(nuevo_pedido)
        db.session.commit()
        
        # Agregar los productos al detalle del pedido
        for item in carrito:
            detalle = DetallePedido(
                id_pedido=nuevo_pedido.id_pedido,
                id_producto=item['id_producto'],
                cantidad=item['cantidad'],
                precio_unitario=item['precio'],
                subtotal=item['cantidad'] * item['precio']
            )
            db.session.add(detalle)
        
        db.session.commit()
        
        # Vaciar el carrito
        session['carrito'] = []
        return 'Pedido confirmado exitosamente'
    
    return 'El carrito está vacío'

@app.route('/admin/pedidos')
def admin_pedidos():
    pedidos = Pedido.query.all()
    return render_template('admin_pedidos.html', pedidos=pedidos)


@app.route('/historial_pedidos')
def historial_pedidos():
    pedidos = Pedido.query.filter_by(id_usuario=session['id_usuario']).all()
    return render_template('historial_pedidos.html', pedidos=pedidos)


def login_requerido(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'id_usuario' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrap

def admin_requerido(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if session.get('rol') != 'admin':
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return wrap

@app.route('/')
def index():
    return render_template('index.html')

