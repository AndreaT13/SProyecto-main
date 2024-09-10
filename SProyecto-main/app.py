from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('layout.html', tab='informacion')

@app.route('/pedidos')
def tab1():
    return render_template('layout.html', tab='pedidos')

if __name__ == '__main__':
    app.run(debug=True)