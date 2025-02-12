from django.db import models

class CategorizedVideos(models.Model):
    name = models.CharField(max_length=255)  # Name for the response
    response = models.JSONField()  # To store the JSON response
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp of the save

    def __str__(self):
        return f"{self.name} - Saved at {self.created_at}"
