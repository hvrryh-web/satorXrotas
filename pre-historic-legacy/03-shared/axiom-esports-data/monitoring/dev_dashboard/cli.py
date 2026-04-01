"""
Developer Dashboard CLI
Command-line interface for managing maintenance windows and alerts.
"""

import asyncio
import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from typing import List, Optional

import asyncpg
from tabulate import tabulate

from .models import SystemLayer, Severity, MaintenanceWindow, AlertRule
from .scheduler import MaintenanceScheduler
from .alerts import AlertManager

# Database connection
async def get_db_pool():
    """Get database connection pool."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        # Try to construct from individual env vars
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '5432')
        user = os.getenv('DB_USER', 'axiom')
        password = os.getenv('DB_PASSWORD', 'axiom')
        database = os.getenv('DB_NAME', 'axiom_esports')
        database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    return await asyncpg.create_pool(database_url)


# Maintenance Commands
async def list_maintenance(args):
    """List maintenance windows."""
    pool = await get_db_pool()
    scheduler = MaintenanceScheduler(pool)
    
    if args.status == 'active':
        windows = await scheduler.get_active_maintenance()
    elif args.status == 'upcoming':
        windows = await scheduler.get_upcoming_maintenance(hours=args.hours)
    else:
        # Get all
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM maintenance_windows
                ORDER BY scheduled_start DESC
                LIMIT $1
                """,
                args.limit
            )
            windows = [scheduler._row_to_window(row) for row in rows]
    
    if not windows:
        print("No maintenance windows found.")
        return
    
    data = []
    for w in windows:
        data.append([
            w.window_id,
            w.title[:40],
            w.status,
            w.start_time.strftime('%Y-%m-%d %H:%M'),
            w.end_time.strftime('%Y-%m-%d %H:%M'),
            ', '.join(l.value for l in w.affected_layers) if w.affected_layers else '-'
        ])
    
    headers = ['ID', 'Title', 'Status', 'Start', 'End', 'Layers']
    print(tabulate(data, headers=headers, tablefmt='grid'))
    await pool.close()


async def schedule_maintenance(args):
    """Schedule a new maintenance window."""
    pool = await get_db_pool()
    scheduler = MaintenanceScheduler(pool)
    
    # Parse layers
    layers = [SystemLayer(l.strip()) for l in args.layers.split(',')]
    
    # Parse times
    start_time = datetime.fromisoformat(args.start)
    end_time = datetime.fromisoformat(args.end)
    
    # Parse components
    components = [c.strip() for c in args.components.split(',')] if args.components else []
    
    window = await scheduler.schedule_maintenance(
        title=args.title,
        description=args.description,
        start_time=start_time,
        end_time=end_time,
        affected_layers=layers,
        affected_components=components,
        created_by=args.user,
        notify_before_minutes=args.notify
    )
    
    print(f"✓ Maintenance window scheduled: {window.window_id}")
    print(f"  Title: {window.title}")
    print(f"  Start: {window.start_time}")
    print(f"  End: {window.end_time}")
    print(f"  Layers: {', '.join(l.value for l in window.affected_layers)}")
    
    await pool.close()


async def cancel_maintenance(args):
    """Cancel a maintenance window."""
    pool = await get_db_pool()
    scheduler = MaintenanceScheduler(pool)
    
    success = await scheduler.cancel_maintenance(args.window_id)
    if success:
        print(f"✓ Maintenance window {args.window_id} cancelled.")
    else:
        print(f"✗ Could not cancel window {args.window_id}. It may not exist or is already in progress.")
    
    await pool.close()


async def show_maintenance(args):
    """Show detailed maintenance window information."""
    pool = await get_db_pool()
    scheduler = MaintenanceScheduler(pool)
    
    window = await scheduler.get_maintenance_by_id(args.window_id)
    if not window:
        print(f"Maintenance window {args.window_id} not found.")
        return
    
    print(f"\n{'='*60}")
    print(f"Maintenance Window: {window.window_id}")
    print(f"{'='*60}")
    print(f"Title:       {window.title}")
    print(f"Status:      {window.status}")
    print(f"Description: {window.description or 'N/A'}")
    print(f"\nTiming:")
    print(f"  Start:     {window.start_time}")
    print(f"  End:       {window.end_time}")
    print(f"  Timezone:  {window.timezone}")
    print(f"\nAffected:")
    print(f"  Layers:    {', '.join(l.value for l in window.affected_layers) or 'None'}")
    print(f"  Components: {', '.join(window.affected_components) or 'None'}")
    print(f"\nNotifications:")
    print(f"  Before:    {window.notify_before_minutes} minutes")
    print(f"  Sent:      {len(window.notifications_sent)} notifications")
    print(f"\nCreated by: {window.created_by} at {window.created_at}")
    print(f"{'='*60}\n")
    
    await pool.close()


