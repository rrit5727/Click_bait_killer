from flask import Flask, render_template, request
from Fetch_and_analyse import scrape_articles, filter_articles_with_vague_references, perform_ner_on_articles
import spacy
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    nlp = spacy.load("en_core_web_sm")
except Exception as e:
    logger.error(f"Error loading spaCy model: {str(e)}")
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL').replace("postgres://", "postgresql://", 1) if os.getenv('DATABASE_URL') else "sqlite:///local.db"

print(f"Connecting to database: {app.config['SQLALCHEMY_DATABASE_URI']}")

db = SQLAlchemy(app)

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    ner_results = db.Column(db.JSON)

def init_db():
    with app.app_context():
        inspector = db.inspect(db.engine)
        if not inspector.has_table("article"):
            db.create_all()
            print("Database tables created.")
        else:
            print("Database tables already exist.")

def scrape_and_process_articles():
    try:
        logging.info("Starting scrape and process job")
        scraped_articles = scrape_articles()
        logging.info(f"Scraped {len(scraped_articles)} articles")
        
        new_articles_count = 0
        for article in scraped_articles:
            existing_article = Article.query.filter_by(title=article['title']).first()
            if not existing_article:
                adjusted_article = {
                    'title': article['title'],
                    'headline': article['title'],
                    'full_text': article['first_512_chars'],
                    'article_url': article['article_url'],
                    'image_url': article['image_url']
                }
                refined_articles = filter_articles_with_vague_references([adjusted_article])
                if refined_articles:
                    refined_article = refined_articles[0]
                    ner_results = perform_ner_on_articles([refined_article])[0]
                    new_article = Article(title=refined_article['headline'], content=refined_article['full_text'], ner_results=ner_results)
                    db.session.add(new_article)
                    new_articles_count += 1
        
        db.session.commit()
        logging.info(f"Completed scrape and process job. Added {new_articles_count} new articles.")
    except Exception as e:
        logging.error(f"Error in scrape_and_process_articles: {str(e)}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/results', methods=['POST'])
def show_results():
    recent_articles = Article.query.order_by(Article.id.desc()).limit(16).all()
    logging.info(f"Found {len(recent_articles)} recent articles")

    valid_results = [article.ner_results for article in recent_articles if article.ner_results.get('first_named_entity')]
    logging.info(f"Found {len(valid_results)} valid results")

    return render_template('results.html', ner_results=valid_results)

@app.route('/debug')
def debug():
    articles = Article.query.all()
    return f"Total articles: {len(articles)}"

@app.route('/scrape')
def manual_scrape():
    scrape_and_process_articles()
    return "Scrape and process job completed. Check logs for details."

# initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=scrape_and_process_articles, trigger="interval", hours=3)
logger.info("Scheduler initialized")

if __name__ == "__main__":
    init_db()
    scheduler.start()
    logger.info("Scheduler started")
    scrape_and_process_articles()  # Run immediately
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))