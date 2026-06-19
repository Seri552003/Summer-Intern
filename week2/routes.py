# routes.py
# Manufacturing Routes define karo
# Week 2 | LLM-CAPP Project

# Route A — Standard process
ROUTE_A = [
    "Facing",
    "Center Drilling",
    "Drilling",
    "Reaming",
    "Inspection"
]

# Route B — Simple process
ROUTE_B = [
    "Facing",
    "Drilling",
    "Boring",
    "Inspection"
]

# Route C — Thread process
ROUTE_C = [
    "Facing",
    "Drilling",
    "Threading",
    "Chamfering",
    "Inspection"
]

ALL_ROUTES = {
    "Route_A": ROUTE_A,
    "Route_B": ROUTE_B,
    "Route_C": ROUTE_C
}

def get_route(name: str) -> list:
    return ALL_ROUTES.get(name, [])

def print_all_routes():
    for name, steps in ALL_ROUTES.items():
        print(f"\n{name}:")
        for i, step in enumerate(steps, 1):
            print(f"  {i}. {step}")

if __name__ == "__main__":
    print("=== Manufacturing Routes ===")
    print_all_routes()