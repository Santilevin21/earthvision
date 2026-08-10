const requiredUser = "Douglas";
const requiredPassword = "Dinero";

const button = document.getElementById('login');
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
