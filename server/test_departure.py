from departure_optimizer import recommend_departure

traffic_predictions = {
    "7:30 AM": "High",
    "7:40 AM": "Medium",
    "7:50 AM": "Low",
    "8:00 AM": "High"
}

best = recommend_departure(traffic_predictions)

print("Recommended Departure Time:")
print(f"Leave at {best['Departure Time']} to avoid traffic.")
print(f"Expected travel time: {best['Estimated Travel Time']} minutes.")