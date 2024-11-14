from flask import Flask, render_template, send_file
from flask_sqlalchemy import SQLAlchemy
import pymysql
from datetime import datetime
from flask import request, redirect, url_for, flash, session
from flask import jsonify
import json
import mysql.connector
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from io import BytesIO
from fpdf import FPDF
import tempfile
from datetime import date
from fpdf.enums import XPos, YPos
import io



pymysql.install_as_MySQLdb()
app = Flask(__name__, static_folder='static')
app.secret_key = 'KEYSECRET'

# Configuración de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost:3306/seminario'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo de la tabla de usuarios
class Usuarios(db.Model):
    __tablename__ = 'usuarios'
    id_usuario = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    contrasena = db.Column(db.String(100), nullable=False)
    rol = db.Column(db.String(10), nullable=False)  # Rol: admin o user


# Modelo de la tabla de clientes
class Clientes(db.Model):
    __tablename__ = 'clientes'
    id_cliente = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    correo = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    direccion = db.Column(db.String(200), nullable=False)

# Modelo de la tabla de productos
class Productos(db.Model):
    __tablename__ = 'producto'
    id_producto = db.Column(db.Integer, primary_key=True)
    producto = db.Column(db.String(50))  # Nombre del producto
    precio = db.Column(db.Float)  # Precio del producto
    id_categoria = db.Column(db.String(255))

class Pedido(db.Model):
    __tablename__ = 'pedido'
    id_pedido = db.Column(db.Integer, primary_key=True)
    id_cliente = db.Column(db.String(50), nullable=False)
    nombre_cliente = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(200), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    estado = db.Column(db.String(20), nullable=False, default='Pendiente')  # Campo para el estado del pedido


    detalles = db.relationship('DetallePedido', back_populates='pedido', cascade='all, delete-orphan')


class DetallePedido(db.Model):
    __tablename__ = 'detalle_pedido'
    id_detalle = db.Column(db.Integer, primary_key=True)
    id_pedido = db.Column(db.Integer, db.ForeignKey('pedido.id_pedido'), nullable=False)
    codigo_producto = db.Column(db.String(8), nullable=False)
    nombre_producto = db.Column(db.String(100), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)



    pedido = db.relationship('Pedido', back_populates='detalles')

# Ruta para crear un usuario
@app.route('/crear-usuario', methods=['GET', 'POST'])
def crear_usuario():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contrasena = request.form['contrasena']
        rol = request.form['rol']

        # Verificar si el usuario ya existe
        usuario_existente = Usuarios.query.filter_by(usuario=usuario).first()
        
        if usuario_existente:
            flash('Usuario existente. Intenta con otro nombre de usuario.', 'error')
            return redirect(url_for('crear_usuario'))
        
        # Crear un nuevo usuario si no existe
        nuevo_usuario = Usuarios(usuario=usuario, contrasena=contrasena, rol=rol)
        
        try:
            # Guardar el usuario en la base de datos
            db.session.add(nuevo_usuario)
            db.session.commit()
            flash('Usuario creado exitosamente!', 'success')
            return redirect(url_for('mostrar_usuarios'))  # Redireccionar a la página de usuarios
        except Exception as e:
            flash('Ocurrió un error al crear el usuario.', 'error')
            db.session.rollback()  # Revertir cambios en caso de error

    return render_template('usuarios.html')


@app.route('/registrar_cliente', methods=['GET', 'POST'])
def registrar_cliente():
    if request.method == 'POST':
        nombre=request.form['nombre']
        direccion=request.form['direccion']
        telefono=request.form['telefono']
        correo=request.form['correo']

        cliente_existente = Clientes.query.filter_by(nombre=nombre).first()

        if cliente_existente:
            flash('Nombre de cliente existente', 'error')
            return redirect(url_for('mostrar_clientes'))

        nuevo_cliente = Clientes(
            id_cliente=id,
            nombre=nombre,
            direccion=direccion,
            telefono=telefono,
            correo=correo
        )
        db.session.add(nuevo_cliente)
        db.session.commit()
        flash('Cliente registrado exitosamente!', 'success')
        return redirect(url_for('mostrar_clientes'))
    return render_template('clientes.html') 

