from flask import Flask, render_template, jsonify, request
import requests
import pandas as pd
import json
import os

app = Flask(__name__)

# ---------------------------
# User submissions file
# ---------------------------
USER_FILE = "user_sightings.json"
if not os.path.exists(USER_FILE):
    with open(USER_FILE, "w") as f:
        json.dump([], f)

# ---------------------------
# Routes
# ---------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/get_sightings")
def get_sightings():
    species = request.args.get("species", "").strip()
    url = "https://api.inaturalist.org/v1/observations"
    params = {"per_page": 100, "geo": True}
    if species:
        params["taxon_name"] = species

    sightings = []

    try:
        r = requests.get(url, params=params, timeout=8)
        r.raise_for_status()
        data = r.json().get("results", [])

        for obs in data:
            gj = obs.get("geojson")
            if not gj or "coordinates" not in gj:
                continue
            lng, lat = gj["coordinates"]
            sightings.append({
                "name": obs.get("species_guess", "Unknown"),
                "lat": lat,
                "lng": lng,
                "observer": obs.get("user", {}).get("name", "Unknown"),
                "date": obs.get("observed_on", "Unknown"),
                "image": obs.get("photos")[0]["url"] if obs.get("photos") else None
            })
    except Exception:
        sightings = [
            {"name": "Tiger",    "lat": 28.7041, "lng": 77.1025, "observer": "Admin", "date": "2025-01-01", "image": None},
            {"name": "Leopard",  "lat": 19.0760, "lng": 72.8777, "observer": "Admin", "date": "2025-01-01", "image": None},
            {"name": "Elephant", "lat": 13.0827, "lng": 80.2707, "observer": "Admin", "date": "2025-01-01", "image": None},
        ]

    # Add user sightings
    try:
        if os.path.exists(USER_FILE):
            with open(USER_FILE, "r") as f:
                user_sightings = json.load(f)
            for s in user_sightings:
                sightings.append({
                    "name": s.get("name"),
                    "lat": s.get("lat"),
                    "lng": s.get("lng"),
                    "observer": "User",
                    "date": "N/A",
                    "image": s.get("image", None)
                })
    except Exception:
        pass

    return jsonify(sightings)


@app.route("/submit_sighting", methods=["POST"])
def submit_sighting():
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data received"}), 400

    try:
        with open(USER_FILE, "r") as f:
            sightings = json.load(f)
        sightings.append(data)
        with open(USER_FILE, "w") as f:
            json.dump(sightings, f, indent=2)
        return jsonify({"message": "Sighting submitted successfully!"})
    except Exception as e:
        return jsonify({"message": f"Error saving sighting: {str(e)}"}), 500


@app.route("/get_species_image")
def get_species_image():
    species = request.args.get("species", "").strip()
    if not species:
        return jsonify({"image": None})

    url = "https://api.inaturalist.org/v1/observations"
    params = {"per_page": 1, "taxon_name": species, "geo": True}

    try:
        r = requests.get(url, params=params, timeout=8)
        r.raise_for_status()
        data = r.json().get("results", [])
        if data and data[0].get("photos"):
            image_url = data[0]["photos"][0]["url"]
            return jsonify({"image": image_url})
        else:
            return jsonify({"image": None})
    except Exception:
        return jsonify({"image": None})



# ---------------------------
# Dash integration at /dash/
# ---------------------------
def fetch_observations_df(species: str) -> pd.DataFrame:
    url = "https://api.inaturalist.org/v1/observations"
    params = {"per_page": 200, "geo": True}
    if species:
        params["taxon_name"] = species

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json().get("results", [])
        rows = []
        for obs in data:
            gj = obs.get("geojson")
            if not gj or "coordinates" not in gj:
                continue
            lng, lat = gj["coordinates"]
            rows.append({"name": obs.get("species_guess", "Unknown"), "lat": lat, "lng": lng})
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame([
            {"name": "Tiger", "lat": 28.7041, "lng": 77.1025},
            {"name": "Leopard", "lat": 19.0760, "lng": 72.8777},
            {"name": "Elephant", "lat": 13.0827, "lng": 80.2707},
        ])


def create_dash_app(flask_app):
    import dash
    from dash import html, dcc, Input, Output, State
    import plotly.express as px

    dash_app = dash.Dash(
        __name__,
        server=flask_app,
        url_base_pathname="/dash/",
        suppress_callback_exceptions=True,
        title="Wildlife Analytics",
    )

    dash_app.layout = html.Div(
        style={"maxWidth": "1100px", "margin": "0 auto", "padding": "12px"},
        children=[
            html.H2("Wildlife Analytics (Dash + Plotly)"),
            html.Div([
                dcc.Input(
                    id="species-input",
                    type="text",
                    placeholder="Enter species (e.g., tiger, koala)",
                    value="tiger",
                    style={"width": "60%", "padding": "8px"}
                ),
                html.Button("Update", id="update-btn", n_clicks=0,
                            style={"marginLeft": "8px", "padding": "8px 16px"}),
                html.A(" ↩ Back to Dashboard", href="/", style={"marginLeft": "16px"})
            ], style={"marginBottom": "12px"}),

            dcc.Loading(
                type="default",
                children=[
                    dcc.Graph(id="map-fig"),
                    dcc.Graph(id="count-fig"),
                    dcc.Graph(id="trend-fig"),
                ]
            ),
            html.Div(id="data-note", style={"fontSize": "12px", "color": "#666"})
        ]
    )

    @dash_app.callback(
        [Output("map-fig", "figure"),
         Output("count-fig", "figure"),
         Output("trend-fig", "figure"),
         Output("data-note", "children")],
        [Input("update-btn", "n_clicks")],
        [State("species-input", "value")]
    )
    def refresh(n, species):
        df = fetch_observations_df(species)

        fig_map = px.scatter_mapbox(df, lat="lat", lon="lng", text="name", zoom=3, height=500)
        fig_map.update_layout(mapbox_style="open-street-map")

        counts = df["name"].value_counts().reset_index()
        counts.columns = ["name", "count"]
        fig_count = px.bar(counts.head(15), x="name", y="count", title="Top Observed Species")

        df["date"] = pd.date_range(end=pd.Timestamp.today(), periods=len(df))
        fig_trend = px.line(df, x="date", y=df.groupby("date").cumcount(), title="Sightings Trend Over Time")

        note = f"Showing {len(df)} observations (API + fallback)."
        return fig_map, fig_count, fig_trend, note

    return dash_app


# Create Dash app
create_dash_app(app)

if __name__ == "__main__":
    app.run(debug=True)
