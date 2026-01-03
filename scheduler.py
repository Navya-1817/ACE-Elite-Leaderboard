from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import time
import concurrent.futures
from models import db, Student, StatsSnapshot
from services.codeforces import codeforces_api
from services.leetcode import leetcode_api
from services.codechef import codechef_api


class StatsScheduler:
    """Background scheduler for automatic stats fetching"""
    
    def __init__(self, app=None):
        self.scheduler = BackgroundScheduler()
        self.app = app
        
    def init_app(self, app):
        """Initialize scheduler with Flask app"""
        self.app = app
        
    def start(self):
        """Start the background scheduler"""
        if not self.scheduler.running:
            # Fetch stats every 24 hours
            self.scheduler.add_job(
                func=self.fetch_all_stats,
                trigger=IntervalTrigger(hours=24),
                id='fetch_stats_job',
                name='Fetch all student stats',
                replace_existing=True
            )
            self.scheduler.start()
            print("✓ Stats scheduler started (runs every 24 hours)")
    
    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            print("✓ Stats scheduler stopped")
    
    def fetch_all_stats(self):
        """Fetch stats for all students from all platforms using batch processing"""
        if not self.app:
            print("❌ Scheduler not initialized with Flask app")
            return
        
        with self.app.app_context():
            students = Student.query.all()
            
            if not students:
                print("ℹ No students found to fetch stats for")
                return
            
            print(f"\n{'='*60}")
            print(f"📊 Starting stats fetch for {len(students)} students")
            print(f"⏰ Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
            print(f"🚀 Processing in batches of 10 students")
            print(f"{'='*60}\n")
            
            # Process students in batches
            batch_size = 10
            for i in range(0, len(students), batch_size):
                batch = students[i:i + batch_size]
                print(f"🔄 Processing batch {i//batch_size + 1} ({len(batch)} students)")
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                    futures = []
                    for student in batch:
                        futures.append(executor.submit(self._fetch_student_all_platforms, student))
                    
                    # Wait for all futures to complete
                    concurrent.futures.wait(futures)
                
                # Rate limiting between batches
                if i + batch_size < len(students):
                    time.sleep(2)
                    print()
            
            print(f"{'='*60}")
            print("✅ Stats fetch completed")
            print(f"{'='*60}\n")
    
    def _fetch_student_all_platforms(self, student):
        """Fetch stats for a single student from all platforms"""
        print(f"📌 Fetching: {student.name} ({student.roll_number})")
        
        # Fetch from all platforms
        if student.cf_handle:
            self._fetch_codeforces_stats(student)
        
        if student.lc_username:
            self._fetch_leetcode_stats(student)
        
        if student.cc_username:
            self._fetch_codechef_stats(student)
    
    def _fetch_codeforces_stats(self, student):
        """Fetch and store Codeforces stats for a student with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                data = codeforces_api.get_user_info(student.cf_handle)
                
                if data:
                    snapshot = StatsSnapshot(
                        student_id=student.id,
                        platform='CF',
                        rating=data.get('rating', 0),
                        max_rating=data.get('max_rating', 0),
                        solved=data.get('solved', 0),
                        fetch_status='success'
                    )
                    db.session.add(snapshot)
                    db.session.commit()
                    print(f"  🔵 CF ✓")
                    return
                else:
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    self._save_failed_snapshot(student.id, 'CF', 'Failed to fetch data')
                    print(f"  🔵 CF ❌")
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                self._save_failed_snapshot(student.id, 'CF', str(e))
                print(f"  🔵 CF ❌")
    
    def _fetch_leetcode_stats(self, student):
        """Fetch and store LeetCode stats for a student with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                data = leetcode_api.get_user_stats(student.lc_username)
                
                if data:
                    snapshot = StatsSnapshot(
                        student_id=student.id,
                        platform='LC',
                        rating=None,
                        solved=data.get('total_solved', 0),
                        easy=data.get('easy', 0),
                        medium=data.get('medium', 0),
                        hard=data.get('hard', 0),
                        fetch_status='success'
                    )
                    db.session.add(snapshot)
                    db.session.commit()
                    print(f"  🟡 LC ✓")
                    return
                else:
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    self._save_failed_snapshot(student.id, 'LC', 'Failed to fetch data')
                    print(f"  🟡 LC ❌")
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                self._save_failed_snapshot(student.id, 'LC', str(e))
                print(f"  🟡 LC ❌")
    
    def _fetch_codechef_stats(self, student):
        """Fetch and store CodeChef stats for a student with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                data = codechef_api.get_user_stats(student.cc_username)
                
                if data:
                    snapshot = StatsSnapshot(
                        student_id=student.id,
                        platform='CC',
                        rating=data.get('rating', 0),
                        solved=data.get('solved', 0),
                        fetch_status='success'
                    )
                    db.session.add(snapshot)
                    db.session.commit()
                    print(f"  🟤 CC ✓")
                    return
                else:
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    self._save_failed_snapshot(student.id, 'CC', 'Failed to fetch data')
                    print(f"  🟤 CC ❌")
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                self._save_failed_snapshot(student.id, 'CC', str(e))
                print(f"  🟤 CC ❌")
    
    def _save_failed_snapshot(self, student_id, platform, error_message):
        """Save a failed fetch attempt"""
        try:
            snapshot = StatsSnapshot(
                student_id=student_id,
                platform=platform,
                fetch_status='failed',
                error_message=error_message,
                solved=0
            )
            db.session.add(snapshot)
            db.session.commit()
        except Exception as e:
            print(f"Error saving failed snapshot: {e}")
            db.session.rollback()
    
    def fetch_student_stats(self, student_id):
        """Manually fetch stats for a specific student (useful for testing)"""
        with self.app.app_context():
            student = Student.query.get(student_id)
            if not student:
                return False
            
            if student.cf_handle:
                self._fetch_codeforces_stats(student)
            if student.lc_username:
                self._fetch_leetcode_stats(student)
            if student.cc_username:
                self._fetch_codechef_stats(student)
            
            return True


# Global scheduler instance
scheduler = StatsScheduler()
