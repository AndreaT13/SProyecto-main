# En el archivo .py
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/detalle')
def detalle():
    # Obteniendo la lista de solicitudes para pasarla a la plantilla
    solicitudes = D_Solicitud_Alimento.query.all()  # Ejemplo usando SQLAlchemy
    return render_template('detalle.html', solicitudes=solicitudes)

if __name__ == '__main__':
    app.run(debug=True)
