import os
import datetime
from crontab import CronTab
from app.services.backup_service import BackupService

class BackupSchedule:
    """Simple backup schedule model"""
    def __init__(self, id, db_name, db_type, frequency, day_of_week=None, day_of_month=None, hour=0, minute=0):
        self.id = id
        self.db_name = db_name
        self.db_type = db_type  # 'mysql' or 'postgres'
        self.frequency = frequency  # 'daily', 'weekly', 'monthly'
        self.day_of_week = day_of_week
        self.day_of_month = day_of_month
        self.hour = hour
        self.minute = minute
        self.created_at = datetime.datetime.now()
        self.next_run = self._calculate_next_run()
    
    def _calculate_next_run(self):
        """Calculate the next run time based on frequency"""
        now = datetime.datetime.now()
        
        if self.frequency == 'daily':
            next_run = datetime.datetime(
                now.year, now.month, now.day, 
                hour=self.hour, minute=self.minute
            )
            if next_run < now:
                next_run += datetime.timedelta(days=1)
                
        elif self.frequency == 'weekly':
            days_ahead = self.day_of_week - now.weekday()
            if days_ahead < 0 or (days_ahead == 0 and now.hour >= self.hour and now.minute >= self.minute):
                days_ahead += 7
                
            next_run = datetime.datetime(
                now.year, now.month, now.day,
                hour=self.hour, minute=self.minute
            ) + datetime.timedelta(days=days_ahead)
            
        elif self.frequency == 'monthly':
            if now.day > self.day_of_month or (now.day == self.day_of_month and now.hour >= self.hour and now.minute >= self.minute):
                # Move to next month
                if now.month == 12:
                    next_month = 1
                    next_year = now.year + 1
                else:
                    next_month = now.month + 1
                    next_year = now.year
                    
                next_run = datetime.datetime(
                    next_year, next_month, min(self.day_of_month, 28),
                    hour=self.hour, minute=self.minute
                )
            else:
                next_run = datetime.datetime(
                    now.year, now.month, self.day_of_month,
                    hour=self.hour, minute=self.minute
                )
        else:
            next_run = now
            
        return next_run

