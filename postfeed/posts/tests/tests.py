from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status

from posts.models import Post, Tag, Like
from posts.recommendation import score_posts_for_user

User = get_user_model()


class ScoringTests(TestCase):
    def setUp(self):
        # Create users
        self.user = User.objects.create_user(username="rukky", password="pass123")  #the target user we ask for recommendations for
        self.other_user = User.objects.create_user(username="john", password="pass123") #other users to populate posts

        # Create tags to test affinity
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
        """Fresh posts should score higher than very old ones."""
        scored = score_posts_for_user(self.user, Post.objects.all())
        posts_order = [p.id for p, score in scored]

        self.assertLessEqual(posts_order.index(self.post1.id), posts_order.index(self.post2.id))

    def test_popularity_increases_score(self):
        """Posts with more likes should score higher."""
        scored = score_posts_for_user(self.user, Post.objects.all())
        scores = {p.id: s for p, s in scored}
        self.assertGreater(scores[self.post3.id], scores[self.post2.id])

    def test_affinity_boosts_score(self):
        """Posts with tags the user likes should rank higher."""
        scored = score_posts_for_user(self.user, Post.objects.all())
        scores = {p.id: s for p, s in scored}
        self.assertGreaterEqual(round(scores[self.post1.id], 2), round(scores[self.post2.id], 2))


class FeedEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="joy",
            email="joy@example.com",
            password="mypassword"
        )
        
        self.other_user = User.objects.create_user(
            username="john",
            email="john@example.com",
            password="pass123"
        )
        
        self.tag = Tag.objects.create(name="django")
        self.post1 = Post.objects.create(
            author=self.other_user,
            text="Hello Django",
        )
        self.post1.tags.add(self.tag)
        
        #self.other_user = User.objects.create_user(username="john", password="pass123")

        # Authenticate test client
        #self.client.login(username="rukky", password="pass123")
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Make posts
        self.post = Post.objects.create(
            author=self.other_user,
            text="Feed test post",
            created_at=timezone.now() - timedelta(hours=1)
        )

    def test_feed_requires_authentication(self):
        """Feed should reject unauthenticated requests."""
        client2 = APIClient()
        self.client.force_authenticate(user=self.user)

        response = client2.get("/api/feed/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_feed_returns_posts_with_score(self):
        """Feed should return posts scored by the recommendation system."""
        response = self.client.get("/api/feed/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertGreaterEqual(len(response.data["results"]), 1)
        self.assertIn("score", response.data["results"][0])
