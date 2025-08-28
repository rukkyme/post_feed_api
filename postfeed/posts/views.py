from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.db.models import Count
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import Post, Tag, Like
from .serializers import UserSerializer, PostSerializer, PostCreateSerializer, TagSerializer, LikeSerializer
from .recommendation import score_posts_for_user

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("id")
    serializer_class = UserSerializer
    http_method_names = ["get", "post", "retrieve", "head", "options"]
    permission_classes = [AllowAny] 

class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all().order_by("name")
    serializer_class = TagSerializer
    http_method_names = ["get", "post", "head", "options"]
    permission_classes = [IsAuthenticated]  # only authenticated users can create/view tags

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all().order_by("-created_at").annotate(like_count=Count("likes"))
    serializer_class = PostSerializer
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return PostCreateSerializer
        return PostSerializer

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        """
        Like a post (authenticated users only).
        """
        user = request.user
        post = self.get_object()
        Like.objects.get_or_create(user=user, post=post)
        return Response({"status": "liked"}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"], url_path="unlike", permission_classes=[IsAuthenticated])
    def unlike(self, request, pk=None):
        """
        Unlike a post (authenticated users only).
        """
        user = request.user
        post = self.get_object()
        Like.objects.filter(user=user, post=post).delete()
        return Response({"status": "unliked"}, status=status.HTTP_204_NO_CONTENT)


class FeedView(APIView):
    """
    Personalized feed for authenticated users.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

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