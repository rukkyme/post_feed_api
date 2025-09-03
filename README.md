#   Post_Feed_API

##  Project Overview

A backend that serves a
post feed with personalized recommendations. It stores Users, Posts  and keeps records of users. 

It returns a personalized feed for a user.

##  Technologies Used:
**Language:** Python 3.12
**Framework:** Django
**Docker**

**Auth:**
djangorestframework-simplejwt==5.3.1

##  Instructions **
### Prerequisites

Python 3.12
pip
docker
venv
PostgreSQL

##  Local Setup Locally
1. Clone repo

2. Create virtual environment and activate it. Then install Docker in root project

3. **To run migrations on docker** 

docker compose build web up 

docker compose up -d 

python manage.py makemigration

docker compose exec web 

python manage.py migrate

4.  **To populate with seed data(while on docker)** 

docker compose exec web python manage.py seed --flush --users=10 --tags=15 --posts=30 --likes=100

5.  **without flush** 

docker compose exec web python manage.py seed --users=10 --tags=15 --posts=30 --likes=100


##  Test with Curl
base_url = http://localhost:8000/

**  To register new user: **
 curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{"username": "joy", "password": "mypassword", "email": "joy@example.com"}'

**  To get a JWT token:**

 curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "joy", "password": "mypassword"}'


** Copy access token and paste in the Bearer token as shown here to access all other endpoints
Call protected endpoints with Bearer token:

 curl http://localhost:8000/api/tags/ \
  -H "Authorization: Bearer <your_access_token_here>"

 curl http://localhost:8000/api/posts/ \
  -H "Authorization: Bearer <your_access_token_here>"

 curl http://localhost:8000/api/feed/ \
  -H "Authorization: Bearer <your_access_token_here>"     

** To list users**
 curl http://localhost:8000/api/users/

 ** To Retrieve a user**
  curl http://localhost:8000/api/users/{id}

   
Endpoint            |   Method    |   Description
---------------------------------------------------
api/users/          |  POST       |   Register user

api/token           |  POST       |   Accss token

api/users/          |   GET       |   List users

api/users/{id}      |   GET       |   Retrieve one user

api/tags            |   POST      |   create a tag

api/tags            |   GET       |   List tags

api/tags{id}        |   GET       |   Retrieve a tag

api/posts           |   POST      | create a post

api/posts           |   GET       |  List posts (ordered by created_at desc, includes like_count)

api/posts/{id}      |   GET       |  Retrieve a post 

api/posts/{id}/likes|   POST      |  Likee a new like

api/posts/{id}/unlike| DELETE     |   Unlike a post

api/feed/           |  GET        |  Personalized feed for the logged-in user (with scores)

##  Automated Testing
docker compose exec web python manage.py test posts


##  Recommendation
Recommendation Method

Our feed ranking uses a hybrid scoring model that combines recency (freshness), popularity, and user affinity.
Each factor contributes to the final score via a weighted sum.
The weights are configurable via .env, so they can be tuned without changing code


**For Freshness (Recency Bias)**

We want newer posts to appear higher in the feed.
This is handled by an exponential decay function that makes it possible to ensure
that a post created an hour ago will score much higher than one from 2 weeks ago.

The lam (RECENCY_LAMBDA) controls how quickly old posts fade away ensuring the feed feels fresh and alive.

**For Popularity **
We don’t want great posts with many likes to get buried.
So we add a popularity boost:

def popularity(like_count):
    return math.log1p(like_count)

we use the natural logarithm, so 100 likes isn’t 100× better than 1 like.

This helps prevents viral messages from dominating while still rewarding engagement.

and makes sure the feed highlights posts people enjoy, without letting one viral post take over forever.

**For Affinity-Personalization**

To personalize the feed, we look at what tags a user has liked before.
We build a user interest profile that checks how much a each candidate's post matches the interests.
This takes care of it:

def affinity(user_tag_weights, post_tags):
    if not post_tags:
        return 0.0
    return sum(user_tag_weights.get(t.name, 0.0) for t in post_tags) / len(post_tags)


So if a user has liked many “Django” posts, new posts tagged django will rank higher for them.

**Final Score (Hybrid Model)**

Each post’s final score is the weighted sum:

s = (
    W_R * recency_decay(p.created_at, now, LAMBDA)
    + W_P * popularity(getattr(p, "like_count", 0))
    + W_A * affinity(utw, list(p.tags.all()))
)


Posts are then sorted by score (descending), with ties broken by created_at and id.

##  Assumptions

Tags are meaningful and represent content well.

A user’s interests can be modeled by tags on posts they liked.

Users prefer a mix of fresh, popular, and personalized content.

Simplicity and clarity are more valuable than complexity (for this scale).

##  Trade-Offs

By choosing recency bias, fresh posts are boosted and the feed feels lively. But older good posts get buried.


By choosing tag affinity (personalization by tags), the method is easy, interpretable, and works with small data.
But if tags are missing or wrong, the personalization fails.


By choosing a simple weighted formula instead of ML , the method is fast, transparent, and easier to understand, but it's less powerful than modern ML recommenders.






