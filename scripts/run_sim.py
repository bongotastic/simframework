"""Simple demo runner for the simulation framework."""
from simframework import SimulationEngine

def main():
    engine = SimulationEngine()
    # Schedule events with data payloads instead of callbacks
    engine.scheduler.schedule(0, message="Start")
    engine.scheduler.schedule(1.5, message="hello")
    engine.scheduler.schedule(0.5, message="quick")
    
    print("Running simulation...")
    # Run loop: step() returns the event, we handle the logic (printing) here
    while True:
        event = engine.scheduler.step()
        if event is None:
            break
        
        msg = event.data.get("message")
        if msg:
            print(f"Event at t={engine.scheduler.now}: {msg}")

if __name__ == "__main__":
    main()
