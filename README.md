# Wildlife Sighting Dashboard

A **Flask + Dash web app** to visualize wildlife sightings with an interactive map and analytics dashboard.

---

## Features
- Interactive map showing wildlife sightings
- Analytics dashboard with charts and stats
- View sightings data with images

---

## Screenshots
![Map](static/images/Screenshot_map.png) ![Analytics](static/images/Screenshot_page.png)

---

## How to Run Locally
1. Clone repo:  
```bash
git clone https://github.com/anjum-28/wildlife_dashboard.git
cd wildlife_dashboard

python -m venv venv
.\venv\Scripts\Activate   # PowerShell
# or
venv\Scripts\activate     # CMD

pip install flask dash pandas plotly requests

python app.py
