from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta

from posts.models import Post, Tag, Like
from posts.scoring import score_posts_for_user

User = get_user_model()

class ScoringTests(TestCase):
    def setUp(self):
        # Create users
        self.user = User.objects.create(username="rukky")
        self.other_user = User.objects.create(username="john")

        # Create tags
        self.django_tag = Tag.objects.create(name="django")
        self.python_tag = Tag.objects.create(name="python")

        # Create posts
        self.post1 = Post.objects.create(
            author=self.other_user,
            text="Fresh Django post",
            created_at=timezone.now() - timedelta(hours=1)  # fresh
        )
        self.post1.tags.add(self.django_tag)

        self.post2 = Post.objects.create(
            author=self.other_user,
            text="Old Python post",
            created_at=timezone.now() - timedelta(days=3)  # old
        )
        self.post2.tags.add(self.python_tag)

        self.post3 = Post.objects.create(
            author=self.other_user,
            text="Popular post with likes",
            created_at=timezone.now() - timedelta(hours=2)
        )
        self.post3.tags.add(self.python_tag)

        # Add likes to simulate popularity
        Like.objects.create(user=self.other_user, post=self.post3)
        Like.objects.create(user=self.user, post=self.post3)

        # User likes a django-tagged post → affinity boost
        Like.objects.create(user=self.user, post=self.post1)

    def test_scoring_prefers_fresh_posts(self):
        """Fresh posts should score higher than very old ones, all else equal."""
        scored = score_posts_for_user(self.user, Post.objects.all())
        posts_order = [p.id for p, score in scored]

        self.assertIn(self.post1.id, posts_order)
        self.assertLess(posts_order.index(self.post1.id), posts_order.index(self.post2.id))

    def test_popularity_increases_score(self):
        """Posts with more likes should score higher."""
        scored = score_posts_for_user(self.user, Post.objects.all())
        scores = {p.id: s for p, s in scored}

        self.assertGreater(scores[self.post3.id], scores[self.post2.id])

    def test_affinity_boosts_score(self):
        """Posts with tags the user likes should rank higher."""
        scored = score_posts_for_user(self.user, Post.objects.all())
        scores = {p.id: s for p, s in scored}

        # user liked django-tag post → should have affinity boost
        self.assertGreater(scores[self.post1.id], scores[self.post2.id])
