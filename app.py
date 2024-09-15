import os
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import threading
import time
import random
from sentence_transformers import SentenceTransformer
from pymongo import MongoClient
import requests
from bs4 import BeautifulSoup
import redis
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Setup logging
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

# Setup rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["5 per minute"],
    storage_uri=os.getenv('REDIS_URL', "redis://localhost:6379")
)

# Connect to MongoDB
mongo_uri = os.getenv('MONGO_URI', 'mongodb+srv://anshvaidya:Fsua58PjECXH@documentretrieval.xyqql.mongodb.net/')
client = MongoClient(mongo_uri)
db = client['document_db']
documents = db['documents']
users = db['users']

# Connect to Redis
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = int(os.getenv('REDIS_PORT', 6379))
redis_client = redis.Redis(host=redis_host, port=redis_port, db=0)

# Initialize the sentence transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

def scrape_news():
    while True:
        try:
            response = requests.get('https://news.ycombinator.com')
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.select('.titleline > a')[:5]  # Get top 5 stories
            for item in articles:
                title = item.text
                url = item['href']
                content = requests.get(url).text
                
                # Encode the document
                encoding = model.encode(content)
                
                # Store in MongoDB
                documents.insert_one({
                    'title': title,
                    'content': content,
                    'encoding': encoding.tolist()
                })
            
            app.logger.info(f"Successfully scraped and stored {len(articles)} articles")
        except Exception as e:
            app.logger.error(f"Error in scraping: {str(e)}")
        finally:
            time.sleep(3600)  # Sleep for an hour before next scrape

# Start the scraping thread
scrape_thread = threading.Thread(target=scrape_news)
scrape_thread.start()

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "message": f"The system is operational. Random number: {random.randint(1, 100)}"})

@app.route('/search', methods=['POST'])
def search():
    start_time = time.time()
    
    data = request.json
    text = data.get('text', '')
    top_k = data.get('top_k', 5)
    threshold = data.get('threshold', 0.5)
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    
    # Update user request count and check rate limit
    user = users.find_one_and_update(
        {'_id': user_id},
        {'$inc': {'request_count': 1}},
        upsert=True,
        return_document=True
    )
    
    if user['request_count'] > 5:
        return jsonify({"error": "Rate limit exceeded"}), 429
    
    # Check cache
    cache_key = f"{text}:{top_k}:{threshold}"
    cached_result = redis_client.get(cache_key)
    if cached_result:
        end_time = time.time()
        inference_time = end_time - start_time
        app.logger.info(f"User {user_id} made a search request. Query: '{text}', Top K: {top_k}, Threshold: {threshold}, Inference time: {inference_time:.2f} seconds (Cached)")
        return jsonify({"results": cached_result.decode('utf-8'), "source": "cache", "inference_time": inference_time})
    
    # Encode the query
    query_encoding = model.encode(text)
    
    # Search in MongoDB
    results = []
    for doc in documents.find():
        similarity = float(model.cos_sim([query_encoding], [doc['encoding']])[0][0])
        if similarity >= threshold:
            results.append({
                'title': doc['title'],
                'similarity': similarity
            })
    
    # Sort and limit results
    results = sorted(results, key=lambda x: x['similarity'], reverse=True)[:top_k]
    
    # Cache the results
    redis_client.setex(cache_key, 3600, str(results))  # Cache for 1 hour
    
    end_time = time.time()
    inference_time = end_time - start_time
    
    app.logger.info(f"User {user_id} made a search request. Query: '{text}', Top K: {top_k}, Threshold: {threshold}, Inference time: {inference_time:.2f} seconds")
    
    return jsonify({"results": results, "inference_time": inference_time})

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled exception: {str(e)}")
    return jsonify({"error": "An unexpected error occurred"}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))