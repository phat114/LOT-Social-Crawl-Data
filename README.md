# Create virtual environment
source .venv/bin/activate

# Install mysql connector 
pip install mysql-connector-python

# Generate database structure
Run sql file

# Update this information into routes.py
connection = mysql.connector.connect(
    host="",
    user="",
    password="",
    database=""
)

# Finally, launch the crawler with command:
uv run python -m tiktok_crawlee {link}


