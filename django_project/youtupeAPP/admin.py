from django.contrib import admin
from .models import CategorizedVideos

@admin.register(CategorizedVideos)
class CategorizedVideosAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')  # Fields to display in the admin list view
    search_fields = ('name',)  # Allow searching by name
    list_filter = ('created_at',)  # Add filter options for the created_at field
