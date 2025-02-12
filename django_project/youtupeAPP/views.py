import os
import requests
import json
import uuid  # For generating unique IDs
from collections import defaultdict
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from .models import CategorizedVideos
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from collections import defaultdict
from rest_framework.views import APIView
import uuid  # For generating unique IDs


# def build_hierarchy(tag, tag_hierarchy, video_to_tags, tag_ids, processed_tags, current_depth, max_depth, ancestors):
#     """Recursively builds the tag hierarchy up to max_depth=5, preventing cycles where a child has the same name as an ancestor."""
#     if current_depth >= max_depth or tag in ancestors:
#         return None  # Stop recursion if max depth is reached or cycle is detected

#     overlapping_tags = {}
#     for video_id in tag_hierarchy[tag]:
#         for overlapping_tag in video_to_tags[video_id]:
#             if overlapping_tag != tag and overlapping_tag not in ancestors:  # Prevent cycles
#                 overlapping_tags.setdefault(overlapping_tag, []).append(video_id)

#     children = []
#     for overlapping_tag, overlap_videos in overlapping_tags.items():
#         if overlapping_tag not in processed_tags:
#             child_node = build_hierarchy(
#                 overlapping_tag, tag_hierarchy, video_to_tags, tag_ids, processed_tags, current_depth + 1, max_depth, ancestors + [tag]
#             )
#             if child_node:  # Only add if not None
#                 children.append(child_node)
#             processed_tags.add(overlapping_tag)

#     return {
#         "name": tag,
#         "id": tag_ids[tag],  
#         "children": children if children else None,  
#         "videos_id": tag_hierarchy[tag],
#         "value": len(tag_hierarchy[tag])
#     }


# def categorize_videos_by_tags(video_tags_map, max_depth=5):
#     """Categorizes videos by tags into a hierarchical structure up to max_depth=5 while avoiding cyclic relationships."""
#     tag_hierarchy = defaultdict(list)
#     video_to_tags = defaultdict(list)

#     # Populate mappings
#     for video_id, tags in video_tags_map.items():
#         for tag in tags:
#             tag_hierarchy[tag].append(video_id)
#             video_to_tags[video_id].append(tag)

#     structured_hierarchy = {"children": []}
#     processed_tags = set()

#     # Assign unique IDs to tags
#     tag_ids = {tag: str(uuid.uuid4()) for tag in tag_hierarchy.keys()}

#     for tag in tag_hierarchy.keys():
#         if tag not in processed_tags:
#             node = build_hierarchy(tag, tag_hierarchy, video_to_tags, tag_ids, processed_tags, 1, max_depth, [])
#             if node:
#                 structured_hierarchy["children"].append(node)
#             processed_tags.add(tag)

#     return structured_hierarchy
def build_hierarchy(tag, tag_hierarchy, video_to_tags, tag_ids, processed_tags, current_depth, max_depth):
    """Recursively builds the tag hierarchy up to max_depth=3, ensuring no child has the same name as its parent."""
    if current_depth >= max_depth:
        return None  # Stop recursion if max depth is reached

    overlapping_tags = {}
    for video_id in tag_hierarchy[tag]:
        for overlapping_tag in video_to_tags[video_id]:
            if overlapping_tag != tag:  # Prevent self-referencing tags
                overlapping_tags.setdefault(overlapping_tag, []).append(video_id)

    children = []
    for overlapping_tag, overlap_videos in overlapping_tags.items():
        if overlapping_tag not in processed_tags:
            child_node = build_hierarchy(
                overlapping_tag, tag_hierarchy, video_to_tags, tag_ids, processed_tags, current_depth + 1, max_depth
            )
            if child_node:  # Only add if not None
                children.append(child_node)
            processed_tags.add(overlapping_tag)

    return {
        "name": tag,
        "id": tag_ids[tag],  
        "children": children if children else None,  
        "videos_id": tag_hierarchy[tag],
        "value": len(tag_hierarchy[tag])
    }


