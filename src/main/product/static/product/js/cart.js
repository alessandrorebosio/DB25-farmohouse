document.addEventListener('DOMContentLoaded', () => {
    const debounce = (fn, delay = 350) => { let t; return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), delay); }; };
    const updateFormSelector = 'form[action*="/cart/update/"]';

    document.querySelectorAll(`${updateFormSelector} input[name="qty"]`).forEach(input => {
        const submit = debounce(() => input.form && input.form.requestSubmit());
        input.addEventListener('input', submit);
        input.addEventListener('change', () => input.form && input.form.requestSubmit());
    });

    document.querySelectorAll(`${updateFormSelector} .btn-qty`).forEach(btn => {
        btn.addEventListener('click', () => {
            const form = btn.closest('form');
            const input = form && form.querySelector('input[name="qty"]');
            if (!input) return;
            const delta = parseInt(btn.dataset.delta, 10) || 0;
            const min = parseInt(input.min, 10); const minVal = isNaN(min) ? 0 : min;
            const curr = parseInt(input.value, 10); const currVal = isNaN(curr) ? minVal : curr;
            const next = Math.max(minVal, currVal + delta);
            input.value = next;
            input.dispatchEvent(new Event('input', { bubbles: true }));
        });
    });
});