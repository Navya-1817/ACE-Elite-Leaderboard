import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict
import re


class CodeChefAPI:
    """CodeChef web scraping integration (minimal)"""
    
    BASE_URL = "https://www.codechef.com"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def get_user_stats(self, username: str) -> Optional[Dict]:
        """
        Scrape user statistics from CodeChef profile page
        Returns dict with rating and solved count
        """
        try:
            url = f"{self.BASE_URL}/users/{username}"
            response = self.session.get(url, timeout=15)
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try to find rating
            rating = 0
            rating_element = soup.find('div', class_='rating-number')
            if rating_element:
                try:
                    rating = int(rating_element.text.strip())
                except ValueError:
                    pass
            
            # Alternative: check for rating in text
            if rating == 0:
                rating_text = soup.find(text=re.compile(r'Rating\s*:\s*\d+'))
                if rating_text:
                    match = re.search(r'\d+', rating_text)
                    if match:
                        rating = int(match.group())
            
            # Try to find solved count
            solved = 0
            
            # Look for problems solved section
            problems_section = soup.find('section', class_='problems-solved')
            if problems_section:
                solved_text = problems_section.find('h5')
                if solved_text:
                    match = re.search(r'(\d+)', solved_text.text)
                    if match:
                        solved = int(match.group(1))
            
            # Alternative: look for "Fully Solved" count
            if solved == 0:
                fully_solved = soup.find('h3', text=re.compile(r'Fully Solved'))
                if fully_solved:
                    # Find the count near this heading
                    count_elem = fully_solved.find_next('span', class_='count')
                    if count_elem:
                        try:
                            solved = int(count_elem.text.strip().replace('(', '').replace(')', ''))
                        except ValueError:
                            pass
            
            # Alternative: search in script tags for data
            if solved == 0:
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string and 'fully solved' in script.string.lower():
                        match = re.search(r'"fully_solved"\s*:\s*(\d+)', script.string)
                        if match:
                            solved = int(match.group(1))
                            break
            
            # Check if we got at least some data
            if rating == 0 and solved == 0:
                # Try to verify user exists by checking for username on page
                username_elem = soup.find('div', class_='user-details-container')
                if not username_elem:
                    return None
            
            return {
                'username': username,
                'rating': rating,
                'solved': solved,
                'stars': self._get_star_rating(rating)
            }
            
        except requests.RequestException as e:
            print(f"Error fetching CodeChef data for {username}: {e}")
            return None
        except Exception as e:
            print(f"Error parsing CodeChef data for {username}: {e}")
            return None
    
    def _get_star_rating(self, rating: int) -> str:
        """Convert numeric rating to star rating"""
        if rating >= 2500:
            return '7★'
        elif rating >= 2200:
            return '6★'
        elif rating >= 1800:
            return '5★'
        elif rating >= 1600:
            return '4★'
        elif rating >= 1400:
            return '3★'
        elif rating >= 1200:
            return '2★'
        elif rating > 0:
            return '1★'
        return 'Unrated'
    
    def validate_username(self, username: str) -> bool:
        """Check if a CodeChef username exists"""
        try:
            url = f"{self.BASE_URL}/users/{username}"
            response = self.session.get(url, timeout=10)
            return response.status_code == 200
        except:
            return False


# Singleton instance
codechef_api = CodeChefAPI()
