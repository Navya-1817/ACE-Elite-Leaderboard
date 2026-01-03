import requests
import time
from typing import Optional, Dict


class CodeforcesAPI:
    """Codeforces API integration"""
    
    BASE_URL = "https://codeforces.com/api"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CP-Tracker-Bot/1.0'
        })
    
    def get_user_info(self, handle: str) -> Optional[Dict]:
        """
        Fetch user information from Codeforces
        Returns dict with rating, max_rating, and solved count
        """
        try:
            # Get user info for rating
            url = f"{self.BASE_URL}/user.info?handles={handle}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            if data['status'] != 'OK':
                return None
            
            user = data['result'][0]
            
            # Get user submissions for solved count
            time.sleep(0.5)  # Rate limiting
            submissions_url = f"{self.BASE_URL}/user.status?handle={handle}"
            submissions_response = self.session.get(submissions_url, timeout=10)
            
            solved_problems = set()
            if submissions_response.status_code == 200:
                submissions_data = submissions_response.json()
                if submissions_data['status'] == 'OK':
                    for submission in submissions_data['result']:
                        if submission.get('verdict') == 'OK':
                            problem = submission['problem']
                            problem_id = f"{problem['contestId']}{problem['index']}"
                            solved_problems.add(problem_id)
            
            return {
                'rating': user.get('rating', 0),
                'max_rating': user.get('maxRating', 0),
                'solved': len(solved_problems),
                'handle': user.get('handle'),
                'rank': user.get('rank', 'Unrated')
            }
            
        except requests.RequestException as e:
            print(f"Error fetching Codeforces data for {handle}: {e}")
            return None
        except (KeyError, ValueError, IndexError) as e:
            print(f"Error parsing Codeforces data for {handle}: {e}")
            return None
    
    def validate_handle(self, handle: str) -> bool:
        """Check if a Codeforces handle exists"""
        try:
            url = f"{self.BASE_URL}/user.info?handles={handle}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data['status'] == 'OK'
            return False
        except:
            return False


# Singleton instance
codeforces_api = CodeforcesAPI()
