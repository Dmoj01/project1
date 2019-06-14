import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

import csv

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

file = open("books.csv") # Open file
reader = csv.reader(file) # Create csv reader for file
count = 0 # Keep track of count of rows added to db

for ISBN, title, author, year in reader: # for each row in the csv file
    db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                {"isbn": ISBN, "title": title, "author": author, "year": year})
    print(f"{ISBN} {title} {author} {year} was inserted into books")
    count += 1

print(f"{count} rows were added to the database")
db.commit()
