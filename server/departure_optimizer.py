import pandas as pd

traffic_time = {
    "Low": 30,
    "Medium": 40,
    "High": 55
}

def recommend_departure(predictions):

    results = []

    for time, traffic in predictions.items():
        travel_time = traffic_time[traffic]

        results.append({
            "Departure Time": time,
            "Traffic Level": traffic,
            "Estimated Travel Time": travel_time
        })

    df = pd.DataFrame(results)

    best_option = df.loc[df['Estimated Travel Time'].idxmin()]

    return best_option