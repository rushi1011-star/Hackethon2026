// --- PART 1: THE SAVED DATA ---
// This represents data you might have pulled from a database (SQL, MongoDB, etc.)
const savedMarkers = [
    {
        id: 101,
        name: "Central Park",
        coords: [51.505, -0.09],
        category: "Park",
        description: "A beautiful green space in the city."
    },
    {
        id: 102,
        name: "Main Library",
        coords: [51.515, -0.1],
        category: "Education",
        description: "Open 24/7 for students."
    },
    {
        id: 103,
        name: "Riverside Cafe",
        coords: [51.498, -0.08],
        category: "Food",
        description: "Best coffee with a view."
    }
];

// --- PART 2: INITIALIZING THE MAP ---
// 'map' is the ID of your HTML <div>
const map = L.map('map').setView([51.505, -0.09], 13);

// Add the background tiles (OpenStreetMap)
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap'
}).addTo(map);

// --- PART 3: SHOWING THE DATA ---
// We create a "Layer Group" to hold all our saved points
const markersLayer = L.layerGroup().addTo(map);

function displaySavedData(dataArray) {
    dataArray.forEach(item => {
        // 1. Create the marker using the saved coordinates [lat, lng]
        const marker = L.marker(item.coords);

        // 2. Create a custom popup using the saved properties
        const popupContent = `
            <div style="padding: 5px;">
                <strong style="color: #0078A8;">${item.name}</strong><br/>
                <small>Category: ${item.category}</small><hr/>
                <p>${item.description}</p>
                <button onclick="alert('ID: ${item.id}')">View Details</button>
            </div>
        `;

        // 3. Bind the popup and add to the layer
        marker.bindPopup(popupContent);
        markersLayer.addLayer(marker);
    });
}

// Execute the function
displaySavedData(savedMarkers);

// --- PART 4: AUTO-ZOOM TO FIT DATA ---
// This ensures the user sees all markers immediately
const group = new L.FeatureGroup(markersLayer.getLayers());
map.fitBounds(group.getBounds().pad(0.1));