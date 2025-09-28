// Service page JS: sync date pickers and enable basic client-side validation.
(() => {
    const start = document.getElementById('room_start');
    const end = document.getElementById('room_end');
    if (start && end) {
        const sync = () => {
            if (start.value) end.min = start.value;
            if (end.value && start.value && end.value < start.value) end.value = start.value;
        };
        start.addEventListener('change', sync);
        window.addEventListener('DOMContentLoaded', sync);
    }
})();

(() => {
    const forms = document.querySelectorAll('form.needs-validation');
    forms.forEach((form) => {
        form.addEventListener('submit', (evt) => {
            if (!form.checkValidity()) {
                evt.preventDefault();
                evt.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
})();