def categorize_videos_by_tags(video_tags_map, max_depth=3):
    """Categorizes videos by tags into a hierarchical structure up to max_depth=3."""
    tag_hierarchy = defaultdict(list)
    video_to_tags = defaultdict(list)

    # Populate mappings
    for video_id, tags in video_tags_map.items():
        for tag in tags:
            tag_hierarchy[tag].append(video_id)
            video_to_tags[video_id].append(tag)

    structured_hierarchy = {"children": []}
    processed_tags = set()

    # Assign unique IDs to tags
    tag_ids = {tag: str(uuid.uuid4()) for tag in tag_hierarchy.keys()}

    for tag in tag_hierarchy.keys():
        if tag not in processed_tags:
            node = build_hierarchy(tag, tag_hierarchy, video_to_tags, tag_ids, processed_tags, 1, max_depth)
            if node:
                structured_hierarchy["children"].append(node)
            processed_tags.add(tag)

    return structured_hierarchy


def resolve_handle_to_channel_url(handle_url, api_key):
    try:
        if '@' in handle_url:
            handle = handle_url.split('@')[1].strip('/')
            url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={handle}&type=channel&key={api_key}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            if 'items' in data and data['items']:
                channel_id = data['items'][0]['id']['channelId']
                return f"https://www.youtube.com/channel/{channel_id}"
            return None
        return None
    except requests.exceptions.RequestException:
        return None

def get_uploads_playlist_id(api_key, channel_id):
    try:
        url = f"https://www.googleapis.com/youtube/v3/channels?part=contentDetails&id={channel_id}&key={api_key}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if "items" in data and data["items"]:
            return data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        return None
    except requests.exceptions.RequestException:
        return None

def get_video_ids(api_key, playlist_id):
    video_ids = []
    url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=contentDetails&playlistId={playlist_id}&maxResults=50&key={api_key}"
    while url:
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            video_ids.extend(item["contentDetails"]["videoId"] for item in data.get("items", []))
            next_page_token = data.get("nextPageToken")
            if next_page_token:
                url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=contentDetails&playlistId={playlist_id}&maxResults=50&pageToken={next_page_token}&key={api_key}"
            else:
                url = None
        except requests.exceptions.RequestException:
            break
    return video_ids

def fetch_video_tags(api_key, video_id):
    try:
        url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={api_key}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if "items" in data and data["items"]:
            return data["items"][0]["snippet"].get("tags", [])
        return []
    except requests.exceptions.RequestException:
        return []




def get_video_details(api_key, video_ids):
    filtered_ids = []
    shorts_excluded = []  # Store excluded Shorts

    for video_id in video_ids:
        url = f"https://www.googleapis.com/youtube/v3/videos?part=contentDetails&id={video_id}&key={api_key}"
        response = requests.get(url).json()
        # print(f"Video details for {video_id}: {response}")  # Log full response
        
        if "items" in response and response["items"]:
            duration = response["items"][0]["contentDetails"]["duration"]
            # print(f"Video ID {video_id} Duration: {duration}")  # Log duration
            
            if "PT" in duration and "M" not in duration:  # Likely a Short
                shorts_excluded.append(video_id)
            else:
                filtered_ids.append(video_id)

    # print(f"Excluded Shorts: {shorts_excluded}")  # Print excluded Shorts
    return filtered_ids



def parse_duration(duration):
    """Convert YouTube ISO 8601 duration (PT#H#M#S) to total seconds."""
    import re
    hours = minutes = seconds = 0

    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
    if match:
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)

    return hours * 3600 + minutes * 60 + seconds


