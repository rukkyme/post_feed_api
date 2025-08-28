from django.core.management.base import BaseCommand
from posts.factories import UserFactory, TagFactory, PostFactory, LikeFactory
from django.core.management import call_command
import random
import factory
from faker import Faker

fake = Faker()
fake.unique.clear()


class Command(BaseCommand):
    help = "Seed database with demo Users, Tags, Posts, and Likes"

    def add_arguments(self, parser):
        parser.add_argument("--users", type=int, default=20, help="Number of users")
        parser.add_argument("--tags", type=int, default=20, help="Number of tags")
        parser.add_argument("--posts", type=int, default=20, help="Number of posts")
        parser.add_argument("--likes", type=int, default=50, help="Number of likes")
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Flush the database before seeding (wipes ALL data!)",
        )

        

    def handle(self, *args, **options):
        if options["flush"]:
            self.stdout.write(self.style.WARNING("Flushing database..."))
            call_command("flush", verbosity=0, interactive=False)
            call_command("migrate", verbosity=0)
            
            # Reset Faker's unique cache
            fake.unique.clear()
        
        
        users = UserFactory.create_batch(options["users"])
        tags = TagFactory.create_batch(options["tags"])
        posts = PostFactory.create_batch(options["posts"])
        likes = LikeFactory.create_batch(options["likes"])

        # Assign random tags to posts (extra non-trivial bit)
        for post in posts:
            random_tags = random.sample(tags, random.randint(1, 3))
            post.tags.add(*random_tags)

        # Create likes with random users + posts
        for _ in range(options["likes"]):
            LikeFactory(user=random.choice(users), post=random.choice(posts))

        self.stdout.write(self.style.SUCCESS(
            f"Seeded: {options['users']} users, {options['tags']} tags, "
            f"{options['posts']} posts, {options['likes']} likes"
        ))
