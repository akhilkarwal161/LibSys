/**
 * Aggressive Link Preloading, connection speed checking, and Performance Observer instrumentation.
 * OOG BOOG! CAVEMAN ENGINEER MAKE SITE SPEEDY LIKE CHEETAH!
 */
window.addEventListener("load", () => {
    const preloaded = new Set();

    // 1. DYNAMIC CONNECTION ADJUSTMENT
    const isSlowConnection = () => {
        const conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
        if (conn) {
            // Save-Data is active or cellular connection is 2G/3G
            if (conn.saveData || /(2g|3g)/.test(conn.effectiveType)) {
                console.log("[PERF] OOG BOOG! Slow connection or data saver detected. Disabling aggressive preloading to save bandwidth.");
                return true;
            }
        }
        return false;
    };

    // Helper for manual or link show clicks
    window.show = function(pageId, originId) {
        console.log("[NAV] Navigate page: " + pageId + " from: " + originId);
        return true; 
    };

    const preload = (url) => {
        if (!url || isSlowConnection()) return;
        try {
            const parsedUrl = new URL(url, window.location.href);
            if (parsedUrl.origin !== window.location.origin) return;
            const cleanUrl = parsedUrl.pathname + parsedUrl.search;
            if (preloaded.has(cleanUrl) || cleanUrl.startsWith('#') || cleanUrl.startsWith('/logout') || cleanUrl.startsWith('/admin')) return;

            preloaded.add(cleanUrl);
            const link = document.createElement('link');
            link.rel = 'prefetch';
            link.href = cleanUrl;
            document.head.appendChild(link);
            console.log("[PRELOAD] Prefetched link: " + cleanUrl);
        } catch (e) {
            // Ignore errors
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
        links.forEach(link => observer.observe(link));
    }

    // High-priority preload on hover or touch
    links.forEach(link => {
        link.addEventListener('mouseenter', () => preload(link.href), { passive: true });
        link.addEventListener('touchstart', () => preload(link.href), { passive: true });
    });

    // 2. CLIENT-SIDE PERFORMANCE OBSERVER INSTRUMENTATION
    if ('PerformanceObserver' in window) {
        try {
            // A. Monitor Navigation Timing (TTFB, DOM ready, Server Timings)
            const navObserver = new PerformanceObserver((list) => {
                list.getEntries().forEach((entry) => {
                    const ttfb = entry.responseStart - entry.startTime;
                    const domReady = entry.domContentLoadedEventEnd - entry.startTime;
                    const totalLoad = entry.loadEventEnd - entry.startTime;
                    
                    console.log("\n" + "="*45);
                    console.log("   🦖 LIBSYS REAL-TIME NAVIGATION METRICS");
                    console.log("="*45);
                    console.log(` -> Page URL:          ${entry.name}`);
                    console.log(` -> TTFB (Server):     ${ttfb.toFixed(1)} ms`);
                    console.log(` -> DOM Interactive:   ${domReady.toFixed(1)} ms`);
                    console.log(` -> Total Load Time:   ${totalLoad.toFixed(1)} ms`);
                    
                    // Expose Django Server-Timing metrics
                    if (entry.serverTiming && entry.serverTiming.length > 0) {
                        console.log("-"*45);
                        console.log("   ⚙️ DJANGO SERVER BACKEND TIMINGS:");
                        entry.serverTiming.forEach((metric) => {
                            console.log(` -> Server ${metric.name}:   ${metric.duration.toFixed(1)} ms`);
                        });
                    }
                    console.log("="*45 + "\n");
                });
            });
            navObserver.observe({ type: 'navigation', buffered: true });

            // B. Monitor Long Tasks (Main thread blocked > 50ms)
            const longTaskObserver = new PerformanceObserver((list) => {
                list.getEntries().forEach((entry) => {
                    console.warn(`[PERF WARNING] ⚠️ Main thread blocked by long-running task for ${entry.duration.toFixed(1)} ms! Source:`, entry.attribution || "Unknown");
                });
            });
            longTaskObserver.observe({ type: 'longtask', buffered: true });

            // C. Monitor Large Contentful Paint (LCP)
            const lcpObserver = new PerformanceObserver((list) => {
                list.getEntries().forEach((entry) => {
                    console.log(`[PERF] Largest Contentful Paint (LCP) rendered at: ${entry.startTime.toFixed(1)} ms`);
                });
            });
            lcpObserver.observe({ type: 'largest-contentful-paint', buffered: true });

        } catch (e) {
            console.log("[PERF] PerformanceObserver init error:", e);
        }
    }
});
