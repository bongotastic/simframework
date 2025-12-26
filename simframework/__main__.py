"""Demo: instantiate scheduler, populate with events from three categories, and process."""
import datetime

try:
    # Prefer absolute import when run as a module
    from simframework.scheduler import Scheduler
    from simframework.event import Event
except ImportError:
    # Fallback for running in environments where absolute imports fail
    from .scheduler import Scheduler
    from .event import Event


def main():
    start_time = datetime.datetime(2025, 1, 1, 0, 0, 0)
    scheduler = Scheduler(start_time=start_time)

    # Generate 40 events spread across 1-120 minutes in the future
    categories = ["growth", "weather", "people"]
    five_min_delta = datetime.timedelta(minutes=5)

    for i in range(1, 41):
        # Spread events across 1-120 minutes (i * 3 minutes each)
        trigger_minute = i * 3
        category = categories[i % 3]

        # Every 5th event has a fixed 5-minute timespan; others vary
        if i % 5 == 0:
            timespan = five_min_delta
        else:
            timespan = datetime.timedelta(minutes=i % 20 + 1)

        event = Event(
            data={
                "event_id": i,
                "trigger_minute": trigger_minute,
                "category": category,
            },
            timespan=timespan,
        )

        scheduler.insert_event(
            event,
            trigger_time=trigger_minute * 60,  # Convert minutes to seconds
            category=category,
        )

    print(f"Starting simulation at {scheduler.now}")
    print(f"Total events scheduled: 40 (spread across 1-120 minutes)")
    print("=" * 90)

    # Phase 1: Process only "people" events
    print("PHASE 1: Processing only 'people' events")
    print("-" * 90)
    event_num = 0
    while True:
        event = scheduler.pop_event(category="people")
        if event is None:
            break
        event_num += 1
        elapsed_minutes = (scheduler.now - start_time).total_seconds() / 60
        print(f"Event #{event_num:2d} | Elapsed: {elapsed_minutes:6.1f} min | "
              f"Category: {event.category:8s} | Timespan: {event.timespan} | "
              f"ID: {event.data['event_id']}")

    print(f"\nPhase 1 complete: {event_num} 'people' events processed")
    print("=" * 90)

    # Phase 2: Process all remaining events
    print("\nPHASE 2: Processing all remaining events (growth + weather)")
    print("-" * 90)
    event_num = 0
    while True:
        event = scheduler.step()
        if event is None:
            break
        event_num += 1
        elapsed_minutes = (scheduler.now - start_time).total_seconds() / 60
        print(f"Event #{event_num:2d} | Elapsed: {elapsed_minutes:6.1f} min | "
              f"Category: {event.category:8s} | Timespan: {event.timespan} | "
              f"ID: {event.data['event_id']}")

    print("=" * 90)
    print(f"Simulation ended at {scheduler.now}")
    print(f"Total elapsed time: {(scheduler.now - start_time).total_seconds() / 60:.1f} minutes")


if __name__ == "__main__":
    main()
