// Force scroll to top on page load - Enhanced version
(function() {
    'use strict';
    
    function forceScrollToTop() {
        // Disable smooth scrolling temporarily
        var originalBehavior = document.documentElement.style.scrollBehavior;
        document.documentElement.style.scrollBehavior = 'auto';
        
        // Force scroll to 0.1px to avoid fade-out state while keeping content visible
        window.scrollTo(0, 0.1);
        document.documentElement.scrollTop = 0.1;
        document.body.scrollTop = 0.1;
        
        // Also reset any CSS scroll-margin or scroll-padding
        document.body.style.scrollMarginTop = '0';
        document.documentElement.style.scrollMarginTop = '0';
        
        // Restore smooth behavior after a delay
        setTimeout(function() {
            document.documentElement.style.scrollBehavior = originalBehavior || 'smooth';
        }, 200);
    }
    
    // Execute immediately but less aggressively
    forceScrollToTop();
    setTimeout(forceScrollToTop, 50);
    
    // Execute when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            forceScrollToTop();
            setTimeout(forceScrollToTop, 10);
        });
    }
    
    // Execute when page is fully loaded
    window.addEventListener('load', function() {
        forceScrollToTop();
        setTimeout(forceScrollToTop, 10);
        setTimeout(forceScrollToTop, 50);
    });
    
    // Execute on page show (for back button)
    window.addEventListener('pageshow', function() {
        forceScrollToTop();
        setTimeout(forceScrollToTop, 10);
    });
    
    // Override any automatic scrolling behavior
    window.addEventListener('beforeunload', function() {
        window.scrollTo(0, 0);
    });
})();