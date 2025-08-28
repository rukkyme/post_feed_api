import math
from collections import Counter, defaultdict
from django.utils import timezone
from django.db.models import Count
from .models import Tag, Post, Like
import os

#loads scoring weights for recommendation from the .env with defaults so they can be tuned or twerked without changing code
W_R = float(os.getenv("WEIGHT_RECENCY", 0.5))
W_P = float(os.getenv("WEIGHT_POPULARITY", 0.2))
W_A = float(os.getenv("WEIGHT_AFFINITY", 0.3))
LAMBDA = float(os.getenv("RECENCY_LAMBDA", 0.05))

def recency_decay(created_at, now, lam=LAMBDA): #this computes how fresh a post is. new post will give high score, older post- decayed score
    age_hours = (now - created_at).total_seconds() / 3600.0
    return math.exp(-lam * age_hours)

def popularity(like_count):     #calculates popularity score using natural log of likes
    return math.log1p(like_count)

#function calculates the weight of all liked tags by the user
def build_user_tag_weights(user):#useful for building a recommendation engine to suggest posts to a user based on their interests.
    # Count tags on posts the user liked
    qs = Tag.objects.filter(posts__likes__user=user).values_list("name", flat=True) #filters post, that are liked by the user
    counts = Counter(qs)
    total = sum(counts.values()) or 1 #in the case of zero likes, expression evaluates to 1
    
    #this returns the tag name : the count for how many times specific tag appeared in list of liked post/ sum of all the tags across all liked post
    return {name: c / total for name, c in counts.items()}  

def affinity(user_tag_weights, post_tags): #checks for posts user has more affinity for
    if not post_tags:
        return 0.0
    #note that len(post_tags) is to divide the sum of weights so that longer post with many tags do have a higher score because they have more tags.Its called normalization
    return sum(user_tag_weights.get(t.name, 0.0) for t in post_tags) / len(post_tags) 

def score_posts_for_user(user, queryset):
    """
    queryset: Post queryset already annotated with like_count and prefetched tags.
    Returns list of (post, score) sorted desc by score (then created_at, id).
    """
    now = timezone.now()
    utw = build_user_tag_weights(user)

    scored = []
    for p in queryset:
        s = (
            W_R * recency_decay(p.created_at, now, LAMBDA)
            + W_P * popularity(getattr(p, "like_count", 0))
            + W_A * affinity(utw, list(p.tags.all()))
        )
        scored.append((p, float(s)))

    scored.sort(key=lambda t: (t[1], t[0].created_at, t[0].id), reverse=True)
    return scored
