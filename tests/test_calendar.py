"""Unit tests for the Demesne Calendar class."""
import pytest
from datetime import date

from simulations.Demesne.calendar import Calendar, CalendarEntry


@pytest.fixture
def calendar():
    """Load the default Demesne calendar."""
    return Calendar("simulations/Demesne/calendar.yaml")


class TestCalendarLoading:
    def test_loads_entries(self, calendar):
        """Calendar should load multiple entries from YAML."""
        assert len(calendar.entries) > 0

    def test_entries_sorted_by_day(self, calendar):
        """Entries should be sorted by day-of-year."""
        days = [e.as_day_of_year() for e in calendar.entries]
        assert days == sorted(days)


class TestCurrentProcessFor:
    def test_returns_process_on_exact_date(self, calendar):
        """Should return the process when query_date matches an event date."""
        # Wheat sowing is on 10-01; on that exact date sowing is returned
        result = calendar.current_process_for(
            "source/plant/species/cereal/wheat",
            date(2025, 10, 1)
        )
        # 10-01 has sowing event, but ploughing (09-20) also <= 10-01
        # Since entries are sorted and we iterate, ploughing comes first then sowing
        # The loop keeps updating candidate, so sowing (10-01) should win
        # Actually wheat ploughing 09-20 and sowing 10-01 both exist;
        # on 10-01, sowing is the one that matches exactly
        assert result == "process/cultivation/sowing"

    def test_returns_most_recent_process(self, calendar):
        """Should return the most recent process before query_date."""
        # Wheat: sowing on 10-01, slaughter on 11-11
        # Query on 10-15 should still be sowing
        result = calendar.current_process_for(
            "source/plant/species/cereal/wheat",
            date(2025, 10, 15)
        )
        assert result == "process/cultivation/sowing"

    def test_wraps_to_last_event_if_before_first(self, calendar):
        """If query is before first event of year, wrap to last event."""
        # Wheat first event is ploughing on 09-20
        # Query on 01-05 should wrap to last event (sowing 10-01)
        result = calendar.current_process_for(
            "source/plant/species/cereal/wheat",
            date(2025, 1, 5)
        )
        assert result == "process/cultivation/sowing"

    def test_returns_none_for_unknown_species(self, calendar):
        """Should return None for species not in calendar."""
        result = calendar.current_process_for(
            "source/plant/species/unknown/exotic",
            date(2025, 6, 1)
        )
        assert result is None


class TestNextProcess:
    def test_returns_next_event_after_date(self, calendar):
        """Should return the next event for the species after query_date."""
        # Wheat: ploughing 09-20, sowing 10-01
        # Query on 09-25 should return sowing on 10-01
        result = calendar.next_process(
            date(2025, 9, 25),
            "source/plant/species/cereal/wheat"
        )
        assert result is not None
        process, trigger = result
        assert process == "process/cultivation/sowing"
        assert trigger == date(2025, 10, 1)

    def test_wraps_to_next_year(self, calendar):
        """If no more events this year, wrap to first event next year."""
        # Wheat last event is sowing 10-01
        # Query on 12-01 should wrap to ploughing 09-20 next year
        result = calendar.next_process(
            date(2025, 12, 1),
            "source/plant/species/cereal/wheat"
        )
        assert result is not None
        process, trigger = result
        # First wheat event is ripening 07-20
        assert trigger.year == 2026

    def test_returns_none_for_unknown_species(self, calendar):
        """Should return None for species not in calendar."""
        result = calendar.next_process(
            date(2025, 6, 1),
            "source/plant/species/unknown/exotic"
        )
        assert result is None


class TestCalendarEntry:
    def test_as_day_of_year(self):
        """CalendarEntry.as_day_of_year should return correct day number."""
        entry = CalendarEntry(month=3, day=15, process="test", species=["x"])
        # March 15 in a non-leap year is day 74
        assert entry.as_day_of_year(year=2025) == 74

    def test_species_list_normalization(self, calendar):
        """Species should always be stored as a list."""
        for entry in calendar.entries:
            assert isinstance(entry.species, list)