@app.route('/crear_producto', methods=['GET', 'POST'])
def crear_producto():
    if request.method == 'POST':
        id_producto = request.form['id_producto']
        producto = request.form['nombre']
        precio = request.form['precio']
        id_categoria = request.form['id_categoria']
        #descripcion = request.form['descripcion']

        # Verificar si el ID del producto ya existe
        existe_producto = Productos.query.filter_by(id_producto=id_producto).first()
        
        if existe_producto:
            flash('El Código del producto ya existe. Por favor, ingrese uno diferente.', 'error')
            return redirect(url_for('mostrar_productos'))

        nuevo_producto = Productos(
            id_producto=id_producto,
            producto=producto,
            precio=precio,
            id_categoria=id_categoria,
           # descripcion=descripcion
        )
        db.session.add(nuevo_producto)
        db.session.commit()
        flash('Producto creado exitosamente!', 'success')
        return redirect(url_for('mostrar_productos'))

    return render_template('productos.html')

@app.route('/guardar_pedido', methods=['POST'])
def guardar_pedido():

    try:

        data = request.get_json()
        productos = data.get('productos', [])


        if not data:
            return jsonify({"success": False, "message": "No se recibieron datos."}), 400

        id_cliente = data.get('id_cliente')
        nombre_cliente = data.get('nombre_cliente')
        direccion = data.get('direccion')
        productos = data.get('productos', [])
        fecha = datetime.now()  # Fecha actual

        if not id_cliente or not nombre_cliente or not direccion:
            return jsonify({"success": False, "message": "Faltan datos del cliente."}), 400

        nuevo_pedido = Pedido(
        id_cliente=id_cliente,
        nombre_cliente=nombre_cliente,
        direccion=direccion,
        fecha=fecha
    )
        db.session.add(nuevo_pedido)
        db.session.commit()

        for producto in productos:
            nuevo_detalle = DetallePedido(
            id_pedido=nuevo_pedido.id_pedido,
            codigo_producto=producto['id_producto'],
            nombre_producto=producto['nombre_producto'],
            cantidad=producto['cantidad'],
            precio=producto['precio'],
            subtotal=producto['subtotal']
        )
        db.session.add(nuevo_detalle)

        db.session.commit()
        return jsonify({"success": True, "id_pedido": nuevo_pedido.id_pedido})
    except Exception as e:
        # Manejo de errores
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/crear_pedidos', methods=['GET'])
def crear_pedidos():
   # cursor = mysql.connection.cursor()

    # Consulta para obtener el último id_pedido
    #cursor.execute("SELECT ifnull(MAX(id_pedido),1) FROM pedido;")
   # resultado = cursor.fetchone()

    # Si no hay ningún pedido, empieza en 1
   # if resultado[0] is None:
   #     siguiente_pedido_id = 1
   # else:
    #    siguiente_pedido_id = resultado[0] + 1

    #cursor.close()

    # Renderiza la página del formulario y pasa el siguiente número de pedido
    return render_template('uso.html', pedido_id=1)


# Ruta para el inicio de sesión-
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contrasena = request.form['contrasena']
        # Verificar las credenciales
        user = Usuarios.query.filter_by(usuario=usuario, contrasena=contrasena).first()
        if user:
            session['user_id'] = user.id_usuario  # Guarda el ID de usuario en la sesión
            return redirect(url_for('uso'))   # Redirige a la página de pedidos
        else:
            flash('Credenciales incorrectas, intenta nuevamente','danger')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/capa1')
def capa1():
    return render_template('capa1.html')


from flask import request, jsonify

@app.route('/api/clientes', methods=['GET'])
def api_mostrar_clientes():
    nombre = request.args.get('nombre', '').strip()  # Obtener el filtro de nombre si existe

    # Conectar a la base de datos MySQL
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="seminario"
    )
    mycursor = db.cursor(dictionary=True)

    # Consulta SQL para buscar clientes por nombre
    if nombre:
        query = "SELECT id_cliente, nombre, direccion FROM clientes WHERE nombre LIKE %s"
        mycursor.execute(query, (f"%{nombre}%",))
    else:
        query = "SELECT id_cliente, nombre, direccion FROM clientes"
        mycursor.execute(query)

    clientes = mycursor.fetchall()
    db.close()

    # Devolver los clientes en formato JSON
    return jsonify(clientes)

