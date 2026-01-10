"""Calendar class for Demesne agricultural schedule.

Reads calendar.yaml and provides lookup methods for species processes.
"""
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import List, Optional, Tuple

import yaml


@dataclass
class CalendarEntry:
    """A single calendar event entry."""
    month: int
    day: int
    process: str
    species: List[str]

    def as_day_of_year(self, year: int = 2001) -> int:
        """Return the day-of-year for this entry (1-365).
        
        Uses a non-leap year (2001) by default for consistent comparison.
        """
        return date(year, self.month, self.day).timetuple().tm_yday


class Calendar:
    """Agricultural calendar for the Demesne simulation.

    Loads events from a YAML file and provides methods to query
    which process applies to a species on a given date.
    """

    def __init__(self, yaml_path: Optional[str] = None) -> None:
        """Initialize Calendar from a YAML file.

        Args:
            yaml_path: Path to the calendar YAML file. If None, uses
                       the default `simulations/Demesne/calendar.yaml`.
        """
        if yaml_path is None:
            yaml_path = str(Path(__file__).parent / "calendar.yaml")

        self._entries: List[CalendarEntry] = []
        self._load_yaml(yaml_path)

    def _load_yaml(self, yaml_path: str) -> None:
        """Parse the YAML file and populate internal entries."""
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        events = data.get("events", [])
        for ev in events:
            date_str = ev.get("date", "")
            process = ev.get("process", "")
            species_raw = ev.get("species", [])

            # Parse MM-DD
            parts = date_str.split("-")
            if len(parts) != 2:
                continue
            month, day = int(parts[0]), int(parts[1])

            # Normalize species to list
            if isinstance(species_raw, str):
                species_list = [species_raw]
            else:
                species_list = list(species_raw)

            self._entries.append(
                CalendarEntry(month=month, day=day, process=process, species=species_list)
            )

        # Sort entries by day-of-year for efficient lookup
        self._entries.sort(key=lambda e: e.as_day_of_year())

    def _day_of_year(self, d: date) -> int:
        """Return day-of-year (1-366) for a date."""
        return d.timetuple().tm_yday

    def _entries_for_species(self, species: str) -> List[CalendarEntry]:
        """Return all entries that include this species, sorted by day-of-year."""
        return [e for e in self._entries if species in e.species]

    def current_process_for(self, species: str, query_date: date) -> Optional[str]:
        """Return the ongoing process for a species on the given date.

        The "ongoing" process is the most recent (or same-day) event
        for this species that started on or before `query_date`.
        If no matching event is found in the current calendar year,
        wraps to the last event from the previous cycle (annual wrap).

        Args:
            species: Taxonomy path string (e.g. "source/plant/species/cereal/wheat").
            query_date: The date to query.

        Returns:
            Process path string or None if no events exist for this species.
        """
        relevant = self._entries_for_species(species)
        if not relevant:
            return None

        doy = self._day_of_year(query_date)

        # Find most recent event on or before this day-of-year
        candidate: Optional[CalendarEntry] = None
        for entry in relevant:
            entry_doy = entry.as_day_of_year()
            if entry_doy <= doy:
                candidate = entry
            else:
                break  # entries are sorted; no need to continue

        # If none found (query date is before first event), wrap to last event of year
        if candidate is None:
            candidate = relevant[-1]

        return candidate.process

    def next_process(self, query_date: date, species: str) -> Optional[Tuple[str, date]]:
        """Return the next scheduled process and its trigger date for a species.

        Args:
            query_date: The reference date.
            species: Taxonomy path string.

        Returns:
            A tuple (process_path, trigger_date) for the next event after
            `query_date`, or None if no events exist for this species.
            The trigger_date uses the same year as query_date, or next year
            if wrapping around the calendar.
        """
        relevant = self._entries_for_species(species)
        if not relevant:
            return None

        doy = self._day_of_year(query_date)
        year = query_date.year

        # Find first event strictly after this day-of-year
        for entry in relevant:
            entry_doy = entry.as_day_of_year()
            if entry_doy > doy:
                trigger = date(year, entry.month, entry.day)
                return (entry.process, trigger)

        # Wrap to first event of next year
        first = relevant[0]
        trigger = date(year + 1, first.month, first.day)
        return (first.process, trigger)

    @property
    def entries(self) -> List[CalendarEntry]:
        """Return all calendar entries (read-only copy)."""
        return list(self._entries)
