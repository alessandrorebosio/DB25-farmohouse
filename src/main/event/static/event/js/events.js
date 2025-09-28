(function () {
    const init = () => {
        document.querySelectorAll('.capacity').forEach(el => {
            const toInt = (v) => {
                const n = parseInt(v, 10);
                return Number.isNaN(n) ? 0 : n;
            };
            const seats = toInt(el.dataset.seats);
            const remaining = toInt(el.dataset.remaining);
            const taken = Math.max(0, seats - remaining);
            const pct = seats > 0 ? Math.min(100, Math.round((taken / Math.max(seats, 1)) * 100)) : 0;
            const bar = el.querySelector('.capacity-fill');
            if (!bar) return;

            bar.style.width = '0%';
            requestAnimationFrame(() => {
                bar.style.width = pct + '%';
            });
        });
    };
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