@method_decorator(csrf_exempt, name='dispatch')
class FetchChannelTagsView(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            body = json.loads(request.body)
            handle = body.get("channel_url")  
            api_key = "AIzaSyDP03hg1_-sklhoaz0KGA9RHLDwRPaMlHg"  # Replace with your API key
            
            if not api_key or not handle:
                return JsonResponse({"error": "API key or channel handle is missing."}, status=400)
            
            handle_url = f"https://www.youtube.com/@{handle}"
            channel_name = handle
            full_channel_url = resolve_handle_to_channel_url(handle_url, api_key)
            if not full_channel_url:
                return JsonResponse({"error": "Failed to resolve handle to full channel URL."}, status=404)
            
            channel_id = full_channel_url.split("channel/")[1]
            playlist_id = get_uploads_playlist_id(api_key, channel_id)
            if not playlist_id:
                return JsonResponse({"error": "Failed to fetch uploads playlist ID."}, status=404)
            
            video_ids = get_video_ids(api_key, playlist_id)
            if not video_ids:
                return JsonResponse({"error": "No videos found in the channel."}, status=404)

            # ❌ Exclude Shorts
            filtered_video_ids = get_video_details(api_key, video_ids)

            if not filtered_video_ids:
                return JsonResponse({"error": "No valid videos (non-Shorts) found."}, status=404)
            
            # Fetch tags only for filtered videos
            video_tags_map = {video_id: fetch_video_tags(api_key, video_id) for video_id in filtered_video_ids}
            
            # Categorize videos by tags and add unique IDs
            categorized_videos = categorize_videos_by_tags(video_tags_map, max_depth=3)
            
            response = {
                "name": channel_name,
                "children": categorized_videos.get("children", [])
            }
            return JsonResponse(response, status=200)
        
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON body."}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

# @method_decorator(csrf_exempt, name='dispatch')
# class FetchChannelTagsView(APIView):


#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]
#     def post(self, request):
#         try:
#             # Parse JSON from request body
#             body = json.loads(request.body)
#             handle = body.get("channel_url")  # Accept just the channel handle
#             api_key = "AIzaSyDP03hg1_-sklhoaz0KGA9RHLDwRPaMlHg"
            
#             if not api_key or not handle:
#                 return JsonResponse({"error": "API key or channel handle is missing."}, status=400)
            
#             # Construct the full channel URL
#             handle_url = f"https://www.youtube.com/@{handle}"
            
#             # Extract channel name from the handle
#             channel_name = handle
            
#             # Resolve channel URL
#             full_channel_url = resolve_handle_to_channel_url(handle_url, api_key)
#             if not full_channel_url:
#                 return JsonResponse({"error": "Failed to resolve handle to full channel URL."}, status=404)
            
#             channel_id = full_channel_url.split("channel/")[1]
            
#             # Get uploads playlist ID
#             playlist_id = get_uploads_playlist_id(api_key, channel_id)
#             if not playlist_id:
#                 return JsonResponse({"error": "Failed to fetch uploads playlist ID."}, status=404)
            
#             # Get all video IDs
#             video_ids = get_video_ids(api_key, playlist_id)
#             if not video_ids:
#                 return JsonResponse({"error": "No videos found in the channel."}, status=404)
            
#             # Fetch tags for each video
#             video_tags_map = {video_id: fetch_video_tags(api_key, video_id) for video_id in video_ids}
            
            
#             # Categorize videos by tags and add unique IDs
#             categorized_videos = categorize_videos_by_tags(video_tags_map)
#             for category in categorized_videos.get("children", []):
#                 category["id"] = str(uuid.uuid4())  # Generate a unique ID for each category
#                 for subcategory in category.get("children", []):
#                     subcategory["id"] = str(uuid.uuid4())  # Generate a unique ID for each subcategory
            
#             # Prepare the final JSON response
#             response = {
#                 "name": channel_name,
#                 "children": categorized_videos.get("children", [])
#             }
#             return JsonResponse(response, status=200)
        
#         except json.JSONDecodeError:
#             return JsonResponse({"error": "Invalid JSON body."}, status=400)
#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class SaveCategorizedVideosView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            # Parse the JSON data from the request
            body = json.loads(request.body)
            name = body.get('name')  # Channel name
            children = body.get('children')  # Categorized videos array
            
            # Ensure 'name' and 'children' are provided
            if not name or not children:
                return JsonResponse({"error": "Both 'name' and 'children' are required."}, status=400)
            
            # Check if the name is unique
            if CategorizedVideos.objects.filter(name=name).exists():
                return JsonResponse({"error": "The 'name' must be unique."}, status=400)
            
            # Save the instance of CategorizedVideos
            categorized_video_instance = CategorizedVideos(
                name=name,
                response=json.dumps(children)  # Save the 'children' array as a JSON string
            )
            categorized_video_instance.save()
            
            return JsonResponse({"message": "Categorized videos saved successfully."}, status=200)
        
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON body."}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')            
class FetchCategorizedVideosByNameView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            # Extract the 'name' from the query parameters
            name = request.GET.get('name')
            
            # Ensure 'name' is provided
            if not name:
                return JsonResponse({"error": "Name parameter is required."}, status=400)
            
            # Try to retrieve the instance by name
            categorized_video_instance = CategorizedVideos.objects.filter(name=name).first()
            
            if not categorized_video_instance:
                return JsonResponse({"error": "Categorized video not found."}, status=404)
            
            # Return the saved categorized videos data as JSON
            return JsonResponse({
                "name": categorized_video_instance.name,
                "children": json.loads(categorized_video_instance.response)
            }, status=200)
        
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class DeleteCategorizedVideosByNameView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]





    def delete(self, request):
        try:
            # Extract the 'name' from the query parameters
            name = request.GET.get('name')
            
            # Ensure 'name' is provided
            if not name:
                return JsonResponse({"error": "Name parameter is required."}, status=400)
            
            # Try to retrieve the instance by name
            categorized_video_instance = CategorizedVideos.objects.filter(name=name).first()
            
            if not categorized_video_instance:
                return JsonResponse({"error": "Categorized video not found."}, status=404)
            
            # Delete the instance
            categorized_video_instance.delete()
            
            return JsonResponse({"message": "Categorized video deleted successfully."}, status=200)
        
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class GetCategorizedVideosNamesView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            # Get all the names of the saved categorized videos
            categorized_video_names = CategorizedVideos.objects.values_list('name', flat=True)
            
            # Return the names as a JSON response
            return JsonResponse({
                "categorized_video_names": list(categorized_video_names)
            }, status=200)
        
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)