@app.route('/api/productos', methods=['GET'])
def api_mostrar_productos():
    # Obtener el parámetro 'nombre' del frontend (que corresponde a 'producto' en la base de datos)
    producto = request.args.get('nombre', '').strip()

    # Conectar a la base de datos MySQL
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="seminario"
    )
    mycursor = db.cursor(dictionary=True)

    # Consulta SQL para buscar productos
    if producto:
        query = "SELECT id_producto, producto, precio FROM producto WHERE producto LIKE %s"
        mycursor.execute(query, (f"%{producto}%",))
    else:
        query = "SELECT id_producto, producto, precio FROM producto"
        mycursor.execute(query)

    productos = mycursor.fetchall()
    db.close()

    # Formatear la respuesta JSON
    return jsonify(productos)



@app.route('/api/pedidos', methods=['GET'])
def obtener_pedidos():
    pedidos = Pedido.query.all()  # Obtén todos los pedidos desde la base de datos
    pedidos_json = []
    for pedido in pedidos:
        detalles = DetallePedido.query.filter_by(id_pedido=pedido.id_pedido).all()
        detalles_json = [{
            "codigo_producto": detalle.codigo_producto,
            "nombre_producto": detalle.nombre_producto,
            "cantidad": detalle.cantidad,
            "precio": detalle.precio,
            "subtotal": detalle.subtotal
        } for detalle in detalles]
        pedidos_json.append({
            "id_pedido": pedido.id_pedido,
            "fecha": pedido.fecha.isoformat(),
            "estado": pedido.estado,
            "cliente": pedido.nombre_cliente,  # Aquí traemos el nombre del cliente
            "detalles": detalles_json
        })
    return jsonify(pedidos_json)

@app.route('/api/pedidos/<int:id_pedido>', methods=['POST'])
def actualizar_estado(id_pedido):
    try:
        # Leer el nuevo estado desde la solicitud JSON
        data = request.get_json()
        nuevo_estado = data.get('estado')

        if not nuevo_estado:
            return jsonify({"success": False, "message": "No se recibió el nuevo estado."}), 400

        # Buscar el pedido en la base de datos
        pedido = Pedido.query.get(id_pedido)

        if not pedido:
            return jsonify({"success": False, "message": "El pedido no existe."}), 404

        # Actualizar el estado del pedido
        pedido.estado = nuevo_estado
        db.session.commit()

        return jsonify({"success": True, "message": "Estado del pedido actualizado con éxito."}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Error al actualizar el estado del pedido: {str(e)}"}), 500

@app.route('/api/pedidos/<int:id_pedido>', methods=['DELETE'])
def eliminar_pedido(id_pedido):
    pedido = Pedido.query.get(id_pedido)
    if not pedido:
        return jsonify({"message": "Pedido no encontrado"}), 404
    DetallePedido.query.filter_by(id_pedido=id_pedido).delete()  # Elimina los detalles asociados
    db.session.delete(pedido)
    db.session.commit()
    return jsonify({"message": "Pedido eliminado correctamente"})

@app.route('/mostrar_clientes' , methods=['GET'])
def mostrar_clientes():
    clientes = Clientes.query.all()  # Obtiene todos los clientes
    print(f"Clientes encontrados: {len(clientes)}")  # Para depuración
    print(clientes)  # Depuración para ver si se obtienen clientes
    return render_template('clientes.html', clientes=clientes)

def obtener_clientes():
    # Conectar a la base de datos MySQL
  
    db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
   database="seminario"
)
    mycursor = db.cursor(dictionary=True)
    mycursor.execute("SELECT id_cliente, nombre, direccion, telefono, correo FROM clientes")
    clientes = mycursor.fetchall()
    db.close()
    return clientes

