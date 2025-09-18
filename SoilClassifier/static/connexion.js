document.addEventListener('DOMContentLoaded', () => {
    const tabs = document.querySelectorAll('.tab-link');
    const forms = document.querySelectorAll('.form-content');

    // Gérer le cas où il y a des erreurs de formulaire au chargement de la page
    const loginFormHasErrors = document.querySelector('#login-form .form-errors');
    const signupFormHasErrors = document.querySelector('#signup-form .form-errors');

    if (signupFormHasErrors) {
        // Si le formulaire d'inscription a des erreurs, l'afficher par défaut
        showForm('signup');
    } else {
        // Sinon, afficher le formulaire de connexion par défaut
        showForm('login');
    }

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetFormId = tab.dataset.form; // "login" ou "signup"
            showForm(targetFormId);
        });
    });

    function showForm(formId) {
        const targetForm = document.getElementById(`${formId}-form`);
        const targetTab = document.querySelector(`.tab-link[data-form='${formId}']`);

        // Mettre à jour l'état actif des onglets
        tabs.forEach(t => t.classList.remove('active'));
        if (targetTab) {
            targetTab.classList.add('active');
        }

        // Afficher le bon formulaire
        forms.forEach(form => form.classList.remove('active'));
        if (targetForm) {
            targetForm.classList.add('active');
        }
    }
});