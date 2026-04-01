"""
Report Generator — Generate detailed pipeline run reports.

Creates comprehensive reports for:
    - Individual pipeline runs
    - Daily summaries
    - Weekly analytics

Example:
    from pipeline.monitoring import ReportGenerator
    
    generator = ReportGenerator(db_connection=conn)
    
    # Single run report
    run_report = generator.generate_run_report("run_2024_001")
    
    # Daily summary
    daily = generator.generate_daily_summary(date.today())
    
    # Weekly report
    weekly = generator.generate_weekly_report(week=42)
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional, Any
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class RunStatus(str, Enum):
    """Pipeline run status."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    RUNNING = "running"
    CANCELLED = "cancelled"


@dataclass
class StageStats:
    """Statistics for a single pipeline stage."""
    stage_name: str
    records_in: int = 0
    records_out: int = 0
    records_failed: int = 0
    duration_seconds: float = 0.0
    avg_latency_ms: float = 0.0
    errors: list[dict] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        total = self.records_in
        if total == 0:
            return 0.0
        return self.records_out / total
    
    def to_dict(self) -> dict:
        return {
            "stage_name": self.stage_name,
            "records_in": self.records_in,
            "records_out": self.records_out,
            "records_failed": self.records_failed,
            "duration_seconds": self.duration_seconds,
            "avg_latency_ms": self.avg_latency_ms,
            "success_rate": self.success_rate,
            "errors": self.errors[:10],  # Limit errors in report
        }


@dataclass
class RunReport:
    """Comprehensive pipeline run report."""
    run_id: str
    status: RunStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    
    # Overall stats
    total_records: int = 0
    processed_records: int = 0
    failed_records: int = 0
    duplicate_records: int = 0
    
    # Quality metrics
    validation_pass_rate: float = 0.0
    data_quality_score: float = 0.0
    
    # Stage breakdown
    stages: list[StageStats] = field(default_factory=list)
    
    # Anomalies and alerts
    anomalies_detected: int = 0
    alerts_triggered: list[str] = field(default_factory=list)
    
    # Metadata
    mode: str = "delta"  # delta, full, backfill
    epochs: list[int] = field(default_factory=list)
    version: str = "1.0.0"
    
    @property
    def success_rate(self) -> float:
        """Calculate overall success rate."""
        if self.total_records == 0:
            return 0.0
        return self.processed_records / self.total_records
    
    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "total_records": self.total_records,
            "processed_records": self.processed_records,
            "failed_records": self.failed_records,
            "duplicate_records": self.duplicate_records,
            "success_rate": self.success_rate,
            "validation_pass_rate": self.validation_pass_rate,
            "data_quality_score": self.data_quality_score,
            "stages": [s.to_dict() for s in self.stages],
            "anomalies_detected": self.anomalies_detected,
            "alerts_triggered": self.alerts_triggered,
            "mode": self.mode,
            "epochs": self.epochs,
            "version": self.version,
        }
    
    def to_markdown(self) -> str:
        """Generate markdown report."""
        md = f"""# Pipeline Run Report: {self.run_id}

## Summary

| Metric | Value |
|--------|-------|
| Status | {self.status.value.upper()} |
| Duration | {self.duration_seconds:.1f}s |
| Success Rate | {self.success_rate:.1%} |
| Data Quality | {self.data_quality_score:.1f}/100 |

## Records Processed

- **Total**: {self.total_records:,}
- **Successful**: {self.processed_records:,}
- **Failed**: {self.failed_records:,}
- **Duplicates**: {self.duplicate_records:,}

## Stage Breakdown

| Stage | In | Out | Failed | Duration | Success Rate |
|-------|-----|-----|--------|----------|--------------|
"""
        for stage in self.stages:
            md += f"| {stage.stage_name} | {stage.records_in:,} | {stage.records_out:,} | {stage.records_failed:,} | {stage.duration_seconds:.1f}s | {stage.success_rate:.1%} |\n"
        
        if self.alerts_triggered:
            md += f"\n## Alerts Triggered\n\n"
            for alert in self.alerts_triggered:
                md += f"- ⚠️ {alert}\n"
        
        if self.anomalies_detected > 0:
            md += f"\n## Anomalies\n\n{self.anomalies_detected} anomalies detected during this run.\n"
        
        return md