@method_decorator(csrf_exempt, name='dispatch')
class FetchYouTubeVideoDataView(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            # Parse JSON from request body
            body = json.loads(request.body)
            video_ids = body.get("video_ids", [])

            # Ensure video IDs are provided
            if not video_ids:
                return JsonResponse({"error": "No video IDs provided."}, status=400)

            # Construct the API request
            video_id_string = ",".join(video_ids)
            base_url = "https://www.googleapis.com/youtube/v3/videos"
            params = {
                "part": "snippet,statistics",
                "id": video_id_string,
                "key": "AIzaSyDP03hg1_-sklhoaz0KGA9RHLDwRPaMlHg",
            }





            # Send request to YouTube API
            response = requests.get(base_url, params=params)

            if response.status_code != 200:
                return JsonResponse({"error": "Failed to fetch data from YouTube."}, status=response.status_code)

            data = response.json()
            video_data_list = []

            for item in data.get("items", []):
                video_info = {
                    "video_id": item["id"],
                    "title": item["snippet"]["title"],
                    "views": int(item["statistics"].get("viewCount", 0)),
                    "likes": int(item["statistics"].get("likeCount", 0)),
                    "thumbnail": item["snippet"]["thumbnails"]["high"]["url"]
                }
                video_data_list.append(video_info)

            return JsonResponse(video_data_list, safe=False, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON body."}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)



@method_decorator(csrf_exempt, name='dispatch')
class DeleteCategorizedVideosByNameView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def remove_tags(self, node, tags_to_delete):
        """Recursively removes tags and their children"""
        if not node:
            return None

        # If current node should be deleted, return None
        if node.get("name") in tags_to_delete:
            return None

        # Process children recursively
        if "children" in node and isinstance(node["children"], list):
            filtered_children = [
                self.remove_tags(child, tags_to_delete)
                for child in node["children"]
            ]
            node["children"] = [child for child in filtered_children if child]

        return node

    def delete(self, request):
        try:
            # Parse request body
            data = json.loads(request.body)

            # Validate request data
            if "name" not in data or "children" not in data or "tags_to_delete" not in data:
                return JsonResponse({"error": "Invalid request format."}, status=400)

            tags_to_delete = set(data["tags_to_delete"])  # Use set for faster lookup
            filtered_data = self.remove_tags(data, tags_to_delete)

            # Remove "tags_to_delete" before returning response
            if "tags_to_delete" in filtered_data:
                del filtered_data["tags_to_delete"]

            return JsonResponse(filtered_data, status=200, json_dumps_params={'ensure_ascii': False})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format."}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