# Alert Commands
async def list_alerts(args):
    """List active alerts."""
    pool = await get_db_pool()
    manager = AlertManager(pool)
    await manager._load_active_alerts()
    
    alerts = manager.get_active_alerts(
        severity=Severity(args.severity) if args.severity else None
    )
    
    if not alerts:
        print("No active alerts.")
        return
    
    data = []
    for a in alerts:
        data.append([
            a.alert_id[:30],
            a.component_id[:25],
            a.severity.value,
            a.message[:50],
            a.triggered_at.strftime('%Y-%m-%d %H:%M')
        ])
    
    headers = ['Alert ID', 'Component', 'Severity', 'Message', 'Triggered']
    print(tabulate(data, headers=headers, tablefmt='grid'))
    await pool.close()


async def acknowledge_alert(args):
    """Acknowledge an alert."""
    pool = await get_db_pool()
    manager = AlertManager(pool)
    await manager._load_active_alerts()
    
    success = await manager.acknowledge_alert(args.alert_id, args.user)
    if success:
        print(f"✓ Alert {args.alert_id} acknowledged.")
    else:
        print(f"✗ Alert {args.alert_id} not found or already resolved.")
    
    await pool.close()


async def resolve_alert(args):
    """Manually resolve an alert."""
    pool = await get_db_pool()
    manager = AlertManager(pool)
    await manager._load_active_alerts()
    
    success = await manager.resolve_alert(args.alert_id, args.note or "Manually resolved")
    if success:
        print(f"✓ Alert {args.alert_id} resolved.")
    else:
        print(f"✗ Alert {args.alert_id} not found or already resolved.")
    
    await pool.close()


async def list_rules(args):
    """List alert rules."""
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        query = "SELECT * FROM alert_rules"
        params = []
        
        if args.enabled:
            query += " WHERE enabled = TRUE"
        elif args.disabled:
            query += " WHERE enabled = FALSE"
        
        query += " ORDER BY name"
        
        rows = await conn.fetch(query, *params)
    
    if not rows:
        print("No alert rules found.")
        return
    
    data = []
    for r in rows:
        data.append([
            r['rule_id'][:25],
            r['name'][:35],
            '✓' if r['enabled'] else '✗',
            r['condition_type'],
            r['severity'],
            ', '.join(r['notify_channels']) if r['notify_channels'] else '-'
        ])
    
    headers = ['Rule ID', 'Name', 'Enabled', 'Condition', 'Severity', 'Channels']
    print(tabulate(data, headers=headers, tablefmt='grid'))
    await pool.close()


async def create_rule(args):
    """Create a new alert rule."""
    pool = await get_db_pool()
    manager = AlertManager(pool)
    
    import uuid
    rule = AlertRule(
        rule_id=f"rule-{uuid.uuid4().hex[:8]}",
        name=args.name,
        component_id=args.component,
        layer=SystemLayer(args.layer) if args.layer else None,
        check_type=None,
        condition=args.condition,
        threshold=args.threshold,
        consecutive_count=args.consecutive,
        severity=Severity(args.severity),
        channels=args.channels.split(',') if args.channels else ['email'],
        recipients=args.recipients.split(',') if args.recipients else [],
        cooldown_minutes=args.cooldown
    )
    
    created = await manager.create_alert_rule(rule)
    print(f"✓ Alert rule created: {created.rule_id}")
    print(f"  Name: {created.name}")
    print(f"  Condition: {created.condition}")
    print(f"  Severity: {created.severity.value}")
    
    await pool.close()


async def delete_rule(args):
    """Delete an alert rule."""
    pool = await get_db_pool()
    manager = AlertManager(pool)
    
    success = await manager.delete_alert_rule(args.rule_id)
    if success:
        print(f"✓ Alert rule {args.rule_id} deleted.")
    else:
        print(f"✗ Alert rule {args.rule_id} not found.")
    
    await pool.close()