@dataclass
class DailySummary:
    """Daily pipeline summary."""
    date: date
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    
    total_records: int = 0
    new_records: int = 0
    updated_records: int = 0
    failed_records: int = 0
    
    avg_duration_seconds: float = 0.0
    avg_data_quality: float = 0.0
    
    errors: list[dict] = field(default_factory=list)
    top_issues: list[str] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate run success rate."""
        if self.total_runs == 0:
            return 0.0
        return self.successful_runs / self.total_runs
    
    def to_dict(self) -> dict:
        return {
            "date": self.date.isoformat(),
            "total_runs": self.total_runs,
            "successful_runs": self.successful_runs,
            "failed_runs": self.failed_runs,
            "success_rate": self.success_rate,
            "total_records": self.total_records,
            "new_records": self.new_records,
            "updated_records": self.updated_records,
            "failed_records": self.failed_records,
            "avg_duration_seconds": self.avg_duration_seconds,
            "avg_data_quality": self.avg_data_quality,
            "top_issues": self.top_issues,
        }


@dataclass
class WeeklyReport:
    """Weekly analytics report."""
    week: int
    year: int
    start_date: date
    end_date: date
    
    total_runs: int = 0
    total_records: int = 0
    
    daily_breakdown: list[dict] = field(default_factory=list)
    
    # Trends
    records_trend: str = "stable"  # up, down, stable
    quality_trend: str = "stable"
    error_rate_trend: str = "stable"
    
    # Highlights
    peak_day: Optional[date] = None
    peak_volume: int = 0
    
    issues_count: int = 0
    top_issues: list[dict] = field(default_factory=list)
    
    # Performance
    avg_records_per_run: float = 0.0
    avg_duration_seconds: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "week": self.week,
            "year": self.year,
            "period": f"{self.start_date.isoformat()} to {self.end_date.isoformat()}",
            "total_runs": self.total_runs,
            "total_records": self.total_records,
            "records_trend": self.records_trend,
            "quality_trend": self.quality_trend,
            "error_rate_trend": self.error_rate_trend,
            "avg_records_per_run": self.avg_records_per_run,
            "avg_duration_seconds": self.avg_duration_seconds,
            "issues_count": self.issues_count,
            "top_issues": self.top_issues,
        }


class ReportGenerator:
    """
    Generate detailed pipeline reports.
    
    Connects to database to fetch run data and generates
    comprehensive reports in multiple formats.
    """
    
    def __init__(
        self,
        db_connection: Optional[Any] = None,
        metrics_path: Optional[Path] = None,
    ) -> None:
        """
        Initialize report generator.
        
        Args:
            db_connection: Database connection for querying run data
            metrics_path: Path to stored metrics files
        """
        self._db = db_connection
        self._metrics_path = metrics_path or Path("data/metrics")
    
    def generate_run_report(self, run_id: str) -> Optional[RunReport]:
        """
        Generate comprehensive report for a single run.
        
        Args:
            run_id: Unique run identifier
            
        Returns:
            RunReport or None if run not found
        """
        # Try to fetch from database first
        if self._db:
            report = self._fetch_run_from_db(run_id)
            if report:
                return report
        
        # Fallback to file
        return self._fetch_run_from_file(run_id)
    
    def _fetch_run_from_db(self, run_id: str) -> Optional[RunReport]:
        """Fetch run data from database."""
        try:
            # This would query the pipeline_runs table
            # Placeholder implementation
            return None
        except Exception as e:
            logger.warning(f"Failed to fetch run from DB: {e}")
            return None
    
    def _fetch_run_from_file(self, run_id: str) -> Optional[RunReport]:
        """Fetch run data from metrics file."""
        run_file = self._metrics_path / f"run_{run_id}.json"
        if not run_file.exists():
            return None
        
        try:
            data = json.loads(run_file.read_text())
            return RunReport(
                run_id=run_id,
                status=RunStatus(data.get("status", "failed")),
                started_at=datetime.fromisoformat(data["started_at"]),
                completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
                duration_seconds=data.get("duration_seconds", 0),
                total_records=data.get("total_records", 0),
                processed_records=data.get("processed_records", 0),
                failed_records=data.get("failed_records", 0),
                duplicate_records=data.get("duplicate_records", 0),
                validation_pass_rate=data.get("validation_pass_rate", 0),
                data_quality_score=data.get("data_quality_score", 0),
                anomalies_detected=data.get("anomalies_detected", 0),
                alerts_triggered=data.get("alerts_triggered", []),
                mode=data.get("mode", "delta"),
                epochs=data.get("epochs", []),
            )
        except Exception as e:
            logger.error(f"Failed to parse run file: {e}")
            return None
    
    def generate_daily_summary(self, target_date: date) -> DailySummary:
        """
        Generate daily pipeline summary.
        
        Args:
            target_date: Date to summarize
            
        Returns:
            DailySummary
        """
        summary = DailySummary(date=target_date)
        
        if self._db:
            try:
                # Query database for daily stats
                # This is a placeholder - actual implementation would query
                # the pipeline_runs table
                pass
            except Exception as e:
                logger.warning(f"Failed to fetch daily summary from DB: {e}")
        
        # Fallback: aggregate from files
        run_files = list(self._metrics_path.glob("run_*.json"))
        
        runs_today = []
        for f in run_files:
            try:
                data = json.loads(f.read_text())
                started = datetime.fromisoformat(data["started_at"])
                if started.date() == target_date:
                    runs_today.append(data)
            except Exception:
                continue
        
        # Aggregate stats
        summary.total_runs = len(runs_today)
        summary.successful_runs = sum(1 for r in runs_today if r.get("status") == "success")
        summary.failed_runs = summary.total_runs - summary.successful_runs
        
        for run in runs_today:
            summary.total_records += run.get("total_records", 0)
            summary.failed_records += run.get("failed_records", 0)
        
        if runs_today:
            summary.avg_duration_seconds = sum(
                r.get("duration_seconds", 0) for r in runs_today
            ) / len(runs_today)
            summary.avg_data_quality = sum(
                r.get("data_quality_score", 0) for r in runs_today
            ) / len(runs_today)
        
        return summary
    
    def generate_weekly_report(self, week: int, year: Optional[int] = None) -> WeeklyReport:
        """
        Generate weekly analytics report.
        
        Args:
            week: ISO week number
            year: Year (defaults to current year)
            
        Returns:
            WeeklyReport
        """
        year = year or date.today().year
        
        # Calculate week dates
        start_date = datetime.strptime(f"{year}-W{week:02d}-1", "%Y-W%W-%w").date()
        end_date = start_date + timedelta(days=6)
        
        report = WeeklyReport(
            week=week,
            year=year,
            start_date=start_date,
            end_date=end_date,
        )
        
        # Generate daily summaries for the week
        daily_summaries = []
        for i in range(7):
            day = start_date + timedelta(days=i)
            daily = self.generate_daily_summary(day)
            daily_summaries.append(daily)
            
            report.total_runs += daily.total_runs
            report.total_records += daily.total_records
        
        report.daily_breakdown = [d.to_dict() for d in daily_summaries]
        
        # Calculate averages
        if report.total_runs > 0:
            report.avg_records_per_run = report.total_records / report.total_runs
            report.avg_duration_seconds = sum(
                d.avg_duration_seconds for d in daily_summaries
            ) / 7
        
        # Find peak day
        peak = max(daily_summaries, key=lambda d: d.total_records, default=None)
        if peak:
            report.peak_day = peak.date
            report.peak_volume = peak.total_records
        
        # Determine trends (compare to previous week)
        prev_week_start = start_date - timedelta(days=7)
        prev_week_end = end_date - timedelta(days=7)
        prev_volume = self._get_volume_for_period(prev_week_start, prev_week_end)
        
        if prev_volume > 0:
            volume_change = (report.total_records - prev_volume) / prev_volume
            if volume_change > 0.1:
                report.records_trend = "up"
            elif volume_change < -0.1:
                report.records_trend = "down"
        
        return report
    
    def _get_volume_for_period(self, start: date, end: date) -> int:
        """Get total record volume for a date period."""
        total = 0
        
        run_files = list(self._metrics_path.glob("run_*.json"))
        for f in run_files:
            try:
                data = json.loads(f.read_text())
                started = datetime.fromisoformat(data["started_at"]).date()
                if start <= started <= end:
                    total += data.get("total_records", 0)
            except Exception:
                continue
        
        return total
    
    def export_report(
        self,
        report: RunReport | DailySummary | WeeklyReport,
        path: Path,
        format: str = "json",
    ) -> None:
        """
        Export report to file.
        
        Args:
            report: Report to export
            path: Output file path
            format: Output format (json, markdown)
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "json":
            with open(path, "w") as f:
                json.dump(report.to_dict(), f, indent=2, default=str)
        elif format == "markdown":
            if hasattr(report, "to_markdown"):
                with open(path, "w") as f:
                    f.write(report.to_markdown())
            else:
                raise ValueError("Report does not support markdown export")
        else:
            raise ValueError(f"Unknown format: {format}")
        
        logger.info(f"Exported report to {path}")
