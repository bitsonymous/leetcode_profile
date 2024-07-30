import asyncio
import httpx
import logging
from django.core.cache import cache
from django.shortcuts import render



# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Rate limit settings
RATE_LIMIT_PER_MINUTE = 5
RATE_LIMIT_DELAY = 60 / RATE_LIMIT_PER_MINUTE

# Semaphore to limit concurrent requests
semaphore = asyncio.Semaphore(5)  # Adjust the limit as needed

# Mapping of usernames to real names
USER_NAME_TO_REAL_NAME = {
    'bitsonymous': 'Himanshu Yadav',
    'Kunal-Sharma': 'Kunal Sharma',
    'lakshya_12': 'Lakshya Varshaney',
    'cbanujgoyal': 'Anuj Goyal',
    'itssme_jai': 'Jai Krishna',
    '_cup_of_cofee': 'Mukul Chauhan',
    'chamoli2k2': 'Gaurav Chamoli',
    'bewildered_': 'Jivtesh Shrivastav',
    'pranjal_trvd': 'Pranjal Trivedi'
    # Add more mappings as needed
}

async def fetch_user_profile_data(username):
    cache_key_profile = f"profile_data_{username}"
    cache_key_contest = f"contest_data_{username}"

    profile_data = cache.get(cache_key_profile)
    contest_data = cache.get(cache_key_contest)

    if not profile_data or not contest_data:
        user_profile_url = f"https://leetcode-api-faisalshohag.vercel.app/{username}"
        contest_rating_url = f"https://alfa-leetcode-api.onrender.com/userContestRankingInfo/{username}"

        async with httpx.AsyncClient(timeout=10.0) as client:
            async with semaphore:
                try:
                    # Implement rate limiting
                    await asyncio.sleep(RATE_LIMIT_DELAY)

                    profile_response = await client.get(user_profile_url)
                    profile_response.raise_for_status()  # Raise an exception for HTTP errors
                    profile_data = profile_response.json()
                    logger.debug(f"Profile data for {username}: {profile_data}")
                    
                    await asyncio.sleep(RATE_LIMIT_DELAY)

                    contest_response = await client.get(contest_rating_url)
                    contest_response.raise_for_status()  # Raise an exception for HTTP errors
                    contest_data = contest_response.json()
                    logger.debug(f"Contest data for {username}: {contest_data}")
                    
                    # Cache the responses
                    cache.set(cache_key_profile, profile_data, timeout=3600)  # Cache for 1 hour
                    cache.set(cache_key_contest, contest_data, timeout=3600)  # Cache for 1 hour

                except httpx.HTTPStatusError as exc:
                    logger.error(f"HTTP error occurred for {username}: {exc}")
                    # Handle specific HTTP errors
                    profile_data = {}
                    contest_data = {}
                except httpx.RequestError as exc:
                    logger.error(f"An error occurred while requesting data for {username}: {exc}")
                    profile_data = {}
                    contest_data = {}

    total_solved = profile_data.get("totalSolved", 0)
    today_submissions = list(profile_data.get("submissionCalendar", {}).values())[-1] if profile_data.get("submissionCalendar") else 0
    contest_rating = contest_data.get("data", {}).get("userContestRanking", {}).get("rating", "N/A")

    return {
        'username': username,
        'total_solved': total_solved,
        'today_submissions': today_submissions,
        'contest_rating': contest_rating,
    }

def user_profiles(request):
    usernames = list(USER_NAME_TO_REAL_NAME.keys())  # Use keys from the mapping

    async def get_all_user_data():
        tasks = [fetch_user_profile_data(username) for username in usernames]
        return await asyncio.gather(*tasks)
    
    # Use asyncio to fetch all user data concurrently
    user_data_list = asyncio.run(get_all_user_data())

    # Add real names to user data and sort by total solved questions
    for user_data in user_data_list:
        user_data['real_name'] = USER_NAME_TO_REAL_NAME.get(user_data['username'], "Unknown")
    
    user_data_list.sort(key=lambda x: x['total_solved'], reverse=True)

    return render(request, 'main.html', {'user_data_list': user_data_list})