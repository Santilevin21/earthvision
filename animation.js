document.addEventListener('DOMContentLoaded', () => {
    const pageWrapper = document.getElementById('pageWrapper');
    const triggerButton = document.getElementById('triggerSignup');
    const loginTab = document.getElementById('loginTab');
    const hectareaButton = document.getElementById('hectarea');

    if (!pageWrapper || !triggerButton || !loginTab) return;

    // Expandir: Sing-up -> vista completa (tarjeta a pantalla completa a la derecha)
    triggerButton.addEventListener('click', () => {
        pageWrapper.classList.add('expanded');

        if (hectareaButton) {
            hectareaButton.textContent = 'Sing-up';
        }
    });

    // Colapsar: Login -> vuelve a la pantalla inicial centrada
    loginTab.addEventListener('click', () => {
        pageWrapper.classList.remove('expanded');

        if (hectareaButton) {
            hectareaButton.textContent = 'Login';
        }
    });
});