from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, JSON, Date
import os
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()

# Use your Heroku DATABASE_URL here
DATABASE_URL = os.environ['HEROKU_DATABASE_URL']
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()

class Article(Base):
    __tablename__ = 'article'
    id = Column(Integer, primary_key=True)
    title = Column(String(200), unique=True, nullable=False)
    content = Column(Text, nullable=False)
    ner_results = Column(JSON)
    date = Column(Date)

def import_to_heroku():
    # Load the exported data
    with open('export.json', 'r') as f:
        articles = json.load(f)

    # Import into Heroku database
    for article_data in articles:
        existing_article = session.query(Article).filter_by(title=article_data['title']).first()
        if not existing_article:
            article = Article(
                title=article_data['title'],
                content=article_data['content'],
                ner_results=article_data['ner_results'],
                date=datetime.strptime(article_data['date'], '%Y-%m-%d').date() if article_data.get('date') else None
            )
            session.add(article)

    session.commit()
    print("Import complete")

def export_to_json():
    articles = session.query(Article).all()
    results = [
        {
            'title': article.title,
            'content': article.content,
            'ner_results': article.ner_results,
            'date': article.date.strftime('%Y-%m-%d') if article.date else None
        }
        for article in articles
    ]
    with open('export.json', 'w') as f:
        json.dump(results, f)
    print("Results exported to export.json")

if __name__ == "__main__":
    # Uncomment the function you want to run
    # import_to_heroku()
    # export_to_json()
    pass