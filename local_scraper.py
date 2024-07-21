from Fetch_and_analyse import scrape_articles, filter_articles_with_vague_references, perform_ner_on_articles
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to your local database
engine = create_engine(os.getenv('LOCAL_DATABASE_URL'))
Session = sessionmaker(bind=engine)
session = Session()

# Define Article model (same as in app.py)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, JSON

Base = declarative_base()

class Article(Base):
    __tablename__ = 'article'
    id = Column(Integer, primary_key=True)
    title = Column(String(200), unique=True, nullable=False)
    content = Column(Text, nullable=False)
    ner_results = Column(JSON)

def scrape_and_analyze():
    scraped_articles = scrape_articles()
    new_articles_count = 0
    for article in scraped_articles:
        existing_article = session.query(Article).filter_by(title=article['title']).first()
        if not existing_article:
            adjusted_article = {
                'title': article['title'],
                'headline': article['title'],
                'full_text': article['first_512_chars'],
                'article_url': article['article_url'],
                'image_url': article['image_url'],
                'date': article['date']
            }
            refined_articles = filter_articles_with_vague_references([adjusted_article])
            if refined_articles:
                refined_article = refined_articles[0]
                ner_results = perform_ner_on_articles([refined_article])[0]
                new_article = Article(title=refined_article['headline'], content=refined_article['full_text'], ner_results=ner_results, date=refined_article['date'])
                session.add(new_article)
                new_articles_count += 1
    session.commit()
    print(f"Added {new_articles_count} new articles.")

def export_to_json():
    articles = session.query(Article).all()
    results = [
        {
            'title': article.title,
            'content': article.content,
            'ner_results': article.ner_results
        }
        for article in articles
    ]
    with open('export.json', 'w') as f:
        json.dump(results, f)
    print("Results exported to export.json")

if __name__ == "__main__":
    scrape_and_analyze()
    export_to_json()