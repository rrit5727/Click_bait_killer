from flask import Flask, render_template, request
from Fetch_and_analyse import scrape_articles, filter_articles_with_vague_references, perform_ner_on_articles
import spacy
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
import os
import logging
from dotenv import load_dotenv

load_dotenv()


try:
    nlp = spacy.load("en_core_web_sm")
except:
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
db = SQLAlchemy(app)

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), unique=True, nullable=False )
    content = db.Column(db.Text, nullable=False)
    ner_results = db.Column(db.JSON)

def scrape_and_process_articles():
    logging.info("Starting scrape and process job")
    scraped_articles = scrape_articles()

    for article in scrape_articles: 
        existing_article = Article.query.filter_by(title=article['title']).first()
        if not existing_article:
            refined_article = filter_articles_with_vague_references([article])[0]
            if refined_article:
                ner_results = perform_ner_on_articles([refined_article])[0]
                new_article = Article(title=refined_article['title'], content=refined_article['content'], ner_results=ner_results)
                db.session.add(new_article)
    db.session.commit()
    logging.info("Completed scrape and process job")



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/results', methods=['POST'])
def show_results():
    recent_articles = Article.query.order_by(Article.id.desc()).limit(10).all()
    return render_template('results.html', ner_results=[article.ner_results for article in recent_articles])

# initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=scrape_and_process_articles, trigger="interval", hours=3)
scheduler.start()



if __name__ == "__main__":
    # create tables
    with app.app_context():
        db.create_all()


    # start the flask app
    app.run(debug=True)