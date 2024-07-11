import requests
from bs4 import BeautifulSoup
import time
import re
import spacy

# Load the spacy NER model
nlp = spacy.load("en_core_web_sm")

def get_article_info(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    articles = []
    
    for article in soup.find_all('article', class_='storyblock'):
        link = article.find('a', class_='storyblock_image_link')
        title = article.find('h4')
        if link and 'href' in link.attrs and title:
            articles.append({
                'url': link['href'],
                'title': title.text.strip()
            })
    
    return articles

def get_article_text(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    paragraphs = soup.find_all('p')
    full_text = ' '.join([p.text for p in paragraphs])
    return full_text[:512] + '...' if len(full_text) > 512 else full_text

def get_image_url(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        image = soup.find('img', class_='responsive-img_img inline-image')
        if image and 'src' in image.attrs:
            return image['src']
        else:
            return None
    except Exception as e:
        print(f"Error fetching image from {url}: {str(e)}")
        return None

def analyze_headline(headline):
    vague_references = [
        r'star', r'celebrity', r'actor', r'actress', r'singer', r'rapper',
        r'athlete', r'player', r'politician', r'leader', r'official',
        r'expert', r'professional', r'icon', r'legend', r'veteran',
        r'personality', r'figure', r'tycoon', r'mogul', r'boss',
        r'chief', r'exec', r'CEO', r'founder', r'creator', r'producer',
        r'director', r'host', r'anchor', r'journalist', r'reporter',
        r'correspondent', r'model', r'designer', r'chef', r'artist',
        r'author', r'writer', r'comedian', r'influencer', r'blogger',
        r'pioneer', r'innovator', r'visionary', r'guru', r'genius',
        r'wizard', r'mastermind', r'virtuoso', r'savant', r'protege',
        r'phenom', r'maverick', r'prodigy', r'specialist', r'expert',
        r'guru', r'hero', r'villain', 
        r'royalty', r'heir', r'heiress', r'artist', r'sculptor', r'painter',
        r'composer', r'conductor', r'dancer', r'performer', r'entertainer',
        r'starlet', r'visionary', r'powerhouse', r'champion', r'genius',
        r'oracle', r'authority', r'warrior', r'champion', r'pundit', r'sage',
        r'commander', r'strategist', r'mind', r'virtuoso', r'architect',
        r'explorer', r'counselor', r'wizard', r'master', r'philosopher',
        r'sage', r'elder', r'giant', 
        r'millionaire', r'billionaire', r'titan', r'captain', r'legendary',
        r'famous', r'notorious', r'illustrious', r'magnate', r'industrialist', r'musician', r'A-lister', r'nominee',
    ]

    # Constructing the regular expression directly
    pattern = r'\b(?:' + '|'.join(vague_references) + r')\b'
    
    matches = re.findall(pattern, headline.lower())
    
    if matches:
        return matches[0]
    else:
        return None

def filter_articles_with_vague_references(articles):
    refined_articles = []

    for article in articles:
        headline = article['headline']
        full_text = article['full_text']  # Changed from 'first_512_chars' to 'full_text'
        
        match = analyze_headline(headline)
        if match:
            refined_articles.append({
                'headline': headline,
                'full_text': full_text,
                'match': match,
                'article_url': article['article_url'],
                'image_url': article['image_url'],
            })
    
    return refined_articles

def scrape_articles():
    base_url = 'https://www.news.com.au/entertainment'
    # Your existing scraping logic here
    # Return the scraped articles list
    article_info = get_article_info(base_url)
    articles = []

    for article in article_info[:60]:  # Limiting to first 40 articles
        try:
            # Check if the article URL contains 'video'
            if 'video' in article['url'].lower():
                continue
            
            full_text = get_article_text(article['url'])
            image_url = get_image_url(article['url'])  # Example function to fetch image URL
            articles.append({
                'title': article['title'],
                'first_512_chars': full_text,
                'article_url': article['url'],
                'image_url': image_url,
            })
            time.sleep(1)  # Be polite to the server
        except Exception as e:
            print(f"Error scraping {article['url']}: {str(e)}")

    return articles

def perform_ner(text):
    doc = nlp(text)
    entities = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    return entities

def perform_ner_on_articles(refined_articles):
    ner_results = []

    for article in refined_articles:
        headline = article['headline']
        full_text = article['full_text']
        match = article['match']
        
        # Perform NER on the full text of the article
        entities = perform_ner(full_text)
        
        # Extract the headline words (excluding common words)
        headline_words = set(word.lower() for word in headline.split() if len(word) > 3)
        
        # Find the first named entity that doesn't appear in the headline
        first_named_entity = None
        for entity in entities:
            entity_words = set(word.lower() for word in entity.split())
            if not entity_words.intersection(headline_words):
                first_named_entity = entity
                break

        ner_results.append({
            'headline': headline,
            'vague_reference': match,
            'first_named_entity': first_named_entity,
            'article_url': article['article_url'],
            'image_url': article['image_url'],
        })
    
    return ner_results