function updateTemperatureData() {
    fetch('/api/temperature/')
        .then(response => response.json())
        .then(data => {
            document.getElementById('temperature').innerText = data.temperature;
            document.getElementById('humidity').innerText = data.humidity;
        })
        .catch(error => console.error('Error fetching temperature data:', error));
}

// // Initial call to populate data on page load
// updateTemperatureData();
// // Update temperature data every 5 seconds
// setInterval(updateTemperatureData, 5000);