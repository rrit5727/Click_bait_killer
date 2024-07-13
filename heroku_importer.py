import json
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Use your Heroku DATABASE_URL here
DATABASE_URL = os.environ['HEROKU_DATABASE_URL']
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
engine = create_engine(DATABASE_URL)
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
                ner_results=article_data['ner_results']
            )
            session.add(article)

    session.commit()
    print("Import complete")

if __name__ == "__main__":
    import_to_heroku()