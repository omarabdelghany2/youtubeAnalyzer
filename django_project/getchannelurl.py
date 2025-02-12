import requests

def resolve_handle_to_channel_url(handle_url, api_key):
    try:
        # Extract the handle (e.g., @StanleyMOV) from the URL
        if '@' in handle_url:
            handle = handle_url.split('@')[1].strip('/')

            # Use the YouTube Data API to search for the channel by handle
            url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={handle}&type=channel&key={api_key}"
            response = requests.get(url)
            response.raise_for_status()

            # Check if the response contains the channel info
            data = response.json()
            if 'items' in data and data['items']:
                # Fetch the channel ID from the API response
                channel_id = data['items'][0]['id']['channelId']
                return f"https://www.youtube.com/channel/{channel_id}"
            else:
                print("Channel not found for the handle.")
                return None
        else:
            print("Invalid handle URL.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None


# Example usage
API_KEY = "AIzaSyDP03hg1_-sklhoaz0KGA9RHLDwRPaMlHg"
CHANNEL_URL = "https://www.youtube.com/@StanleyMOV"

# Fetch and print the resolved channel URL
resolved_channel_url = resolve_handle_to_channel_url(CHANNEL_URL, API_KEY)
print(f"Resolved Channel URL: {resolved_channel_url}")