@app.route('/descargar_pdf_clientes', methods=['GET'])
def descargar_pdf_clientes():
    clientes = obtener_clientes()

    # Crear un archivo temporal para el PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        # Crear una instancia de FPDF
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Título del documento
        pdf.set_font("Helvetica", 'B', 16)
        pdf.cell(0, 10, '********CLIENTES********', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        pdf.ln(10)  # Espacio entre el título y la tabla

        # Estilo de la tabla
        pdf.set_font("Helvetica", 'B', 12)
        pdf.set_fill_color(200, 220, 255)  # Color de fondo para el encabezado
        pdf.cell(25, 10, 'Código', border=1, align='C', fill=True)
        pdf.cell(60, 10, 'Nombre', border=1, align='C', fill=True)
        pdf.cell(50, 10, 'Dirección', border=1, align='C', fill=True)
        pdf.cell(30, 10, 'Teléfono', border=1, align='C', fill=True)
        pdf.ln()

        pdf.set_font("Helvetica", '', 12)
        for index, cliente in enumerate(clientes):
            fill = index % 2 == 0  # Alternar el color de fondo para cada fila
            pdf.set_fill_color(240, 240, 240) if fill else pdf.set_fill_color(255, 255, 255)
            pdf.cell(25, 10, str(cliente['id_cliente']), border=1, align='C', fill=fill)
            pdf.cell(60, 10, cliente['nombre'], border=1, fill=fill)
            pdf.cell(50, 10, cliente['direccion'], border=1, fill=fill)
            pdf.cell(30, 10, cliente['telefono'], border=1, align='C', fill=fill)
            pdf.ln()

        # Guardar el PDF en el archivo temporal
        pdf.output(temp_file.name)

    # Devolver el PDF como respuesta
    return send_file(temp_file.name, as_attachment=True, download_name='clientes.pdf', mimetype='application/pdf')

def obtener_productos():
    # Conectar a la base de datos MySQL
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  # Cambia según tu configuración
        database="seminario"  # Cambia al nombre de tu base de datos
    )
    mycursor = db.cursor(dictionary=True)
    mycursor.execute("SELECT id_producto, producto, precio FROM producto")  # Cambia el nombre de la tabla y las columnas si es necesario
    productos = mycursor.fetchall()
    db.close()
    return productos

@app.route('/mostrar_productos', methods=['GET'])
def mostrar_productos():
    print("Mostrar productos")
    productos = Productos.query.all()  # Usar SQLAlchemy para obtener productos
    return render_template('productos.html', productos=productos )  # Asegúrate de que el nombre del HTML sea correcto

