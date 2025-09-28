// Applies Bootstrap color theme (light/dark) following system preference.
(function () {
    const mq = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)');
    const apply = () => {
        document.documentElement.setAttribute('data-bs-theme', mq && mq.matches ? 'dark' : 'light');
    };
    apply();
    if (mq) {
        if (mq.addEventListener) mq.addEventListener('change', apply);
        else if (mq.addListener) mq.addListener(apply); // Safari < 14
    }
})();
