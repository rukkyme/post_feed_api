from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()  #stores the results of the active User model-get_user_model-that allows us be flexible when we need info about users, other than the one in the User database table that django.contrib.auth.models.User, can provide, hence we swap out of the User model

class Tag(models.Model):    #define a database table for tags so posts can be categorized easily.
    name = models.CharField(max_length=64, unique=True) #each tag of 64 xters and unique=true ensure there are no duplicate tag names

    def __str__(self):      #this fxn returns the tag name in strings and readable rep
        return self.name

class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")    #links each post to a user, if user is deleted, their post is deleted too. with this you can acces a user with user.posts.all()
    text = models.TextField()               #stores posts content
    tags = models.ManyToManyField(Tag, related_name="posts", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Post({self.id}) by {self.author_id}"

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "post")      #ensures the user, port is unique


