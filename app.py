from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import logging

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)


@app.route('/')
def home():
    return render_template('weather.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Користувач з таким ім\'ям вже існує.')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Реєстрація пройшла успішно! Тепер ви можете увійти.')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Вхід успішний!')
            return redirect(url_for('home'))
        else:
            flash('Невірне ім\'я користувача або пароль')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Ви вийшли із системи')
    return redirect(url_for('login'))


@app.route('/weather', methods=['GET'])
def get_weather():
    if 'user_id' not in session:
        flash('Будь ласка, увійдіть для перегляду погоди.')
        return redirect(url_for('login'))

    city = request.args.get('city', 'Kharkiv')
    api_key = "5db8796171d7cc86e7f00cd32c4c0361"
    response = get_api(api_key, city)
    return jsonify(response)


def get_api(api_key, city):
    url = "https://api.openweathermap.org/data/2.5/weather"
    response = requests.get(url, params={"q": city, "appid": api_key, "lang": "ua", "units": "metric"})
    app.logger.info(f"Запит до API: {response.url}")
    app.logger.info(f"Статус відповіді: {response.status_code}")
    if response.status_code == 200:
        app.logger.info(f"Дані від API: {response.json()}")
        return response.json()
    return {"error": response.status_code}


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    with app.app_context():
        db.create_all()
    app.run(debug=True)

