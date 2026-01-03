import requests
from typing import Optional, Dict


class LeetCodeAPI:
    """LeetCode GraphQL API integration"""
    
    GRAPHQL_URL = "https://leetcode.com/graphql"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/json',
            'Referer': 'https://leetcode.com'
        })
    
    def get_user_stats(self, username: str) -> Optional[Dict]:
        """
        Fetch user statistics from LeetCode
        Returns dict with solved counts by difficulty
        """
        try:
            query = """
            query getUserProfile($username: String!) {
                matchedUser(username: $username) {
                    username
                    submitStats {
                        acSubmissionNum {
                            difficulty
                            count
                        }
                    }
                    profile {
                        ranking
                    }
                }
            }
            """
            
            payload = {
                'query': query,
                'variables': {'username': username}
            }
            
            response = self.session.post(
                self.GRAPHQL_URL,
                json=payload,
                timeout=15
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            if 'errors' in data or not data.get('data', {}).get('matchedUser'):
                return None
            
            user_data = data['data']['matchedUser']
            submissions = user_data['submitStats']['acSubmissionNum']
            
            # Parse difficulty counts
            easy = 0
            medium = 0
            hard = 0
            total = 0
            
            for stat in submissions:
                difficulty = stat['difficulty']
                count = stat['count']
                
                if difficulty == 'Easy':
                    easy = count
                elif difficulty == 'Medium':
                    medium = count
                elif difficulty == 'Hard':
                    hard = count
                elif difficulty == 'All':
                    total = count
            
            return {
                'username': user_data['username'],
                'total_solved': total,
                'easy': easy,
                'medium': medium,
                'hard': hard,
                'ranking': user_data.get('profile', {}).get('ranking', 0)
            }
            
        except requests.RequestException as e:
            print(f"Error fetching LeetCode data for {username}: {e}")
            return None
        except (KeyError, ValueError, IndexError) as e:
            print(f"Error parsing LeetCode data for {username}: {e}")
            return None
    
    def validate_username(self, username: str) -> bool:
        """Check if a LeetCode username exists"""
        try:
            result = self.get_user_stats(username)
            return result is not None
        except:
            return False


# Singleton instance
leetcode_api = LeetCodeAPI()
