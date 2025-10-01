import time
import requests
from dotenv import load_dotenv
import os


load_dotenv()


BRIGHTDATA_API_KEY = os.getenv("BRIGHTDATA_API_KEY")
BASE_URL = "https://api.brightdata.com/datasets/v3"



HEADERS = {
    "Authorization": f"Bearer {BRIGHTDATA_API_KEY}",
    "Content-Type": "application/json"
}



def trigger_scrape(dataset_id: str, urls: list) -> dict:
    """
    Trigger a Bright Data scrape job for LinkedIn (or similar URLs).
    
    Args:
        dataset_id (str): The dataset ID configured in Bright Data.
        urls (list): List of profile URLs to scrape.
    
    Returns:
        dict: Trigger response containing job info (including snapshot ID).
    """
    payload = [{"url": u} for u in urls]
    print(payload,'payload')
    response = requests.post(
        f"{BASE_URL}/trigger?dataset_id={dataset_id}&include_errors=true",
        headers=HEADERS,
        json=payload
    )
    print(response.json(),'response.json()')
    response.raise_for_status()
    return response.json()


def trigger_scrape_glassdoor_comments(dataset_id: str, urls: list,days: int = 1825) -> dict:
    """
    Trigger a Bright Data scrape job for LinkedIn (or similar URLs).
    
    Args:
        dataset_id (str): The dataset ID configured in Bright Data.
        urls (list): List of profile URLs to scrape.
    
    Returns:
        dict: Trigger response containing job info (including snapshot ID).
    """
    payload = [{"url": u,"days":1825} for u in urls]
    print(payload,'payload')
    response = requests.post(
        f"{BASE_URL}/trigger?dataset_id={dataset_id}&include_errors=true",
        headers=HEADERS,
        json=payload
    )
    print(response.json(),'response.json()')
    response.raise_for_status()
    return response.json()



def poll_progress(snapshot_id: str, max_attempts: int = 60, delay: int = 5) -> bool:
    """
    Poll Bright Data scrape progress until done, failed, or max_attempts reached.


    Args:
        snapshot_id (str): Snapshot/job ID from Bright Data.
        max_attempts (int): Maximum number of polling attempts.
        delay (int): Seconds to wait between attempts.


    Returns:
        bool: True if completed successfully, False otherwise.
    """
    api_key = os.getenv("BRIGHTDATA_API_KEY")
    if not api_key:
        raise ValueError("BRIGHTDATA_API_KEY not set in environment variables")


    progress_url = f"https://api.brightdata.com/datasets/v3/progress/{snapshot_id}"
    headers = {"Authorization": f"Bearer {api_key}"}


    for attempt in range(max_attempts):
        try:
            print(f"⏳ Checking snapshot progress... (attempt {attempt + 1}/{max_attempts})")


            response = requests.get(progress_url, headers=headers)
            response.raise_for_status()
            progress_data = response.json()


            status = progress_data.get("status")
            if status == "ready":
                print("✅ Snapshot completed!")
                return True
            elif status == "failed":
                print("❌ Snapshot failed")
                return False
            elif status == "running":
                print("🔄 Still processing...")
                time.sleep(delay)
            else:
                print(f"❓ Unknown status: {status}")
                time.sleep(delay)


        except Exception as e:
            print(f"⚠️ Error checking progress: {e}")
            time.sleep(delay)


    print("⏰ Timeout waiting for snapshot completion")
    return False


def trigger_scrape_glassdoor_comments(dataset_id: str, urls: list,days: int = 1825) -> dict:
    """
    Trigger a Bright Data scrape job for LinkedIn (or similar URLs).
    
    Args:
        dataset_id (str): The dataset ID configured in Bright Data.
        urls (list): List of profile URLs to scrape.
    
    Returns:
        dict: Trigger response containing job info (including snapshot ID).
    """
    payload = [{"url": u,"days":1825} for u in urls]

    response = requests.post(
        f"{BASE_URL}/trigger?dataset_id={dataset_id}&include_errors=true",
        headers=HEADERS,
        json=payload
    )
    print(response.json(),'response.json()')
    response.raise_for_status()
    return response.json()




def get_snapshot(snapshot_id: str, fmt: str = "json", poll_interval: int = 30, max_attempts: int = 10) -> dict | None:
    """
    Fetch snapshot results from Bright Data, waiting until it's ready.


    Args:
        snapshot_id (str): Snapshot/job ID.
        fmt (str): Format ("json" recommended).
        poll_interval (int): Seconds to wait between checks when building.
        max_attempts (int): Maximum number of attempts before giving up.


    Returns:
        dict | None: Scraped data if successful, None if failed.
    """
    url = f"{BASE_URL}/snapshot/{snapshot_id}?format={fmt}"


    for attempt in range(1, max_attempts + 1):
        try:
            print(f"📥 Attempt {attempt}/{max_attempts}: Downloading snapshot...")
            resp = requests.get(url, headers=HEADERS)
            resp.raise_for_status()


            data = resp.json()
            print(data, "data")


            if isinstance(data, dict) and data.get("status") == "building":
                print(f"⏳ Snapshot still building. Retrying in {poll_interval}s...")
                time.sleep(poll_interval)
                continue  # try again


            if data:
                print(f"🎉 Snapshot ready! Downloaded {len(data) if isinstance(data, list) else 1} items")
                return data
            else:
                print("⚠️ Snapshot returned empty data.")
                return None


        except Exception as e:
            print(f"❌ Error downloading snapshot: {e}")
            return None


    print("❌ Gave up waiting for snapshot to be ready.")
    return None