"""Staff models for BubbleTea shop.

This module defines data structures for representing employees, shifts,
and staff management with kawaii-inspired scheduling.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import List, Optional


class StaffRole(Enum):
    """Staff roles with kawaii personality indicators.
    
    Each role includes visual hints for TUI rendering.
    """
    OWNER = "owner"
    MANAGER = "manager"
    HEAD_BARISTA = "head_barista"
    BARISTA = "barista"
    TRAINEE = "trainee"
    CASHIER = "cashier"
    CLEANER = "cleaner"
    
    @property
    def kawaii_icon(self) -> str:
        """Kawaii emoji for this role.
        
        Returns:
            Emoji representing the role and its responsibilities
        """
        icons = {
            self.OWNER: "👑",
            self.MANAGER: "📊",
            self.HEAD_BARISTA: "🧋",
            self.BARISTA: "🥤",
            self.TRAINEE: "📚",
            self.CASHIER: "💰",
            self.CLEANER: "🧼"
        }
        return icons.get(self, "👤")
    
    @property
    def responsibility_level(self) -> int:
        """Responsibility level (1=lowest, 5=highest).
        
        Returns:
            Responsibility rating from 1 to 5
        """
        levels = {
            self.OWNER: 5,
            self.MANAGER: 5,
            self.HEAD_BARISTA: 4,
            self.BARISTA: 3,
            self.TRAINEE: 1,
            self.CASHIER: 2,
            self.CLEANER: 2
        }
        return levels.get(self, 1)
    
    @property
    def color_hint(self) -> str:
        """Color hint for TUI styling based on role importance.
        
        Returns:
            Color name or hex for terminal styling
        """
        colors = {
            self.OWNER: "#FFD700",
            self.MANAGER: "#FF69B4",
            self.HEAD_BARISTA: "#32CD32",
            self.BARISTA: "#87CEEB",
            self.TRAINEE: "#DDA0DD",
            self.CASHIER: "#F0E68C",
            self.CLEANER: "#98FB98"
        }
        return colors.get(self, "#FFFFFF")


@dataclass
class Employee:
    """Individual employee with kawaii personality traits.
    
    Attributes:
        id: Unique employee identifier
        name: Employee's full name
        role: Employee's role in the organization
        hire_date: Unix timestamp when employee was hired
        hourly_wage: Hourly wage in cents
        is_part_time: Whether employee works part-time
        phone_number: Employee phone number
        email: Employee email address
        emergency_contact: Emergency contact information
        skills: List of employee skills
        languages: Languages employee can speak
        availability: Days and hours employee is available
        performance_score: Performance rating (1-10)
        certifications: List of certifications
        allergies: Employee allergies or restrictions
        preferred_schedule: Preferred working hours
        last_training_date: Date of last training session
        notes: Additional notes about the employee
        is_active: Whether employee is currently active
        kawaii_mood: Current mood indicator
        timestamp: Last updated timestamp
    """
    
    id: str
    name: str
    role: StaffRole
    hire_date: float
    hourly_wage: int  # in cents
    is_part_time: bool = True
    phone_number: str = ""
    email: str = ""
    emergency_contact: str = ""
    skills: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    availability: dict = field(default_factory=dict)  # {day: [start_time, end_time]}
    performance_score: int = 5
    certifications: List[str] = field(default_factory=list)
    allergies: List[str] = field(default_factory=list)
    preferred_schedule: str = ""
    last_training_date: Optional[float] = None
    notes: str = ""
    is_active: bool = True
    kawaii_mood: str = "😊"
    timestamp: float = field(default_factory=time.time)
    
    def __post_init__(self):
        """Update kawaii mood based on role and performance."""
        self._update_kawaii_mood()
    
    def _update_kawaii_mood(self):
        """Update kawaii mood based on role and performance."""
        if self.performance_score >= 8:
            self.kawaii_mood = "😍"  # Excellent performance
        elif self.performance_score >= 6:
            self.kawaii_mood = "😊"  # Good performance
        elif self.performance_score >= 4:
            self.kawaii_mood = "😐"  # Average performance
        else:
            self.kawaii_mood = "😔"  # Needs improvement
    
    @property
    def role_emoji(self) -> str:
        """Emoji representation of employee's role.
        
        Returns:
            Emoji for the employee's role
        """
        return self.role.kawaii_icon
    
    @property
    def tenure_months(self) -> int:
        """Employee tenure in months.
        
        Returns:
            Number of months since hire date
        """
        months = (time.time() - self.hire_date) / (30 * 24 * 60 * 60)
        return int(months)
    
    @property
    def is_senior_employee(self) -> bool:
        """Whether employee is considered senior (6+ months).
        
        Returns:
            True if employee has been with company 6+ months
        """
        return self.tenure_months >= 6
    
    @property
    def formatted_hourly_wage(self) -> str:
        """Formatted hourly wage for display.
        
        Returns:
            Wage formatted as currency string
        """
        return f"${self.hourly_wage / 100:.2f}/hr"
    
    @property
    def estimated_monthly_earnings(self) -> int:
        """Estimated monthly earnings based on availability.
        
        Returns:
            Estimated monthly earnings in cents
        """
        # Simple estimation: assume 20 hours/week for part-time, 40 for full-time
        hours_per_week = 20 if self.is_part_time else 40
        hours_per_month = hours_per_week * 4.33  # Average weeks per month
        
        return int(hours_per_month * self.hourly_wage)
    
    @property
    def kawaii_profile(self) -> str:
        """Kawaii profile summary for TUI.
        
        Returns:
            String with emoji, name, role, and mood
        """
        return f"{self.role_emoji} {self.name} - {self.role.value.title()} {self.kawaii_mood}"
    
    @property
    def needs_training(self) -> bool:
        """Whether employee needs refresher training.
        
        Returns:
            True if last training was more than 3 months ago
        """
        if self.last_training_date is None:
            return True
        
        months_since_training = (time.time() - self.last_training_date) / (30 * 24 * 60 * 60)
        return months_since_training > 3
    
    def is_available_on_day(self, day_name: str) -> bool:
        """Check if employee is available on a specific day.
        
        Args:
            day_name: Day of week (e.g., "monday")
            
        Returns:
            True if employee is available on that day
        """
        return day_name.lower() in self.availability
    
    def get_availability_hours(self, day_name: str) -> List[str]:
        """Get availability hours for a specific day.
        
        Args:
            day_name: Day of week (e.g., "monday")
            
        Returns:
            List of available time slots
        """
        if day_name.lower() in self.availability:
            return self.availability[day_name.lower()]
        return []
    
    def add_skill(self, skill: str):
        """Add a skill to the employee's skill list.
        
        Args:
            skill: Skill to add
        """
        if skill not in self.skills:
            self.skills.append(skill)
            self.timestamp = time.time()
    
    def remove_skill(self, skill: str):
        """Remove a skill from the employee's skill list.
        
        Args:
            skill: Skill to remove
        """
        if skill in self.skills:
            self.skills.remove(skill)
            self.timestamp = time.time()
    
    def update_performance_score(self, new_score: int):
        """Update performance score and mood.
        
        Args:
            new_score: New performance score (1-10)
        """
        self.performance_score = max(1, min(10, new_score))
        self._update_kawaii_mood()
        self.timestamp = time.time()
    
    def to_json(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        data = asdict(self)
        data["role"] = self.role.value
        return data
    
    @classmethod
    def from_json(cls, data: dict) -> Employee:
        """Create instance from JSON-serializable dictionary."""
        data["role"] = StaffRole(data["role"])
        return cls(**data)


@dataclass
class Shift:
    """Work shift with kawaii scheduling information.
    
    Attributes:
        id: Unique shift identifier
        employee_id: ID of assigned employee
        employee_name: Name of assigned employee
        start_time: Unix timestamp when shift starts
        end_time: Unix timestamp when shift ends
        role_during_shift: Role employee will perform during this shift
        break_minutes: Planned break duration in minutes
        actual_break_minutes: Actual break duration in minutes
        station_assignment: Work station assignment (bar, cash, etc.)
        responsibilities: List of shift responsibilities
        scheduled_hours: Scheduled hours (calculated)
        actual_hours: Actual hours worked
        status: Shift status (scheduled, in_progress, completed, no_show)
        notes: Notes about the shift
        overtime_hours: Overtime hours worked
        is_cover_shift: Whether this is a coverage shift
        filled_by: Employee ID if this was a filled shift
        kawaii_status: Visual status indicator
        timestamp: Last updated timestamp
    """
    
    id: str
    employee_id: str
    employee_name: str
    start_time: float
    end_time: float
    role_during_shift: StaffRole = StaffRole.BARISTA
    break_minutes: int = 30
    actual_break_minutes: int = 0
    station_assignment: str = "bar"
    responsibilities: List[str] = field(default_factory=list)
    scheduled_hours: float = field(init=False)
    actual_hours: float = 0.0
    status: str = "scheduled"  # scheduled, in_progress, completed, no_show
    notes: str = ""
    overtime_hours: float = 0.0
    is_cover_shift: bool = False
    filled_by: Optional[str] = None
    kawaii_status: str = "📅"
    timestamp: float = field(default_factory=time.time)
    
    def __post_init__(self):
        """Calculate scheduled hours after initialization."""
        self.scheduled_hours = (self.end_time - self.start_time) / (60 * 60)
        self._update_kawaii_status()
    
    def _update_kawaii_status(self):
        """Update kawaii status based on current time and status."""
        now = time.time()
        
        if self.status == "completed":
            self.kawaii_status = "✅"
        elif self.status == "in_progress":
            if now > self.end_time:
                self.kawaii_status = "⏰"  # Overtime
            else:
                self.kawaii_status = "🧋"  # Working
        elif self.status == "no_show":
            self.kawaii_status = "❌"
        elif now < self.start_time:
            self.kawaii_status = "📅"  # Scheduled
        elif self.start_time <= now <= self.end_time:
            self.kawaii_status = "🕐"  # Should be starting
        else:
            self.kawaii_status = "⏰"  # Missed
    
    @property
    def is_current_shift(self) -> bool:
        """Whether this is the current shift (now between start and end).
        
        Returns:
            True if current time is within shift hours
        """
        now = time.time()
        return self.start_time <= now <= self.end_time
    
    @property
    def is_upcoming(self) -> bool:
        """Whether this shift is in the future.
        
        Returns:
            True if shift start time is in the future
        """
        return time.time() < self.start_time
    
    @property
    def is_past(self) -> bool:
        """Whether this shift has ended.
        
        Returns:
            True if shift end time has passed
        """
        return time.time() > self.end_time
    
    @property
    def duration_hours(self) -> float:
        """Shift duration in hours.
        
        Returns:
            Number of hours the shift is scheduled for
        """
        return self.scheduled_hours
    
    @property
    def break_time_percentage(self) -> float:
        """Break time as percentage of shift duration.
        
        Returns:
            Percentage of shift allocated for breaks
        """
        if self.scheduled_hours <= 0:
            return 0.0
        return (self.break_minutes / 60) / self.scheduled_hours * 100
    
    @property
    def expected_end_time(self) -> float:
        """Expected shift end time including breaks.
        
        Returns:
            Unix timestamp of expected end time
        """
        break_duration = self.break_minutes * 60  # Convert to seconds
        return self.end_time + break_duration
    
    @property
    def kawaii_time_display(self) -> str:
        """Kawaii time display for TUI.
        
        Returns:
            String with emoji and time information
        """
        from datetime import datetime
        start = datetime.fromtimestamp(self.start_time)
        end = datetime.fromtimestamp(self.end_time)
        return f"{self.kawaii_status} {start.strftime('%H:%M')}-{end.strftime('%H:%M')} ({self.duration_hours:.1f}h)"
    
    def start_shift(self, timestamp: Optional[float] = None):
        """Mark shift as started.
        
        Args:
            timestamp: Timestamp for shift start (defaults to now)
        """
        self.status = "in_progress"
        self.timestamp = timestamp or time.time()
        self._update_kawaii_status()
    
    def complete_shift(self, actual_end_time: Optional[float] = None, 
                      actual_break: Optional[int] = None):
        """Mark shift as completed.
        
        Args:
            actual_end_time: Actual end time (defaults to scheduled end)
            actual_break: Actual break duration in minutes
        """
        self.status = "completed"
        if actual_end_time:
            self.actual_hours = (actual_end_time - self.start_time) / (60 * 60)
        else:
            self.actual_hours = self.scheduled_hours
        
        if actual_break is not None:
            self.actual_break_minutes = actual_break
        
        # Calculate overtime
        self.overtime_hours = max(0.0, self.actual_hours - self.scheduled_hours)
        
        self.timestamp = time.time()
        self._update_kawaii_status()
    
    def mark_no_show(self, timestamp: Optional[float] = None):
        """Mark shift as no-show.
        
        Args:
            timestamp: Timestamp for no-show (defaults to now)
        """
        self.status = "no_show"
        self.timestamp = timestamp or time.time()
        self._update_kawaii_status()
    
    def assign_station(self, station: str):
        """Assign employee to a work station.
        
        Args:
            station: Station name (bar, cash, cleaning, etc.)
        """
        self.station_assignment = station
        self.timestamp = time.time()
    
    def add_responsibility(self, responsibility: str):
        """Add a responsibility to the shift.
        
        Args:
            responsibility: Responsibility to add
        """
        if responsibility not in self.responsibilities:
            self.responsibilities.append(responsibility)
            self.timestamp = time.time()
    
    def to_json(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        data = asdict(self)
        data["role_during_shift"] = self.role_during_shift.value
        return data
    
    @classmethod
    def from_json(cls, data: dict) -> Shift:
        """Create instance from JSON-serializable dictionary."""
        data["role_during_shift"] = StaffRole(data["role_during_shift"])
        return cls(**data)


@dataclass
class StaffMetrics:
    """Aggregated staff metrics with kawaii insights.
    
    Attributes:
        total_employees: Total number of employees
        active_employees: Number of currently active employees
        roles_distribution: Count of employees by role
        average_performance: Average performance score
        shifts_today: Number of shifts scheduled for today
        shifts_completed_today: Number of shifts completed today
        no_show_rate: Percentage of no-show shifts
        overtime_hours_today: Total overtime hours today
        coverage_needed: Number of shifts needing coverage
        top_performers: List of top performing employees
        training_needed: List of employees needing training
        staffing_forecast: Upcoming staffing needs
        kawaii_summary: Overall staff health summary
        timestamp: When metrics were collected
    """
    
    total_employees: int
    active_employees: int
    roles_distribution: dict[str, int]
    average_performance: float
    shifts_today: int
    shifts_completed_today: int
    no_show_rate: float
    overtime_hours_today: float
    coverage_needed: int
    top_performers: List[Employee] = field(default_factory=list)
    training_needed: List[Employee] = field(default_factory=list)
    staffing_forecast: dict[str, int] = field(default_factory=dict)  # date -> needed_count
    kawaii_summary: str = "👥"
    timestamp: float = field(default_factory=time.time)
    
    @property
    def completion_rate(self) -> float:
        """Shift completion rate as percentage.
        
        Returns:
            Percentage of completed shifts today
        """
        if self.shifts_today == 0:
            return 100.0
        return (self.shifts_completed_today / self.shifts_today) * 100
    
    @property
    def staffing_efficiency(self) -> int:
        """Overall staffing efficiency score (0-100).
        
        Returns:
            Efficiency score based on completion rate and no-show rate
        """
        efficiency = self.completion_rate
        efficiency -= self.no_show_rate * 2  # Penalty for no-shows
        return max(0, min(100, int(efficiency)))
    
    @property
    def kawaii_health_status(self) -> str:
        """Kawaii health status for TUI.
        
        Returns:
            Summary with emoji and key metrics
        """
        if self.staffing_efficiency >= 90:
            emoji = "😍"
        elif self.staffing_efficiency >= 75:
            emoji = "😊"
        elif self.staffing_efficiency >= 50:
            emoji = "😐"
        else:
            emoji = "😰"
        
        return f"{emoji} Staff: {self.active_employees}/{self.total_employees} active, {self.completion_rate:.0f}% completion rate"
    
    def to_json(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        data = asdict(self)
        # Convert Employee objects to their JSON representations
        data["top_performers"] = [emp.to_json() for emp in self.top_performers]
        data["training_needed"] = [emp.to_json() for emp in self.training_needed]
        return data