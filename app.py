from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', '').replace('postgres://', 'postgresql://')
db = SQLAlchemy(app)


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), unique=True, nullable=False)
    title = db.Column(db.String(200), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    ner_results = db.Column(db.JSON)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/results')
def show_results():
    try:
        recent_articles = Article.query.order_by(Article.id.desc()).limit(16).all()
        valid_results = [article.ner_results for article in recent_articles if article.ner_results and article.ner_results.get('first_named_entity')]
        return render_template('results.html', ner_results=valid_results)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return render_template('error.html', error=str(e)), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5001)))

# comment