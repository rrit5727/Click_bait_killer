from flask import Flask, render_template, request
from Fetch_and_analyse import scrape_articles, filter_articles_with_vague_references, perform_ner_on_articles
import spacy


try:
    nlp = spacy.load("en_core_web_sm")
except:
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/results', methods=['POST'])
def show_results():
    base_url = 'https://www.news.com.au/entertainment'
    
    # Call scrape_articles() without any parameters as it doesn't require base_url
    scraped_articles = scrape_articles()
    
    # Filter articles with vague references
    refined_articles = filter_articles_with_vague_references(scraped_articles)
    
    # Perform NER on the refined articles
    ner_results = perform_ner_on_articles(refined_articles)
    
    return render_template('results.html', ner_results=ner_results)

if __name__ == "__main__":
    app.run(debug=True)