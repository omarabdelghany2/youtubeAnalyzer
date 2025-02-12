from django.urls import path
from .views import FetchChannelTagsView ,SaveCategorizedVideosView,FetchCategorizedVideosByNameView,DeleteCategorizedVideosByNameView,GetCategorizedVideosNamesView,FetchYouTubeVideoDataView,DeleteCategorizedVideosByNameView
from rest_framework_simplejwt.views import TokenObtainPairView
urlpatterns = [
    path('fetch-channel-tags/', FetchChannelTagsView.as_view(), name='fetch_channel_tags'),
    path('save-categorized-videos/', SaveCategorizedVideosView.as_view(), name='save_categorized_videos'),
    path('fetch-categorized-videos/', FetchCategorizedVideosByNameView.as_view(), name='fetch_categorized_videos_by_name'),  # New URL
    path('delete-categorized-videos/', DeleteCategorizedVideosByNameView.as_view(), name='delete_categorized_videos_by_name'),  # New URL
    path('categorized-video-names/', GetCategorizedVideosNamesView.as_view(), name='categorized_video_names'),
    path("fetch_youtube_data/", FetchYouTubeVideoDataView.as_view(), name="fetch_youtube_data"),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # Login to get access token only
    path("hide_tag/", DeleteCategorizedVideosByNameView.as_view(), name="fetch_youtube_data"),


]
