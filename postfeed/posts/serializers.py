from django.contrib.auth import get_user_model
from rest_framework import serializers      #converts complex data types into JSON for APIs
from .models import Post, Tag, Like

User = get_user_model()

#
class UserSerializer(serializers.ModelSerializer):
    class Meta:     #tells DRF which model the serializer is tied to and what to serialize.
        model = User
        fields = ["id", "username", "email", "password", "date_joined"]
        extra_kwargs = {"password": {"write_only": True}}
        read_only_fields = ["id", "date_joined"]
        
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email"),
            password=validated_data["password"]
        )
        return user

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]

class PostSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())    #serializes the author's id and the User.objects.all tells DRF to look into the User objects for it.
    tags = serializers.SlugRelatedField(
        many=True, slug_field="name", queryset=Tag.objects.all(), required=False
    )
    like_count = serializers.IntegerField(read_only=True)
    score = serializers.FloatField(read_only=True)  # only on feed
    

    class Meta: 
        model = Post
        fields = ["id", "author", "text", "tags", "created_at", "like_count", "score"]
        read_only_fields = ["id", "created_at", "like_count", "score"]

class PostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ["content"]



class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ["id", "user", "post", "created_at"]