@app.route('/descargar_pdf_productos', methods=['GET'])
def descargar_pdf_productos():
    productos = obtener_productos()

    # Crear un archivo temporal para el PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        # Crear una instancia de FPDF
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Título del documento
        pdf.set_font("Helvetica", 'B', 16)
        pdf.cell(0, 10, '********PRODUCTOS********', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        pdf.ln(10)  # Espacio entre el título y la tabla

        # Estilo de la tabla
        pdf.set_font("Helvetica", 'B', 12)
        pdf.set_fill_color(200, 220, 255)  # Color de fondo para el encabezado
        pdf.cell(25, 10, 'Código', border=1, align='C', fill=True)
        pdf.cell(100, 10, 'Producto', border=1, align='C', fill=True)
        pdf.cell(30, 10, 'Precio', border=1, align='C', fill=True)
        pdf.ln()

        pdf.set_font("Helvetica", '', 12)
        for index, producto in enumerate(productos):
            fill = index % 2 == 0  # Alternar el color de fondo para cada fila
            pdf.set_fill_color(240, 240, 240) if fill else pdf.set_fill_color(255, 255, 255)
            pdf.cell(25, 10, str(producto['id_producto']), border=1, align='C', fill=fill)
            pdf.cell(100, 10, producto['producto'], border=1, fill=fill)
            pdf.cell(30, 10, f"Q{producto['precio']:.2f}", border=1, align='R', fill=fill)
            pdf.ln()

        # Guardar el PDF en el archivo temporal
        pdf.output(temp_file.name)

    # Devolver el PDF como respuesta
    return send_file(temp_file.name, as_attachment=True, download_name='productos.pdf', mimetype='application/pdf')

@app.route('/')
def inicio():
    return render_template('layout3.html')

@app.route('/mascotas')
def mascotas():
    productos = Productos.query.all()  # Obtener productos de la base de datos
    return render_template('mascotas.html', productos=productos)

@app.route('/animales')
def animales():
    return render_template('animales.html')

@app.route('/sucursales')
def sucursales():
    return render_template('sucursales.html')

@app.route('/uso')
def uso():
    if 'user_id' not in session:  # Verificar si el usuario está autenticado
        return redirect(url_for('login'))  # Redirigir al login si no está autenticado
    return render_template('uso.html')  # Muestra la página de pedidos si está autenticado

@app.route('/productos/mascotas')
def mostrar_mascotas():
   productos = Productos.query.filter_by(categoria=1).all()  # Filtra productos de la categoría 'mascotas'
   return render_template('mascotas.html', productos=productos)

@app.route('/productos/animales')
def mostrar_animales():
    productos = Productos.query.filter_by(categoria=2).all()  # Filtra productos de la categoría 'animales'
    return render_template('animales.html', productos=productos)

@app.route('/eliminar_cliente/<int:id_cliente>', methods=['DELETE'])
def eliminar_cliente(id_cliente):
    cliente = Cliente.query.get(id_cliente)
    if cliente:
        try:
            db.session.delete(cliente)
            db.session.commit()
            return jsonify({'success': True}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
    return jsonify({'success': False, 'error': 'Cliente no encontrado'}), 404

@app.route('/editar_cliente/<int:id_cliente>', methods=['GET', 'POST'])
def editar_cliente(id_cliente):
    cliente = Cliente.query.get(id_cliente)
    
    if request.method == 'POST':
        # Actualizar los datos del cliente con lo enviado por el formulario
        cliente.nombre = request.form['nombre']
        cliente.direccion = request.form['direccion']
        cliente.telefono = request.form['telefono']
        cliente.correo = request.form['correo']
        
        try:
            db.session.commit()
            return redirect(url_for('listar_clientes'))  # Vuelve a la lista de clientes
        except Exception as e:
            db.session.rollback()
            return f"Hubo un error al actualizar: {e}"
    
    # Renderizar el formulario con los datos actuales del cliente
    return render_template('editar_cliente.html', cliente=cliente)

@app.route('/eliminar_producto/<int:id_producto>', methods=['DELETE'])
def eliminar_producto(id_producto):
    producto = Producto.query.get(id_producto)
    if producto:
        try:
            db.session.delete(producto)
            db.session.commit()
            return jsonify({'success': True}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
    return jsonify({'success': False, 'error': 'Producto no encontrado'}), 404



@app.route('/editar_producto/<int:id_producto>', methods=['GET', 'POST'])
def editar_producto(id_producto):
    producto = Producto.query.get(id_producto)
    
    if request.method == 'POST':
        producto.producto = request.form['producto']
        producto.precio = request.form['precio']
        
        try:
            db.session.commit()
            return redirect(url_for('listar_productos'))
        except Exception as e:
            db.session.rollback()
            return f"Error al actualizar producto: {e}"
    
    return render_template('editar_producto.html', producto=producto)

@app.route('/crear_pedido', methods=['POST'])
def crear_pedido():
    data = request.get_json()  # Obtener el cuerpo de la solicitud como JSON
    if not data:
        return jsonify({'message': 'No se recibieron datos JSON'}), 400

    id_cliente = data.get('id_cliente')
    nombre_cliente = data.get('nombreCliente')
    direccion = data.get('direccion')
    listar_productos = data.get('productos', [])  # Obtener los productos del JSON

    # Verificar que los datos del cliente no sean nulos
    if not id_cliente or not nombre_cliente or not direccion:
        return jsonify({'message': 'Faltan datos del cliente'}), 400
    
    # Crear el pedido principal
    nuevo_pedido = Pedido(
        id_cliente=id_cliente,
        nombre_cliente=nombre_cliente,
        direccion=direccion,
        fecha=date.today()
    )
    
    db.session.add(nuevo_pedido)
    db.session.commit()  # Guardamos el pedido para obtener su `id_pedido`

    # Guardar cada producto en `detalle_pedido`
    for producto in listar_productos:
        nuevo_detalle = DetallePedido(
            id_pedido=nuevo_pedido.id_pedido,
            codigo_producto=producto['nombre'],
            cantidad=producto['cantidad'],
            precio=producto['precio'],
            subtotal=producto['cantidad'] * producto['precio']
        )
        db.session.add(nuevo_detalle)

    db.session.commit()  # Guarda todos los productos del pedido

    return jsonify({'message': 'Pedido y detalles guardados correctamente'}), 201

@app.route('/administrar_pedidos', methods=['GET'])
def administrar_pedidos():
    return render_template('pedidos.html')  # Archivo HTML con la tabla de pedidos

class PDF(FPDF):
    def header(self):
        # Logo
        self.image('SProyecto-main\static\Imagenes\logo.jpg', 10, 8, 19)  # Asegúrate de tener un archivo de logo
        self.set_font('Arial', 'B', 16)
        self.cell(0, 15, 'RECIBO', border=False, ln=True, align='C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', align='C')

@app.route('/pedido/<int:id_pedido>/detalle-pdf', methods=['GET'])
def generar_detalle_pedido_pdf(id_pedido):
    # Obtener el pedido y los detalles
    pedido = Pedido.query.get_or_404(id_pedido)
    detalles = DetallePedido.query.filter_by(id_pedido=id_pedido).all()

    # Crear el PDF
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)

    # Información del pedido
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "Información del Pedido", ln=True, align="L")
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 10, f"ID Pedido: {pedido.id_pedido}", ln=True, align="L")
    pdf.cell(0, 10, f"Cliente: {pedido.nombre_cliente}", ln=True, align="L")
    pdf.cell(0, 10, f"Dirección: {pedido.direccion}", ln=True, align="L")
    pdf.cell(0, 10, f"Fecha: {pedido.fecha.strftime('%d/%m/%Y')}", ln=True, align="L")
    pdf.cell(0, 10, f"Estado: {pedido.estado}", ln=True, align="L")
    pdf.ln(10)

    # Tabla de detalles del pedido
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "Detalles", ln=True, align="L")
    pdf.set_font('Arial', 'B', 10)

    # Encabezados de la tabla
    pdf.cell(30, 10, "Cantidad", border=1, align='C')
    pdf.cell(80, 10, "Producto", border=1, align='C')
    pdf.cell(30, 10, "Precio (Q)", border=1, align='C')
    pdf.cell(30, 10, "Subtotal (Q)", border=1, align='C')
    pdf.ln()

    # Contenido de la tabla
    pdf.set_font('Arial', '', 10)
    for detalle in detalles:
        pdf.cell(30, 10, str(detalle.cantidad), border=1, align='C')
        pdf.cell(80, 10, detalle.nombre_producto, border=1)
        pdf.cell(30, 10, f"{detalle.precio:.2f}", border=1, align='R')
        pdf.cell(30, 10, f"{detalle.subtotal:.2f}", border=1, align='R')
        pdf.ln()

    # Total
    pdf.set_font('Arial', 'B', 10)
    total = sum(detalle.subtotal for detalle in detalles)
    pdf.cell(140, 10, "Total (Q):", border=1, align='R')
    pdf.cell(30, 10, f"{total:.2f}", border=1, align='R')
    pdf.ln(10)

    # Enviar el PDF como respuesta
    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)
    
    return send_file(pdf_output, as_attachment=True, download_name=f"recibo_pedido_{id_pedido}.pdf", mimetype="application/pdf")

