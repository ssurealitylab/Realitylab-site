// Force scroll to top on page load
(function() {
    'use strict';
    
    function scrollToTop() {
        // Force scroll to top immediately
        if (window.scrollTo) {
            window.scrollTo(0, 0);
        }
        
        // Also set scroll position directly
        document.documentElement.scrollTop = 0;
        document.body.scrollTop = 0;
        
        // Apply smooth behavior after initial reset
        setTimeout(function() {
            document.documentElement.style.scrollBehavior = 'smooth';
        }, 100);
    }
    
    // Execute immediately
    scrollToTop();
    
    // Execute when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', scrollToTop);
    }
    
    // Execute when page is fully loaded
    window.addEventListener('load', scrollToTop);
    
    // Execute on page show (for back button)
    window.addEventListener('pageshow', scrollToTop);
})();