async def toggle_rule(args):
    """Enable or disable an alert rule."""
    pool = await get_db_pool()
    manager = AlertManager(pool)
    
    if args.enable:
        success = await manager.enable_alert_rule(args.rule_id)
        action = "enabled"
    else:
        success = await manager.disable_alert_rule(args.rule_id)
        action = "disabled"
    
    if success:
        print(f"✓ Alert rule {args.rule_id} {action}.")
    else:
        print(f"✗ Alert rule {args.rule_id} not found.")
    
    await pool.close()


# Dashboard Commands
async def dashboard_summary(args):
    """Show dashboard summary."""
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        # Get summary
        summary = await conn.fetchrow("SELECT * FROM get_dashboard_summary()")
        
        # Get active alerts count
        alerts_count = await conn.fetchval(
            "SELECT COUNT(*) FROM active_alerts WHERE resolved_at IS NULL"
        )
        
        # Get active maintenance count
        maintenance_count = await conn.fetchval(
            "SELECT COUNT(*) FROM maintenance_windows WHERE status = 'in_progress'"
        )
        
        # Get upcoming maintenance
        upcoming = await conn.fetch(
            """
            SELECT window_id, title, scheduled_start 
            FROM maintenance_windows 
            WHERE status = 'scheduled' 
            ORDER BY scheduled_start 
            LIMIT 3
            """
        )
    
    print(f"\n{'='*60}")
    print("Developer Dashboard Summary")
    print(f"{'='*60}")
    print(f"\nOverall Status: {summary['overall_status'].upper()}")
    print(f"\nComponents:")
    print(f"  Total:     {summary['total_components']}")
    print(f"  Healthy:   {summary['healthy_count']} ✓")
    print(f"  Degraded:  {summary['degraded_count']} ⚠" if summary['degraded_count'] else "")
    print(f"  Critical:  {summary['critical_count']} ✗" if summary['critical_count'] else "")
    print(f"  Unknown:   {summary['unknown_count']} ?" if summary['unknown_count'] else "")
    print(f"\nActive Issues:")
    print(f"  Alerts:       {alerts_count}")
    print(f"  Maintenance:  {maintenance_count}")
    
    if upcoming:
        print(f"\nUpcoming Maintenance:")
        for m in upcoming:
            print(f"  - {m['title'][:40]} ({m['scheduled_start'].strftime('%Y-%m-%d %H:%M')})")
    
    print(f"{'='*60}\n")
    await pool.close()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Developer Dashboard CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Schedule maintenance
  %(prog)s maintenance schedule --title "DB Upgrade" --start "2026-03-10T02:00:00" --end "2026-03-10T04:00:00" --layers infrastructure --user admin

  # List active alerts
  %(prog)s alerts list

  # Acknowledge an alert
  %(prog)s alerts ack ALERT-123 --user john

  # Create alert rule
  %(prog)s rules create --name "High CPU" --condition threshold_exceeded --threshold 80 --severity critical --channels slack,email
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Maintenance commands
    maint_parser = subparsers.add_parser('maintenance', help='Maintenance window management')
    maint_subparsers = maint_parser.add_subparsers(dest='maint_command')
    
    # List maintenance
    list_maint = maint_subparsers.add_parser('list', help='List maintenance windows')
    list_maint.add_argument('--status', choices=['all', 'active', 'upcoming'], default='all')
    list_maint.add_argument('--hours', type=int, default=24, help='Hours ahead for upcoming')
    list_maint.add_argument('--limit', type=int, default=20)
    list_maint.set_defaults(func=list_maintenance)
    
    # Schedule maintenance
    schedule_maint = maint_subparsers.add_parser('schedule', help='Schedule new maintenance')
    schedule_maint.add_argument('--title', required=True, help='Maintenance title')
    schedule_maint.add_argument('--description', help='Description')
    schedule_maint.add_argument('--start', required=True, help='Start time (ISO format)')
    schedule_maint.add_argument('--end', required=True, help='End time (ISO format)')
    schedule_maint.add_argument('--layers', required=True, help='Comma-separated layers')
    schedule_maint.add_argument('--components', help='Comma-separated component IDs')
    schedule_maint.add_argument('--user', required=True, help='User scheduling')
    schedule_maint.add_argument('--notify', type=int, nargs='+', default=[60, 15], 
                                 help='Notification minutes before')
    schedule_maint.set_defaults(func=schedule_maintenance)
    
    # Cancel maintenance
    cancel_maint = maint_subparsers.add_parser('cancel', help='Cancel maintenance')
    cancel_maint.add_argument('window_id', help='Window ID to cancel')
    cancel_maint.set_defaults(func=cancel_maintenance)
    
    # Show maintenance details
    show_maint = maint_subparsers.add_parser('show', help='Show maintenance details')
    show_maint.add_argument('window_id', help='Window ID')
    show_maint.set_defaults(func=show_maintenance)
    
    # Alert commands
    alert_parser = subparsers.add_parser('alerts', help='Alert management')
    alert_subparsers = alert_parser.add_subparsers(dest='alert_command')
    
    # List alerts
    list_alert = alert_subparsers.add_parser('list', help='List active alerts')
    list_alert.add_argument('--severity', choices=['critical', 'high', 'medium', 'low', 'info'])
    list_alert.set_defaults(func=list_alerts)
    
    # Acknowledge alert
    ack_alert = alert_subparsers.add_parser('ack', help='Acknowledge alert')
    ack_alert.add_argument('alert_id', help='Alert ID')
    ack_alert.add_argument('--user', required=True, help='User acknowledging')
    ack_alert.set_defaults(func=acknowledge_alert)
    
    # Resolve alert
    res_alert = alert_subparsers.add_parser('resolve', help='Resolve alert')
    res_alert.add_argument('alert_id', help='Alert ID')
    res_alert.add_argument('--note', help='Resolution note')
    res_alert.set_defaults(func=resolve_alert)
    
    # Rule commands
    rule_parser = subparsers.add_parser('rules', help='Alert rule management')
    rule_subparsers = rule_parser.add_subparsers(dest='rule_command')
    
    # List rules
    list_rule = rule_subparsers.add_parser('list', help='List alert rules')
    list_rule.add_argument('--enabled', action='store_true', help='Show only enabled')
    list_rule.add_argument('--disabled', action='store_true', help='Show only disabled')
    list_rule.set_defaults(func=list_rules)
    
    # Create rule
    create_rule_cmd = rule_subparsers.add_parser('create', help='Create alert rule')
    create_rule_cmd.add_argument('--name', required=True, help='Rule name')
    create_rule_cmd.add_argument('--component', help='Component ID')
    create_rule_cmd.add_argument('--layer', choices=[l.value for l in SystemLayer], help='System layer')
    create_rule_cmd.add_argument('--condition', required=True, 
                                  choices=['status_change', 'threshold_exceeded', 'consecutive_failures'],
                                  help='Trigger condition')
    create_rule_cmd.add_argument('--threshold', type=float, help='Threshold value')
    create_rule_cmd.add_argument('--consecutive', type=int, default=1, help='Consecutive failures')
    create_rule_cmd.add_argument('--severity', required=True, 
                                  choices=['critical', 'high', 'medium', 'low', 'info'],
                                  help='Alert severity')
    create_rule_cmd.add_argument('--channels', help='Comma-separated channels (slack,email,pagerduty,webhook)')
    create_rule_cmd.add_argument('--recipients', help='Comma-separated recipients')
    create_rule_cmd.add_argument('--cooldown', type=int, default=15, help='Cooldown minutes')
    create_rule_cmd.set_defaults(func=create_rule)
    
    # Delete rule
    del_rule = rule_subparsers.add_parser('delete', help='Delete alert rule')
    del_rule.add_argument('rule_id', help='Rule ID')
    del_rule.set_defaults(func=delete_rule)
    
    # Toggle rule
    toggle_rule_cmd = rule_subparsers.add_parser('toggle', help='Enable/disable rule')
    toggle_rule_cmd.add_argument('rule_id', help='Rule ID')
    toggle_rule_cmd.add_argument('--enable', action='store_true', help='Enable rule')
    toggle_rule_cmd.add_argument('--disable', action='store_true', help='Disable rule')
    toggle_rule_cmd.set_defaults(func=toggle_rule)
    
    # Dashboard commands
    dash_parser = subparsers.add_parser('dashboard', help='Dashboard operations')
    dash_subparsers = dash_parser.add_subparsers(dest='dash_command')
    
    # Summary
    summary_cmd = dash_subparsers.add_parser('summary', help='Show dashboard summary')
    summary_cmd.set_defaults(func=dashboard_summary)
    
    # Parse args
    args = parser.parse_args()
    
    if not hasattr(args, 'func'):
        parser.print_help()
        sys.exit(1)
    
    # Run async function
    asyncio.run(args.func(args))


if __name__ == '__main__':
    main()
