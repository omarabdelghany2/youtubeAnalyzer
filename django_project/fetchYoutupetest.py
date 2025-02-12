import requests

# Replace with your YouTube API key
API_KEY = "AIzaSyDP03hg1_-sklhoaz0KGA9RHLDwRPaMlHg"

def get_youtube_video_data(video_ids):
    """
    Fetches YouTube video details like views, likes, and thumbnail URL.

    :param video_ids: List of YouTube video IDs
    :return: List of dictionaries containing video data
    """
    video_data_list = []
    base_url = "https://www.googleapis.com/youtube/v3/videos"

    # Convert list of video IDs to a comma-separated string
    video_id_string = ",".join(video_ids)

    # API request parameters
    params = {
        "part": "snippet,statistics",
        "id": video_id_string,
        "key": API_KEY,
    }

    # Make request to YouTube API
    response = requests.get(base_url, params=params)
    
    if response.status_code != 200:
        print("Error fetching data:", response.json())
        return []

    data = response.json()

    # Extract relevant details from response
    for item in data.get("items", []):
        video_info = {
            "video_id": item["id"],
            "title": item["snippet"]["title"],
            "views": int(item["statistics"].get("viewCount", 0)),
            "likes": int(item["statistics"].get("likeCount", 0)),
            "thumbnail": item["snippet"]["thumbnails"]["high"]["url"]
        }
        video_data_list.append(video_info)

    return video_data_list


# Example Usage
if __name__ == "__main__":
    video_ids = ["dQw4w9WgXcQ", "3JZ_D3ELwOQ"]  # Replace with actual video IDs
    results = get_youtube_video_data(video_ids)
    
    for video in results:
        print(f"Title: {video['title']}")
        print(f"Views: {video['views']}")
        print(f"Likes: {video['likes']}")
        print(f"Thumbnail: {video['thumbnail']}\n")
