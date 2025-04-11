import os
import subprocess
from crontab import CronTab
from app.services.backup_service import BackupService

class SchedulerService:
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