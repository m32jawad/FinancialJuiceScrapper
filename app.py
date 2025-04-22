from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
import datetime
import json
from pyngrok import ngrok
import os
# from googletrans import Translator
from aiogoogletrans import Translator
from dotenv import load_dotenv
import os

NGROK_ACCESS_TOKEN = os.getenv("NGROK_TOKEN")
RESERVED_SUBDOMAIN = os.getenv("NGROK_DOMAIN")  # Replace with your reserved subdomain

def translate_to_spanish(text):
    translator = Translator()
    translated_text = translator.translate(text, dest='es').text
    return translated_text

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
# Configure SQLAlchemy to use SQLite database named 'news.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///news.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app)

# Define a News model to store scraped news
class News(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    news_id = db.Column(db.Integer, unique=True, nullable=False)  # Unique NewsID from scrapped data
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    date_published = db.Column(db.DateTime, nullable=False)
    eurl = db.Column(db.String)           # URL of the news article
    fcname = db.Column(db.String)          # Source name (e.g., CNBC, Forbes)
    labels = db.Column(db.String)          # JSON serialized list of labels or tags
    tags = db.Column(db.String)            # Tags associated with the news (JSON serialized)
    stid = db.Column(db.String)            # Some identifier (STID)
    type_id = db.Column(db.String)         # Type identifier (TypeID)
    posted_short = db.Column(db.String)    # Short posted description
    posted_long = db.Column(db.String)     # Long posted description
    test_date_published = db.Column(db.String)  # Test date published
    breaking = db.Column(db.Boolean, default=False)  # Is it breaking news?
    upd = db.Column(db.Boolean, default=False)       # Is it updated news?
    img = db.Column(db.String)             # Image URL
    level = db.Column(db.String)           # Level of importance
    has_e = db.Column(db.Boolean, default=False)  # Has extra content
    rurl = db.Column(db.String)            # Redirect URL
    eurl_img = db.Column(db.String)        # Image URL for the news
    strid = db.Column(db.String)           # String identifier (STRID)
    rid = db.Column(db.String)             # Record identifier (RID)
    fcid = db.Column(db.String)            # Financial content ID (FCID)
    fcname_url = db.Column(db.String)      # URL for the source name
    stream_ids = db.Column(db.String)      # JSON serialized list of stream IDs
    ticker_ids = db.Column(db.String)      # JSON serialized list of ticker IDs
    iid = db.Column(db.String)             # Some identifier (IID)

def create_tables():
    # This method ensures that the tables exist.
    
    with app.app_context():
        try:
            from sqlalchemy.sql import text
            result = db.session.execute(text("PRAGMA table_info(news)"))
            columns = [row[1] for row in result]
            required_columns = [
                "id", "news_id", "title", "description", "date_published", "eurl", "fcname", 
                "labels", "tags", "stid", "type_id", "posted_short", "posted_long", 
                "test_date_published", "breaking", "upd", "img", "level", "has_e", "rurl", 
                "eurl_img", "strid", "rid", "fcid", "fcname_url", "stream_ids", "ticker_ids", "iid"
            ]
            if not all(column in columns for column in required_columns):
                raise Exception("The 'news' table does not have the required schema.")
        except Exception:
            db.drop_all()
            db.create_all()


@app.after_request
def add_csp_header(response):
    # Adjust the allowed sources as needed.
    # The following example allows self and fonts from fonts.gstatic.com and data URIs.
    csp = (
        "default-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "script-src 'self' https://cdnjs.cloudflare.com 'unsafe-inline' 'unsafe-eval'; "
        "font-src 'self' https://fonts.gstatic.com data:;"
        "style-src 'self' https://fonts.googleapis.com 'unsafe-inline'; "
        "img-src 'self' https://www.financialjuice.com;"
        "media-src 'self' https://assets.mixkit.co;")
    
    response.headers['Content-Security-Policy'] = csp
    return response

@app.route('/')
def index():
    # Fetch all news from the database and convert stream_ids from stored JSON to a list.
    all_news = News.query.order_by(News.date_published.desc()).all()[:100]
    news_list = []
    for news in all_news:
        news_item = {
            "news_id": news.news_id,
            "title": news.title,
            "description": news.description,
            "date_published": news.date_published.strftime("%Y-%m-%d %H:%M:%S"),
            "eurl": news.eurl,
            "fcname": news.fcname,
            "img": news.img,
            "labels": json.loads(news.labels) if news.labels else [],
            "tags": json.loads(news.tags) if news.tags else [],
            # Convert stream_ids from the stored JSON string to a list.
            "stream_ids": json.loads(news.stream_ids) if news.stream_ids else []
        }
        news_list.append(news_item)
    return render_template('index.html', news_list=news_list)

@app.route('/news', methods=['POST'])
async def add_news():
    """
    This endpoint accepts a POST request with JSON payload representing a news item.
    It then stores the news into the database and emits a SocketIO event for real-time updates.
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON received'}), 400

    # Validate required fields
    news_id = data.get("NewsID")
    title = data.get("Title")
    date_published_str = data.get("DatePublished")
    if not news_id or not title or not date_published_str:
        return jsonify({'error': 'NewsID, Title, and DatePublished are required'}), 400

    try:
        date_published = datetime.datetime.fromisoformat(date_published_str)
    except Exception as e:
        return jsonify({'error': f"Error parsing date: {str(e)}"}), 400

    # Extract optional fields
    description = data.get("Description", "")
    eurl = data.get("EURL", "")
    fcname = data.get("FCName", "")
    labels = data.get("Labels", [])
    tags = data.get("Tags", [])
    stid = data.get("STID", "")
    type_id = data.get("TypeID", "")
    posted_short = data.get("PostedShort", "")
    posted_long = data.get("PostedLong", "")
    test_date_published = data.get("TestDatePublished", "")
    breaking = bool(data.get("Breaking", False))
    upd = bool(data.get("Upd", False))
    img = data.get("Img", "")
    level = data.get("Level", "")
    rurl = data.get("RURL", "")
    eurl_img = data.get("EURLImg", "")
    strid = data.get("STRID", "")
    rid = data.get("RID", "")
    fcid = data.get("FCID", "")
    fcname_url = data.get("FCNameURL", "")
    stream_ids = data.get("StreamIDs", [])   # This should be an array of numbers or strings
    ticker_ids = data.get("TickerIDs", [])
    iid = data.get("IID", "")
    
    labels_str = json.dumps(labels)
    tags_str = json.dumps(tags)
    stream_ids_str = json.dumps(stream_ids)
    ticker_ids_str = json.dumps(ticker_ids)

    # Check if the news item already exists
    existing = News.query.filter_by(news_id=news_id).first()
    if existing:
        return jsonify({'message': 'News already exists'}), 200

    translator = Translator()
    # Translate title and description to Spanish.
    translated_title = (await translator.translate(title, dest='es')).text
    translated_description = (await translator.translate(description, dest='es')).text if description else ""
    
    news_item = News(
        news_id=news_id,
        title=translated_title,
        description=translated_description,
        date_published=date_published,
        eurl=eurl,
        fcname=fcname,
        labels=labels_str,
        tags=tags_str,
        stid=stid,
        type_id=type_id,
        posted_short=posted_short,
        posted_long=posted_long,
        test_date_published=test_date_published,
        breaking=breaking,
        upd=upd,
        img=img,
        level=level,
        has_e=bool(data.get("HasE", False)),
        rurl=rurl,
        eurl_img=eurl_img,
        strid=strid,
        rid=rid,
        fcid=fcid,
        fcname_url=fcname_url,
        stream_ids=stream_ids_str,
        ticker_ids=ticker_ids_str,
        iid=iid
    )

    try:
        db.session.add(news_item)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f"Failed to add news to the database: {str(e)}"}), 500

    # img = f"https://www.financialjuice.com{img}" if img else img 
    # Prepare data to be sent to clients – include stream_ids as an array
    new_news = {
        "news_id": news_id,
        "title": translated_title,
        "description": translated_description,
        "date_published": date_published.strftime("%Y-%m-%d %H:%M:%S"),
        "eurl": eurl,
        "fcname": fcname,
        "labels": labels,
        "tags": tags,
        "breaking": breaking,
        "level": level,
        "stream_ids": stream_ids,  # Passed as an array
        "img": img,  # Passed as an array
    }

    # Emit a real-time update event to all connected clients
    socketio.emit('news_update', new_news)
    return jsonify({'message': 'News added successfully'}), 201

PORT = 5000

try:
    # Set your Ngrok access token
    ngrok.set_auth_token(NGROK_ACCESS_TOKEN)

    # Disconnect any existing tunnels
    for tunnel in ngrok.get_tunnels():
        ngrok.disconnect(tunnel.public_url)

    # Open an Ngrok tunnel with the reserved subdomain
    public_url = ngrok.connect(PORT, domain=RESERVED_SUBDOMAIN)
    print("Ngrok tunnel available at:", public_url)
except Exception as e:
    print(f"Failed to setup Ngrok tunnel: {str(e)}")
    print("Continuing without Ngrok tunnel...")

if __name__ == '__main__':
    create_tables()  # Ensure tables are created before starting the app
    socketio.run(app, debug=True)
