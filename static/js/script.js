// -------------------
// Initialize Main Map
// -------------------
var map = L.map('map').setView([20.5937, 78.9629], 5);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '© OpenStreetMap contributors'
}).addTo(map);

let humanZones = [
  { lat: 28.6139, lng: 77.2090 }, // Delhi
  { lat: 19.0760, lng: 72.8777 }, // Mumbai
  { lat: 13.0827, lng: 80.2707 }  // Chennai
];

function isNearHumanZone(lat, lng) {
  for (let zone of humanZones) {
    let distance = Math.sqrt(Math.pow(lat - zone.lat, 2) + Math.pow(lng - zone.lng, 2));
    if (distance < 0.5) return true;
  }
  return false;
}

var markers = L.layerGroup().addTo(map);

function loadSightings(species = "") {
  fetch(`/get_sightings?species=${species}`)
    .then(res => res.json())
    .then(data => {
      markers.clearLayers();
      data.forEach(s => {
        let danger = isNearHumanZone(s.lat, s.lng);
        L.circleMarker([s.lat, s.lng], {
          radius: 6,
          color: danger ? 'red' : 'green',
          fillOpacity: 0.8
        }).addTo(markers)
        .bindPopup(`
          <b>${s.name}</b><br>
          Observer: ${s.observer}<br>
          Date: ${s.date}<br>
          ${s.image ? `<img src="${s.image}" width="100">` : ''}
          <br>${danger ? '⚠️ DANGER' : '✅ Safe'}
        `);
      });

      // 🔥 Update gallery with images
      updateGallery(data);
    })
    .catch(err => console.error(err));
}

// -------------------
// Gallery Update
// -------------------
function updateGallery(data) {
  let gallery = document.querySelector(".gallery");
  gallery.innerHTML = ""; // clear old images

  let imagesAdded = false;

  data.forEach(s => {
    if (s.image) {
      let img = document.createElement("img");
      img.src = s.image;
      img.alt = s.name;
      img.style.width = "150px";
      img.style.margin = "10px";
      img.style.borderRadius = "8px";
      img.style.boxShadow = "0 0 6px rgba(0,0,0,0.3)";
      gallery.appendChild(img);
      imagesAdded = true;
    }
  });

  if (!imagesAdded) {
    gallery.innerHTML = "<p>No images available for this search.</p>";
  }
}

// -------------------
// Submit Sighting
// -------------------
document.getElementById('submitBtn').addEventListener('click', () => {
  let species = document.getElementById('userSpecies').value;
  let lat = parseFloat(document.getElementById('userLat').value);
  let lng = parseFloat(document.getElementById('userLng').value);
  let msgEl = document.getElementById('submitMessage');

  if (!species || !lat || !lng) {
    msgEl.style.color = 'red';
    msgEl.textContent = "Please fill all fields.";
    return;
  }

  fetch('/submit_sighting', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: species, lat: lat, lng: lng })
  })
  .then(res => res.json())
  .then(data => {
    msgEl.style.color = 'green';
    msgEl.textContent = data.message;
    loadSightings(species);
  })
  .catch(err => {
    msgEl.style.color = 'red';
    msgEl.textContent = "Error submitting sighting.";
    console.error(err);
  });
});

// -------------------
// Initialize Analytics Map
// -------------------
var analyticsMap = L.map('analyticsMap').setView([20.5937, 78.9629], 5);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '© OpenStreetMap contributors'
}).addTo(analyticsMap);

var analyticsMarkers = L.layerGroup().addTo(analyticsMap);

function updateAnalytics(species) {
  fetch(`/get_sightings?species=${species}`)
    .then(res => res.json())
    .then(data => {
      // Clear markers
      analyticsMarkers.clearLayers();

      data.forEach(s => {
        let danger = isNearHumanZone(s.lat, s.lng);
        L.circleMarker([s.lat, s.lng], {
          radius: 6,
          color: danger ? 'red' : 'green',
          fillOpacity: 0.8
        }).addTo(analyticsMarkers)
        .bindPopup(`
          <b>${s.name}</b><br>
          Observer: ${s.observer}<br>
          Date: ${s.date}<br>
          ${s.image ? `<img src="${s.image}" width="100">` : ''}
          <br>${danger ? '⚠️ DANGER' : '✅ Safe'}
        `);
      });

      // Bar chart
      let counts = {};
      data.forEach(s => counts[s.name] = (counts[s.name] || 0) + 1);
      Plotly.newPlot('barChart', [{
        x: Object.keys(counts),
        y: Object.values(counts),
        type: 'bar'
      }]);

      // Trend chart (placeholder timeline)
      let dates = data.map((_, i) => new Date());
      Plotly.newPlot('trendChart', [{
        x: dates,
        y: Object.values(counts),
        type: 'line'
      }]);

      // Update note
      document.getElementById('dataNote').textContent = `Showing ${data.length} observations.`;

      // Scroll to analytics map
      document.getElementById('analyticsMap').scrollIntoView({ behavior: 'smooth' });
    })
    .catch(err => console.error(err));
}

// Bind search button
document.getElementById('searchBtn').addEventListener('click', () => {
  let species = document.getElementById('speciesInput').value;
  updateAnalytics(species);
  loadSightings(species); // 🔥 also refresh gallery when searching
});

// Default load
document.addEventListener('DOMContentLoaded', () => {
  loadSightings();
  updateAnalytics('');
});
