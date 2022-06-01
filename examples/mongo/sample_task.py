"""
Example usage of mongoengine==0.24.0 with Mongoproxy Native
"""

import sys
from typing import List
from mongoengine import connect
from pymongo.mongo_client import MongoClient
from sample_schema import MONGO_URI, DB, User, TextPost


def init_connection() -> MongoClient:
    try:
        conn = connect(
            host=MONGO_URI,
            db=DB,
        )
    except Exception as err:
        print(f"Failed to connect to Mongodb. Error {err}")
        sys.exit(1)
    return conn


def create_user(email: str, first_name: str, last_name: str) -> User:
    return User(email=email, first_name=first_name, last_name=last_name).save()


def create_textpost(title: str, author: User, tags: List, upvote: int = 0) -> TextPost:
    post = TextPost(
        title=title, author=author, content="Something interesting", upvote=upvote
    )
    post.tags = tags
    return post.save()


def main() -> None:
    init_connection()

    alice = create_user(email="alice@example.com", first_name="Alice", last_name="a")
    bob = create_user(email="bob@example.com", first_name="Bob", last_name="b")
    create_textpost("Fun with MongoEngine", alice, ["mongodb", "mongoengine"])
    create_textpost(
        "Fun with MongoEngine v2", alice, ["newmongodb", "newmongoengine"], 10
    )
    create_textpost("Mongoengine Changelog", bob, ["newmongodb", "newmongoengine"], 5)
    # print existing users
    for user in User.objects:
        print(
            f"User: {user.first_name} {user.last_name} - email {user.email} - isDrunk {user.drunk}"
        )

    # print existing TextPost
    for post in TextPost.objects().clear_cls_query():
        print(f"Text Post: {post.title} - tags {post.tags}")

    # Some aggregate operation
    pipeline = [
        {"$match": {"tags": ["newmongodb", "newmongoengine"]}},
        {"$group": {"_id": "$title", "total": {"$sum": "$upvote"}}},
    ]
    docs = TextPost.objects().aggregate(pipeline)
    for doc in docs:
        print(doc)

    # Cleanup - delete all users
    for user in User.objects:
        user.delete()

    # Deleting the author will delete the post as well
    print(f"Currently we have {TextPost.objects.count()} existing text posts.")


if __name__ == "__main__":
    main()
