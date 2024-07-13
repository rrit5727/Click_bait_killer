from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
import os
import logging
from dotenv import load_dotenv
from celery import Celery

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL').replace("postgres://", "postgresql://", 1) if os.getenv('DATABASE_URL') else "sqlite:///local.db"

print(f"Connecting to database: {app.config['SQLALCHEMY_DATABASE_URI']}")

db = SQLAlchemy(app)

# Celery configuration
app.config['CELERY_BROKER_URL'] = os.getenv('REDIS_URL')
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

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
    from celery_config import scrape_and_process_articles_task
    task = scrape_and_process_articles_task.delay()
    return f"Scrape and process job started with task id {task.id}. Check logs for details."

# initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=manual_scrape, trigger="interval", hours=3)
logger.info("Scheduler initialized")

if __name__ == "__main__":
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))