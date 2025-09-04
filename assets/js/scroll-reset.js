// Force scroll to top on page load - Enhanced version
(function() {
    'use strict';
    
    function forceScrollToTop() {
        // Disable smooth scrolling temporarily
        var originalBehavior = document.documentElement.style.scrollBehavior;
        document.documentElement.style.scrollBehavior = 'auto';
        
        // Force scroll to top using multiple methods
        window.scrollTo(0, 0);
        document.documentElement.scrollTop = 0;
        document.body.scrollTop = 0;
        
        // Also reset any CSS scroll-margin or scroll-padding
        document.body.style.scrollMarginTop = '0';
        document.documentElement.style.scrollMarginTop = '0';
        
        // Restore smooth behavior after a delay
        setTimeout(function() {
            document.documentElement.style.scrollBehavior = originalBehavior || 'smooth';
        }, 200);
    }
    
    // Execute immediately and repeatedly to ensure it takes effect
    forceScrollToTop();
    setTimeout(forceScrollToTop, 10);
    setTimeout(forceScrollToTop, 50);
    setTimeout(forceScrollToTop, 100);
    
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