class SchedulerService:
    """Service for backup scheduling"""
    # In-memory schedule storage (for development/fallback)
    _schedules = []
    
    @classmethod
    def get_backup_schedules(cls):
        """Get all backup schedules"""
        return cls._schedules
    
    @classmethod
    def create_backup_schedule(cls, db_name, db_type, frequency, day_of_week=None, day_of_month=None, hour=0, minute=0):
        """Create a new backup schedule"""
        # Validate frequency and corresponding parameters
        if frequency == 'weekly' and day_of_week is None:
            day_of_week = 0  # Default to Monday
        
        if frequency == 'monthly' and day_of_month is None:
            day_of_month = 1  # Default to 1st of month
        
        # Create backup schedule
        next_id = max([s.id for s in cls._schedules], default=0) + 1
        schedule = BackupSchedule(
            id=next_id,
            db_name=db_name,
            db_type=db_type,
            frequency=frequency,
            day_of_week=day_of_week,
            day_of_month=day_of_month,
            hour=hour,
            minute=minute
        )
        
        # Add to in-memory storage
        cls._schedules.append(schedule)
        
        # Try to create a cron job for this schedule
        try:
            cls._create_cron_job(schedule)
        except Exception:
            pass  # Ignore cron errors in development/fallback mode
        
        return schedule
    
    @classmethod
    def delete_backup_schedule(cls, schedule_id):
        """Delete a backup schedule by ID"""
        schedule = None
        for s in cls._schedules:
            if s.id == schedule_id:
                schedule = s
                break
        
        if schedule:
            # Remove from in-memory storage
            cls._schedules.remove(schedule)
            
            # Try to remove the cron job
            try:
                cls._remove_cron_job(schedule)
            except Exception:
                pass  # Ignore cron errors in development/fallback mode
            
            return True
        
        return False
    
    @classmethod
    def _create_cron_job(cls, schedule):
        """Create a cron job for the backup schedule"""
        try:
            # Get the current user's crontab
            cron = CronTab(user=True)
            
            # Create a new job
            job = cron.new(
                command=f"/opt/nexdb/venv/bin/python3 -m app.backup_cli {schedule.db_type} {schedule.db_name}"
            )
            
            # Set the schedule based on frequency
            if schedule.frequency == 'daily':
                job.setall(f"{schedule.minute} {schedule.hour} * * *")
            elif schedule.frequency == 'weekly':
                job.setall(f"{schedule.minute} {schedule.hour} * * {schedule.day_of_week}")
            elif schedule.frequency == 'monthly':
                job.setall(f"{schedule.minute} {schedule.hour} {schedule.day_of_month} * *")
            
            # Add comment for identification
            job.set_comment(f"NEXDB backup schedule {schedule.id}")
            
            # Write the changes to crontab
            cron.write()
            
            return True
        except Exception:
            return False
    
    @classmethod
    def _remove_cron_job(cls, schedule):
        """Remove a cron job for the backup schedule"""
        try:
            # Get the current user's crontab
            cron = CronTab(user=True)
            
            # Find and remove the job with the matching comment
            for job in cron.find_comment(f"NEXDB backup schedule {schedule.id}"):
                cron.remove(job)
            
            # Write the changes to crontab
            cron.write()
            
            return True
        except Exception:
            return False

    @staticmethod
    def schedule_backup(db_type, db_name, schedule, user_id=None):
        """
        Schedule a database backup using cron
        
        schedule format: 
        - daily: "0 0 * * *" (midnight)
        - weekly: "0 0 * * 0" (Sunday midnight)
        - monthly: "0 0 1 * *" (1st of month midnight)
        - custom: A valid cron expression
        """
        try:
            # Get current user's crontab
            cron = CronTab(user=True)
            
            # Create backup script path
            script_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "scripts")
            os.makedirs(script_dir, exist_ok=True)
            
            script_path = os.path.join(script_dir, f"backup_{db_type}_{db_name}.py")
            
            # Create the backup script
            with open(script_path, 'w') as f:
                f.write(f"""#!/usr/bin/env python3
import sys
import os
sys.path.append('{os.path.dirname(os.path.dirname(os.path.dirname(__file__)))}')
from app import create_app
from app.services.backup_service import BackupService

app = create_app()
with app.app_context():
    BackupService.create_backup('{db_type}', '{db_name}', {user_id})
""")
            
            # Make script executable
            os.chmod(script_path, 0o755)
            
            # Preset schedules
            schedule_presets = {
                'daily': '0 0 * * *',
                'weekly': '0 0 * * 0',
                'monthly': '0 0 1 * *'
            }
            
            # Get cron expression
            cron_expr = schedule_presets.get(schedule, schedule)
            
            # Add new cron job
            job = cron.new(command=f"python3 {script_path}")
            job.setall(cron_expr)
            
            # Save crontab
            cron.write()
            
            return {
                'db_type': db_type,
                'db_name': db_name,
                'schedule': cron_expr,
                'script_path': script_path
            }
            
        except Exception as e:
            print(f"Error scheduling backup: {str(e)}")
            return None
    
    @staticmethod
    def delete_backup_schedule(db_type, db_name):
        """Delete a backup schedule"""
        try:
            # Get current user's crontab
            cron = CronTab(user=True)
            
            # Find and remove the job
            script_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "scripts")
            script_path = os.path.join(script_dir, f"backup_{db_type}_{db_name}.py")
            
            # Find jobs matching this command
            jobs_removed = 0
            for job in cron.find_command(script_path):
                cron.remove(job)
                jobs_removed += 1
            
            # Delete the script if it exists
            if os.path.exists(script_path):
                os.remove(script_path)
            
            # Save crontab
            cron.write()
            
            return jobs_removed > 0
            
        except Exception as e:
            print(f"Error deleting backup schedule: {str(e)}")
            return False
    
    @staticmethod
    def get_backup_schedules():
        """Get all backup schedules"""
        try:
            # Get current user's crontab
            cron = CronTab(user=True)
            
            # Find backup jobs
            schedules = []
            script_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "scripts")
            
            for job in cron:
                cmd = job.command
                if "backup_" in cmd and ".py" in cmd:
                    # Parse db_type and db_name from command
                    script_name = cmd.split("/")[-1].replace("python3 ", "").strip()
                    script_path = os.path.join(script_dir, script_name)
                    
                    if os.path.exists(script_path):
                        parts = script_name.replace(".py", "").split("_")
                        if len(parts) >= 3:
                            db_type = parts[1]
                            db_name = "_".join(parts[2:])
                            
                            schedules.append({
                                'db_type': db_type,
                                'db_name': db_name,
                                'schedule': str(job.slices),
                                'script_path': script_path
                            })
            
            return schedules
            
        except Exception as e:
            print(f"Error getting backup schedules: {str(e)}")
            return [] 