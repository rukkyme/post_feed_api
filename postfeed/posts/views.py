from django.shortcuts import render

from django.contrib.auth import get_user_model
from django.db.models import Count
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Post, Tag, Like
from .serializers import UserSerializer, PostSerializer, TagSerializer
from .recommendation import score_posts_for_user

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("id")
    serializer_class = UserSerializer
    http_method_names = ["get", "post", "retrieve", "head", "options"]

class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all().order_by("name")
    serializer_class = TagSerializer

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all().order_by("-created_at").annotate(like_count=Count("likes"))
    serializer_class = PostSerializer

    @action(detail=True, methods=["post"])
    def like(self, request, pk=None):
        """
        Body: {"user": <user_id>}
        """
        user_id = request.data.get("user")
        if not user_id:
            return Response({"detail": "user is required"}, status=400)
        try:
            user = User.objects.get(pk=user_id)
            post = self.get_object()
            Like.objects.get_or_create(user=user, post=post)
            return Response({"status": "liked"}, status=201)
        except User.DoesNotExist:
            return Response({"detail": "user not found"}, status=404)

    @action(detail=True, methods=["delete"], url_path="unlike")
    def like(self, request, pk=None):  # DRF allows same name with different methods
        user_id = request.data.get("user") or request.query_params.get("user")
        if not user_id:
            return Response({"detail": "user is required"}, status=400)
        try:
            user = User.objects.get(pk=user_id)
            post = self.get_object()
            Like.objects.filter(user=user, post=post).delete()
            return Response({"status": "unliked"}, status=204)
        except User.DoesNotExist:
            return Response({"detail": "user not found"}, status=404)

class FeedView(APIView):
    """
    GET /api/feed/?user_id=1&limit=20&offset=0
    Returns posts ordered by personalized score.
    """

    def get(self, request):
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response({"detail": "user_id required"}, status=400)
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"detail": "user not found"}, status=404)

        limit = int(request.query_params.get("limit", 20))
        offset = int(request.query_params.get("offset", 0))
        limit = max(1, min(limit, 100))

        # Candidate set: all posts not authored by the user
        base_qs = (
            Post.objects.exclude(author=user)
            .annotate(like_count=Count("likes"))
            .prefetch_related("tags", "author")
        )

        scored = score_posts_for_user(user, base_qs)
        page = scored[offset : offset + limit]

        # attach score to serializer output
        posts = [p for (p, _) in page]
        scores_map = {p.id: s for (p, s) in page}
        serializer = PostSerializer(posts, many=True)
        data = serializer.data
        for row in data:
            row["score"] = round(scores_map.get(row["id"], 0.0), 6)
        return Response({"count": len(scored), "results": data})
