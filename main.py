from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from apify_client import ApifyClient
from decouple import config


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ig-zh.vercel.app"], # Cambiar "*" por un dominio específico si es necesario
    allow_credentials=True,
    allow_methods=["*"],  # Métodos HTTP permitidos
    allow_headers=["*"],  # Cabeceras HTTP permitidas
)



API_TOKEN = config('API_TOKEN')

if not API_TOKEN:
    raise ValueError('The token is not configured')

client = ApifyClient(API_TOKEN)

reels_storage = {}

@app.get("/")
async def root():
    """ Ruta raíz """
    return {"message": "Cors correctly configured"}

@app.post('/api/reels/{username}/start')
async def start_reels_processing(username: str):
    """Start the actor asynchronously"""
    try:
        run_input = {
            'username': [username],
            'resultsLimit': 3,
        }
        run = client.actor("xMc5Ga1oCONPmWJIa").start(run_input=run_input)
        return {"message": "Actor started", "runId": run["id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting the actor: {str(e)}")



@app.get('/api/reels/{run_id}/status')
async def get_actor_status(run_id: str):
    """Check the status of the actor run"""
    try:
        run = client.run(run_id).get()
        if run["status"] == "SUCCEEDED":
            dataset_id = run["defaultDatasetId"]
            reels = []
            for item in client.dataset(dataset_id).iterate_items():
                reels.append({
                    "type": item.get("type"),
                    "media_url": item.get("videoUrl") or item.get("imageUrl"),
                    "post_url": item.get("url"),
                })
            reels_storage[run_id] = reels

            return reels
        return {"status": run["status"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching actor status: {str(e)}")


@app.get('/api/reels')
async def get_saved_reels():
    """Endpoint to get all saved reels from in-memory storage"""
    try:
        if not reels_storage:
            raise HTTPException(status_code=404, detail="No reels data found.")
        
        # Combina todos los reels almacenados para diferentes IDs o usernames
        all_reels = []
        for key, reels in reels_storage.items():
            all_reels.extend(reels)
        
        return all_reels
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading saved reels: {str(e)}")

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
            
        reels_storage[username] = latest_reels

        return latest_reels

    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Error fetching reels: {str(e)}")