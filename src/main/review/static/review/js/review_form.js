/* Review form interactions: live comment length counter.
 * Uses data attributes to decouple from server-side IDs.
 */
(function () {
    const textareas = document.querySelectorAll('[data-behavior="comment-textarea"]');
    if (!textareas.length) return;

    textareas.forEach((textarea) => {
        const counterSel = textarea.getAttribute('data-counter');
        const counter = counterSel ? document.querySelector(counterSel) : null;
        if (!counter) return;

        const update = () => {
            counter.textContent = String(textarea.value.length);
        };

        textarea.addEventListener('input', update);
        update();
    });
})();