@app.route('/api/pedidos', methods=['GET'])
def obtener_pedidos_filtrados():
    # Obtener los parámetros de los filtros
    cliente = request.args.get('cliente', default=None)
    fecha_inicio = request.args.get('fecha_inicio', default=None)
    fecha_fin = request.args.get('fecha_fin', default=None)

    # Construir la consulta base
    query = Pedido.query

    # Filtrar por cliente (si se especifica)
    if cliente:
        query = Pedido.query.filter(func.trim(Pedido.nombre_cliente).ilike(f"%{cliente}%"))
        print(query)  # Muestra la consulta generada




    # Ejecutar la consulta y devolver los resultados
    pedidos = query.all()

    # Convertir los resultados en JSON
    pedidos_json = [
        {
            "id_pedido": pedido.id_pedido,
            "nombre_cliente": pedido.nombre_cliente,
            "fecha": pedido.fecha.strftime("%Y-%m-%d"),
            "estado": pedido.estado,
        }
        for pedido in pedidos
    ]

    return jsonify({"success": True, "pedidos": pedidos_json})

@app.route('/logout')
def logout():
    # Clear the user's session
    session.clear()
    # Redirect to the login page
    return redirect(url_for('inicio'))

if __name__ == '__main__':
    app.run(debug=True)
