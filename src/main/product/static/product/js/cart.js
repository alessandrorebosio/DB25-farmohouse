document.addEventListener('DOMContentLoaded', () => {
    const debounce = (fn, delay = 300) => { let t; return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), delay); }; };
    const updateFormSelector = 'form[action$="/cart/update/"]';

    const guardedSubmit = (form) => {
        if (!form || form.dataset.submitting === '1') return;
        form.dataset.submitting = '1';
        form.requestSubmit();
    };

    document.querySelectorAll(`${updateFormSelector} input[name="qty"]`).forEach(input => {
        const submit = debounce(() => guardedSubmit(input.form));
        input.addEventListener('input', submit);
        // Removed 'change' handler to avoid double submit on blur/navigation
    });

    // No plus/minus buttons: rely on user typing. The debounced input handler will submit.
});