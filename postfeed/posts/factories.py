import factory
from django.contrib.auth import get_user_model
from faker import Faker
import random
from posts.models import User, Post, Like, Tag

fake = Faker()
User = get_user_model()

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.LazyAttribute(lambda _: fake.unique.user_name())
    email = factory.LazyAttribute(lambda _: fake.unique.email())
    is_active = True


class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tag

    name = factory.LazyAttribute(lambda _: fake.unique.word())


class PostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Post

    author = factory.SubFactory(UserFactory)
    text = factory.LazyAttribute(lambda _: fake.paragraph(nb_sentences=5))

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            # Add specific tags if provided
            for tag in extracted:
                self.tags.add(tag)
        else:
            # Add 1–3 random tags
            tag_batch = TagFactory.create_batch(fake.random_int(min=1, max=3))
            for tag in tag_batch:
                self.tags.add(tag)


class LikeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Like

    user = factory.SubFactory(UserFactory)
    post = factory.SubFactory(PostFactory)
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Ensure unique (user, post) pair when seeding"""
        user = kwargs.get("user") or UserFactory()
        post = kwargs.get("post") or PostFactory()

        # If like already exists, pick another random combo
        while model_class.objects.filter(user=user, post=post).exists():
            user = random.choice(User.objects.all())
            post = random.choice(Post.objects.all())

        kwargs["user"] = user
        kwargs["post"] = post
        return super()._create(model_class, *args, **kwargs)
