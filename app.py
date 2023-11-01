import os
import json
import sqlite3
from flask import Flask, render_template, request

import openai
openai.api_key = os.getenv("api_key")

def create_connection():
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat (
            id INTEGER PRIMARY KEY,
            messages TEXT
        )
    ''')
    conn.commit()
    return conn

app = Flask(__name__)

@app.after_request
def add_header(response):
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response

@app.route('/delete_chats', methods=['POST'])
def delete_messages():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(' DROP TABLE IF EXISTS chat')

    return {'status': 200}

@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.get_json()
    new_user_message = {"role": "user", "content": data.get('message')}

    conn = create_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT messages FROM chat')
    final_result = cursor.fetchone()
    if final_result:
      new_messages = json.loads(final_result[0])
    else:
      new_messages = [
          {"role": "system", "content": "You are an educational instructor."}
      ]
    new_messages.append(new_user_message)
    completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=new_messages)
    GPT_ANSWER = completion.choices[0].message

    cursor.execute('SELECT messages FROM chat')
    result = cursor.fetchone()

    if result:
        existing_messages = json.loads(result[0])
        existing_messages.append(new_user_message)
        existing_messages.append(GPT_ANSWER)
        cursor.execute('UPDATE chat SET messages=?', (json.dumps(existing_messages),))
    else:
        messages = [new_user_message, GPT_ANSWER]
        cursor.execute('INSERT INTO chat (messages) VALUES (?)', (json.dumps(messages),))

    conn.commit()
    conn.close()

    return {'status': 200}

@app.route('/messages', methods=['GET'])
def messages():
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT messages FROM chat')
    final_result = cursor.fetchone()
    if final_result:
      new_messages = json.loads(final_result[0])
    else:
      new_messages = []

    conn.commit()
    conn.close()
    
    return {'messages': new_messages}

@app.route('/')
def index():
      return render_template('index.html')


if __name__ == '__main__':
      app.run()
