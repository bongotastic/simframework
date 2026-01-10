"""Example script demonstrating Entity usage: a jerrycan of fuel."""
from simframework.entity import Entity


def main():
    # Create a jerrycan (container)
    jerrycan = Entity(essence="jerrycan", volume_liters=25.0, mass_kg=2.0)
    print("Created jerrycan container:")
    print(f"  identifier: {jerrycan.essence}")
    print(f"  volume_liters: {jerrycan.volume_liters}")
    print(f"  mass_kg: {jerrycan.mass_kg}")

    # Create a fuel entity (1L unit)
    fuel = Entity(essence="fuel", volume_liters=1.0, mass_kg=0.8)
    
    # Add 25L of fuel (25 units of 1L each) to the jerrycan
    jerrycan.add_to_container(fuel, quantity=25)
    fuel_in_jerrycan = jerrycan.query_container("fuel")
    total_volume = sum(f.volume_liters for f in fuel_in_jerrycan)
    print(f"\nFilled jerrycan with {len(fuel_in_jerrycan)} fuel units = {total_volume}L")

    # Remove 12L of fuel (12 units)
    removed = jerrycan.remove_from_container("fuel", count=12)
    removed_volume = sum(f.volume_liters for f in removed)
    print(f"\nRemoved {len(removed)} fuel units = {removed_volume}L")

    # Check remaining
    remaining_fuel = jerrycan.query_container("fuel")
    remaining_volume = sum(f.volume_liters for f in remaining_fuel)
    print(f"\nRemaining in jerrycan: {len(remaining_fuel)} fuel units = {remaining_volume}L")


if __name__ == "__main__":
    main()
