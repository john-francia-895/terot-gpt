from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSONB
from flask_migrate import Migrate
import os
import requests
import json
import openai

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
    answer_id = db.Column(db.Integer, nullable=True)


class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)

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

    tarot_data = ''
    with open("backend/resourses/card_data.json") as f:
        tarot_data = json.load(f)

    card_lookup = {card["name"]: card for card in tarot_data["cards"]}

    card_contexts = []
    for c in cards:
        card_info = card_lookup[c["name"]]
        meaning = card_info["meaning_up"] if c["direction"] == "up" else card_info["meaning_rev"]
        card_contexts.append(f"- {card_info['name']} ({c['direction']}): {meaning}")
    


    system_prompt = (
        "You are a wise and intuitive tarot reader who provides spiritual, thoughtful guidance based "
        "on the cards drawn by the user."
    )

    user_prompt = f"""
    A user asks: \"{question}\"

    They drew the following 3 cards:
    {chr(10).join(card_contexts)}

    Please provide a thoughtful, spiritually-guided answer to their question, incorporating the meanings of the cards into your explanation.
    """
    print('user prompt: ' + user_prompt)







    openai.api_key = "api-token"

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",  # or "gpt-3.5-turbo" if desired
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    ai_response = response.choices[0].message.content.strip()

    answer = Answer(content=ai_response)
    db.session.add(answer)
    db.session.commit()

    draw = Draw.query.get(draw.id)
    draw.answer_id = answer.id
    db.session.commit()
    

    return jsonify(
        id=draw.id,
        username=draw.username,
        question=draw.question,
        cards=draw.cards,
        answer=answer.content 
    ), 201



if __name__ == "__main__":
    app.run(debug=True)
