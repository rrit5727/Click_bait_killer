from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, Text, JSON, Date
import os
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()

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
    with open('export.json', 'r') as f:
        articles = json.load(f)

    for article_data in articles:
        existing_article = session.query(Article).filter_by(title=article_data['title']).first()
        if not existing_article:
            article = Article(
                title=article_data['title'],
                content=article_data['content'],
                ner_results=article_data['ner_results'],
                date=datetime.fromisoformat(article_data['date']).date() if article_data.get('date') else None
            )
            session.add(article)

    session.commit()
    print("Import complete")

if __name__ == "__main__":
    Base.metadata.create_all(engine)  # Create tables
    import_to_heroku()