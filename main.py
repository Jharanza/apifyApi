from fastapi import FastAPI, HTTPException
from apify_client import ApifyClient
import json
from pathlib import Path

API_TOKEN = "apify_api_7oOQ8c8pTtjyDGTVr113OCzETU8NAh4saRLA"
client = ApifyClient(API_TOKEN)

app = FastAPI()

DATA_FILE = Path('reels_data_json')

def save_data_to_file (data):
    """ Save the data into a json file """
    with open(DATA_FILE, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def load_data_from_file ():
    """ Get the data from the json file """
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


@app.get('/api/reels/{username}')
async def get_reels (username: str):
    """ Endpoint to get the lasts reels and save it in a json file """
    try:
        run_input = {
            'username': [username],
            'resultsLimit': 3,
        }

        run = client.actor("xMc5Ga1oCONPmWJIa").call(run_input=run_input)
        
        latest_reels = []
        for item in client.dataset(run['defaultDatasetId']).iterate_items():
            latest_reels.append({
                "type": item.get("type"),
                "media_url": item.get("videoUrl") or item.get("imageUrl"),
                "post_url": item.get("url"),
            })
            
        save_data_to_file(latest_reels)

        return latest_reels

    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Error fetching reels: {str(e)}")

@app.get('/api/reels')
async def get_saved_reels():
    """ Endpoint to get the data from the json file """
    try:
        data = load_data_from_file()
        if not data:
            raise HTTPException(status_code=404, detail="No reels data found.")
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading saved reels: {str(e)}")