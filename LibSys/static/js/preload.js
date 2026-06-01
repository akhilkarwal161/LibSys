/**
 * Aggressive Link Preloading & Navigation Optimizer
 * OOG BOOG! ME PRELOAD ALL THE THINGS FOR SPEEDY CAVEMAN WEB!
 */
document.addEventListener("DOMContentLoaded", () => {
    const preloaded = new Set();

    // Custom helper for manual or link show clicks
    window.show = function(pageId, originId) {
        console.log("OOG BOOG! Navigate page " + pageId + " from " + originId);
        return true; 
    };

    const preload = (url) => {
        if (!url) return;
        try {
            const parsedUrl = new URL(url, window.location.href);
            if (parsedUrl.origin !== window.location.origin) return;
            const cleanUrl = parsedUrl.pathname + parsedUrl.search;
            if (preloaded.has(cleanUrl) || cleanUrl.startsWith('#') || cleanUrl.startsWith('/logout')) return;

            preloaded.add(cleanUrl);
            const link = document.createElement('link');
            link.rel = 'prefetch';
            link.href = cleanUrl;
            document.head.appendChild(link);
            console.log("OOG BOOG! Preloaded: " + cleanUrl);
        } catch (e) {
            // Ignore parse errors
        }
    };

    // Preload local links in viewport (idle-time preloading)
    const links = document.querySelectorAll('a[href]');
    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    preload(entry.target.href);
                    observer.unobserve(entry.target);
                }
            });
        });

        links.forEach(link => {
            observer.observe(link);
        });
    }

    // High-priority preload on hover or touch
    links.forEach(link => {
        link.addEventListener('mouseenter', () => preload(link.href), { passive: true });
        link.addEventListener('touchstart', () => preload(link.href), { passive: true });
    });
});
