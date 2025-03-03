from django.db import models

class CategorizedVideos(models.Model):
    name = models.CharField(max_length=255)  # Name for the response
    response = models.JSONField()  # To store the JSON response
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp of the save

    def __str__(self):
        return f"{self.name} - Saved at {self.created_at}"



class LastState(models.Model):
    channel_name = models.CharField(max_length=255)  # Stores the name of the channel
    excluded = models.JSONField(default=list)  # List of strings (e.g., excluded categories)

    def save(self, *args, **kwargs):
        """Ensure only one instance of LastState exists."""
        self.pk = 1  # Always use the same primary key
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Channel: {self.channel_name}, Excluded: {self.excluded}"

    @classmethod
    def get_instance(cls):
        """Retrieve the singleton instance or create it if it doesn't exist."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

