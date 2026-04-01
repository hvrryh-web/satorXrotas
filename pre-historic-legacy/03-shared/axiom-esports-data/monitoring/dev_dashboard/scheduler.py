"""
Maintenance Scheduler
Manages scheduled maintenance windows and notifications.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional
import asyncpg
import logging
import uuid

from .models import MaintenanceWindow, SystemLayer

logger = logging.getLogger(__name__)


class MaintenanceScheduler:
    """
    Schedules and manages maintenance windows.
    Sends notifications before maintenance starts.
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self._scheduler_task = None
        self._running = False
    
    async def start(self):
        """Start the maintenance scheduler."""
        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Maintenance scheduler started")
    
    async def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        logger.info("Maintenance scheduler stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop - checks for upcoming maintenance."""
        while self._running:
            try:
                await self._process_maintenance_windows()
                await self._send_notifications()
            except Exception as e:
                logger.exception("Scheduler loop error")
            
            await asyncio.sleep(60)  # Check every minute
    
    async def _process_maintenance_windows(self):
        """Process active and upcoming maintenance windows."""
        async with self.db_pool.acquire() as conn:
            # Start scheduled maintenance
            await conn.execute(
                """
                UPDATE maintenance_windows
                SET status = 'in_progress',
                    actual_start = NOW()
                WHERE status = 'scheduled'
                  AND scheduled_start <= NOW()
                  AND scheduled_end > NOW()
                """
            )
            
            # Complete finished maintenance
            await conn.execute(
                """
                UPDATE maintenance_windows
                SET status = 'completed',
                    actual_end = NOW()
                WHERE status = 'in_progress'
                  AND scheduled_end <= NOW()
                """
            )
    
    async def _send_notifications(self):
        """Send notifications for upcoming maintenance."""
        async with self.db_pool.acquire() as conn:
            # Find maintenance that needs notifications
            rows = await conn.fetch(
                """
                SELECT 
                    window_id, title, scheduled_start, notify_before_minutes,
                    array_length(notifications_sent, 1) as sent_count
                FROM maintenance_windows
                WHERE status = 'scheduled'
                  AND scheduled_start > NOW()
                  AND array_length(notify_before_minutes, 1) > 0
                """
            )
            
            for row in rows:
                window_id = row['window_id']
                start_time = row['scheduled_start']
                notify_minutes = row['notify_before_minutes']
                sent_count = row['sent_count'] or 0
                
                # Check if next notification should be sent
                if sent_count < len(notify_minutes):
                    next_notify_minutes = notify_minutes[sent_count]
                    notify_at = start_time - timedelta(minutes=next_notify_minutes)
                    
                    if datetime.utcnow().replace(tzinfo=start_time.tzinfo) >= notify_at:
                        await self._notify_maintenance(
                            window_id,
                            row['title'],
                            start_time,
                            next_notify_minutes
                        )
    
    async def _notify_maintenance(
        self,
        window_id: str,
        title: str,
        start_time: datetime,
        minutes_before: int
    ):
        """Send notification for upcoming maintenance."""
        # TODO: Implement actual notification (email, Slack, etc.)
        logger.info(
            f"NOTIFICATION: Maintenance '{title}' starting in {minutes_before} minutes "
            f"(at {start_time.isoformat()})"
        )
        
        # Record notification sent
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE maintenance_windows
                SET notifications_sent = array_append(notifications_sent, NOW())
                WHERE window_id = $1
                """,
                window_id
            )
    
    async def schedule_maintenance(
        self,
        title: str,
        description: Optional[str],
        start_time: datetime,
        end_time: datetime,
        affected_layers: List[SystemLayer],
        affected_components: List[str],
        created_by: str,
        notify_before_minutes: List[int] = None
    ) -> MaintenanceWindow:
        """Schedule a new maintenance window."""
        
        if notify_before_minutes is None:
            notify_before_minutes = [60, 15]  # Default: 1 hour, 15 minutes before
        
        window_id = f"mnt-{uuid.uuid4().hex[:8]}"
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO maintenance_windows (
                    window_id, title, description, scheduled_start, scheduled_end,
                    affected_layers, affected_components,
                    notify_before_minutes, requested_by
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING *
                """,
                window_id,
                title,
                description,
                start_time,
                end_time,
                [l.value for l in affected_layers],
                affected_components,
                notify_before_minutes,
                created_by
            )
            
            return MaintenanceWindow(
                window_id=row['window_id'],
                title=row['title'],
                description=row['description'],
                start_time=row['scheduled_start'],
                end_time=row['scheduled_end'],
                timezone=row['timezone'],
                affected_layers=[SystemLayer(l) for l in row['affected_layers']] if row['affected_layers'] else [],
                affected_components=row['affected_components'] or [],
                status=row['status'],
                notify_before_minutes=row['notify_before_minutes'] or [60, 15],
                notifications_sent=list(row['notifications_sent']) if row['notifications_sent'] else [],
                created_by=row['requested_by'],
                created_at=row['requested_at']
            )
    
    async def get_active_maintenance(self) -> List[MaintenanceWindow]:
        """Get currently active maintenance windows."""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM maintenance_windows
                WHERE status = 'in_progress'
                ORDER BY scheduled_start
                """
            )
            return [self._row_to_window(row) for row in rows]
    
    async def get_upcoming_maintenance(
        self,
        hours: int = 24
    ) -> List[MaintenanceWindow]:
        """Get upcoming maintenance windows."""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM maintenance_windows
                WHERE status = 'scheduled'
                  AND scheduled_start <= NOW() + $1::INTERVAL
                ORDER BY scheduled_start
                """,
                f"{hours} hours"
            )
            return [self._row_to_window(row) for row in rows]
    
    async def cancel_maintenance(self, window_id: str) -> bool:
        """Cancel a scheduled maintenance window."""
        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE maintenance_windows
                SET status = 'cancelled'
                WHERE window_id = $1 AND status = 'scheduled'
                """,
                window_id
            )
            return 'UPDATE 1' in result
    
    async def approve_maintenance(
        self,
        window_id: str,
        approved_by: str
    ) -> bool:
        """Approve a pending maintenance window."""
        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE maintenance_windows
                SET status = 'scheduled',
                    approved_by = $2,
                    approved_at = NOW()
                WHERE window_id = $1 AND status = 'pending_approval'
                """,
                window_id,
                approved_by
            )
            return 'UPDATE 1' in result
    
    async def get_maintenance_by_id(self, window_id: str) -> Optional[MaintenanceWindow]:
        """Get a maintenance window by ID."""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM maintenance_windows WHERE window_id = $1",
                window_id
            )
            if row:
                return self._row_to_window(row)
            return None
    
    def _row_to_window(self, row) -> MaintenanceWindow:
        """Convert database row to MaintenanceWindow model."""
        return MaintenanceWindow(
            window_id=row['window_id'],
            title=row['title'],
            description=row['description'],
            start_time=row['scheduled_start'],
            end_time=row['scheduled_end'],
            timezone=row['timezone'],
            affected_layers=[SystemLayer(l) for l in row['affected_layers']] if row['affected_layers'] else [],
            affected_components=row['affected_components'] or [],
            status=row['status'],
            notify_before_minutes=row['notify_before_minutes'] or [60, 15],
            notifications_sent=list(row['notifications_sent']) if row['notifications_sent'] else [],
            created_by=row['requested_by'],
            created_at=row['requested_at']
        )
