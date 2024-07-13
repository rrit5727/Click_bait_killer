from celery import Celery
import os
from dotenv import load_dotenv
from flask import current_app
from flask.app import Flask

load_dotenv()

celery_app = Celery('tasks', broker=os.getenv('REDIS_URL'))

def create_app():
    from app import app, db  # Import here to avoid circular imports
    return app

@celery_app.task
def scrape_and_process_articles_task():
    app = create_app()
    with app.app_context():
        from app import db, Article  # Import here to avoid circular imports
        try:
            from Fetch_and_analyse import scrape_articles, filter_articles_with_vague_references, perform_ner_on_articles
            scraped_articles = scrape_articles()
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
            return f"Completed scrape and process job. Added {new_articles_count} new articles."
        except Exception as e:
            return f"Error in scrape_and_process_articles: {str(e)}"