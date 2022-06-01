"""
Sample mongo schemas
Once your service is ready for production, check in those schemas in Contextlogic/mongo-schemas
"""

from datetime import datetime
from mongoengine import (
    CASCADE,
    Document,
    fields,
)

# If mongodb operations are defined as a task under app/task, define the following config under app.config.Config
MONGO_URI = "mongogatenative-microsvcstage-online.service.consul:27017"
DB = "python-backend-worker"


class User(Document):
    drunk = fields.BooleanField(default=False)
    email = fields.StringField(required=True)
    first_name = fields.StringField(max_length=50)
    last_name = fields.StringField(max_length=50)


class Post(Document):
    title = fields.StringField(max_length=120, required=True)
    # delete the author will delete the post as well
    author = fields.ReferenceField(User, reverse_delete_rule=CASCADE)
    timestamp = fields.DateTimeField(default=datetime.utcnow)
    tags = fields.ListField(fields.StringField(max_length=30), max_length=10)
    upvote = fields.IntField(default=0)
    meta = {"allow_inheritance": True}


class TextPost(Post):
    content = fields.StringField(required=True)
