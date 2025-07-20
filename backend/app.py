from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSONB
from flask_migrate import Migrate
import os
import requests

app = Flask(__name__)

# Config
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'postgresql://terrot_gpt_user:password@localhost/terrot_gpt'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


# data Question - id, user, cards,  
# Example model
class Draw(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=False, nullable=False)
    question = db.Column(db.Text, nullable=False)
    cards = db.Column(JSONB, nullable=False)



@app.route('/question', methods=['POST'])
def question():
    # list of json objects {"card_name":"card name", "direction":"up"}
    data = request.get_json()
    print(data)
    cards = data.get("cards")
    question = data.get("question")

    draw = Draw(
        username="default_user",
        question=question,
        cards=cards
    )

    db.session.add(draw)
    db.session.commit()

    return jsonify(
        id=draw.id,
        username=draw.username,
        question=draw.question,
        cards=draw.cards
    ), 201



@app.route("/")
def home():
    response = requests.get("https://tarotapi.dev/api/v1")

    if response.status_code != 200:
        print(response)
        return jsonify(error="Failed to fetch from external API"), 502

    data = response.json()
    return jsonify(data)
    # return jsonify(message="Flask + Postgres + SQLAlchemy ready!")


if __name__ == "__main__":
    app.run(debug=True)
