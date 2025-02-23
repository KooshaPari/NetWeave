import geopandas as gpd
import pandas as pd

# Load the data
cities = gpd.read_file("ne_10m_populated_places.zip")

# Select and rename relevant columns
cities_df = cities[["NAME_EN", "ADM0NAME", "LATITUDE", "LONGITUDE", "POP_MAX"]].rename(
    columns={
        "NAME_EN": "city",
        "ADM0NAME": "country",
        "LATITUDE": "lat",
        "LONGITUDE": "lon",
        "POP_MAX": "population",
    }
)

# Filter for major cities (population > 1M)
cities_df = cities_df[cities_df["population"] > 800000]

# Sort by population descending
cities_df = cities_df.sort_values("population", ascending=False)

# Save to CSV
cities_df.to_csv("cities.csv", index=False)

# Print summary
print(f"Saved {len(cities_df)} cities to cities.csv")
print("\nTop 5 cities by population:")
print(cities_df.head())
