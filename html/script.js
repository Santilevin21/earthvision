const requiredUser = "Douglas";
const requiredPassword = "Dinero";

const button = document.getElementById('hectarea');
const userInput = document.getElementById('username');
const passwordInput = document.getElementById('password');
const responseText = document.getElementById('response');

button.addEventListener('click', () => {
    const user = userInput.value;
    const password = passwordInput.value;

    if (user === requiredUser && password === requiredPassword) {
        window.location.href = 'app.html'; 
    } else {
        responseText.textContent = "Usuario o contraseña incorrectos";
    }
});

document.addEventListener('DOMContentLoaded', () => {
    // Elementos UI
    const triggerSignup = document.getElementById('triggerSignup');
    const pageWrapper = document.getElementById('pageWrapper');
    const btnOpenMap = document.getElementById('btn-open-map');
    const btnCloseMap = document.getElementById('btn-close-map');
    const mapModal = document.getElementById('map-modal');
    
    const fieldAreaInput = document.getElementById('field-area');
    const fieldCoordsInput = document.getElementById('field-coordinates');
  
    let map = null;
    let marker = null;
  
    // 1. Animación expandir tarjeta
    if (triggerSignup && pageWrapper) {
      triggerSignup.addEventListener('click', () => {
        pageWrapper.classList.add('expanded');
      });
    }
  
    // 2. Control del mapa Modal
    if (btnOpenMap && mapModal && btnCloseMap) {
  
      btnOpenMap.addEventListener('click', () => {
        mapModal.classList.add('active');
  
        // Inicializar Leaflet solo la primera vez que se abre
        if (!map) {
          setTimeout(() => {
            // Coordenadas por defecto (Buenos Aires)
            map = L.map('map-container').setView([-34.6037, -58.3816], 13);
  
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
              attribution: '© OpenStreetMap'
            }).addTo(map);
  
            // Evento de clic en el mapa
            map.on('click', (e) => {
              const { lat, lng } = e.latlng;
              
              if (marker) {
                marker.setLatLng(e.latlng);
              } else {
                marker = L.marker(e.latlng).addTo(map);
              }
  
              // Simulación de cálculo de área estimada en m² y rellenado de inputs
              const estimatedArea = (Math.random() * (5000 - 500) + 500).toFixed(2);
  
              fieldCoordsInput.value = `${lat.toFixed(5)}, ${lng.toFixed(5)}`;
              fieldAreaInput.value = `${estimatedArea} m²`;
  
              // Cerrar el modal automáticamente tras seleccionar
              setTimeout(() => {
                mapModal.classList.remove('active');
              }, 600);
            });
          }, 100);
        } else {
          setTimeout(() => map.invalidateSize(), 100);
        }
      });
  
      // Cerrar modal
      btnCloseMap.addEventListener('click', () => {
        mapModal.classList.remove('active');
      });
  
      mapModal.addEventListener('click', (e) => {
        if (e.target === mapModal) {
          mapModal.classList.remove('active');
        }
      });
    }
  });