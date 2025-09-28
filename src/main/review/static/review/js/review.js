/* Small enhancements for the Reviews page.
 * - Disable service_type when target = event
 */
(function () {
    const target = document.getElementById('filter-target');
    const st = document.getElementById('filter-service-type');
    if (!target || !st) return;

    function toggleServiceType() {
        const disable = target.value === 'event';
        st.disabled = disable;
        if (disable) st.value = '';
    }

    target.addEventListener('change', toggleServiceType);

    toggleServiceType();
})();
