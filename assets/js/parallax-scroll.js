// GitHub-style Parallax Scrolling Effect
(function() {
    'use strict';
    
    var masthead = null;
    var parallaxContainer = null;
    var isInitialized = false;
    
    function log(message) {
        console.log('[Parallax Scroll]', new Date().toISOString(), message);
    }
    
    function initializeElements() {
        masthead = document.querySelector('header.masthead');
        if (!masthead) {
            log('Masthead not found');
            return false;
        }
        
        // Wrap masthead content in parallax container if not already wrapped
        if (!masthead.querySelector('.parallax-container')) {
            var container = masthead.querySelector('.container');
            if (container) {
                var parallaxDiv = document.createElement('div');
                parallaxDiv.className = 'parallax-container';
                
                // Move container inside parallax div
                masthead.insertBefore(parallaxDiv, container);
                parallaxDiv.appendChild(container);
                
                parallaxContainer = parallaxDiv;
                log('Created parallax container');
            }
        } else {
            parallaxContainer = masthead.querySelector('.parallax-container');
        }
        
        return parallaxContainer !== null;
    }
    
    function handleScroll() {
        if (!parallaxContainer || !masthead) return;
        
        var scrollY = window.pageYOffset || document.documentElement.scrollTop;
        var mastheadHeight = masthead.offsetHeight;
        var windowHeight = window.innerHeight;
        
        // Calculate scroll progress (0 to 1)
        var scrollProgress = Math.min(scrollY / mastheadHeight, 1);
        
        // Calculate parallax effects
        var translateY = scrollY * 0.5; // Move slower than scroll (parallax effect)
        var blur = scrollProgress * 8; // Increase blur as scrolling
        var opacity = Math.max(1 - scrollProgress * 1.2, 0); // Fade out
        var scale = Math.max(1 - scrollProgress * 0.1, 0.9); // Slightly scale down
        
        // Apply transforms
        var transform = `translate3d(0, ${translateY}px, 0) scale(${scale})`;
        var filter = `blur(${blur}px)`;
        
        // Apply styles
        parallaxContainer.style.transform = transform;
        parallaxContainer.style.filter = filter;
        parallaxContainer.style.opacity = opacity;
        
        // Add class for additional styling when scrolled
        if (scrollProgress > 0.1) {
            masthead.classList.add('scrolled');
        } else {
            masthead.classList.remove('scrolled');
        }
    }
    
    function init() {
        if (isInitialized) return;
        
        if (!initializeElements()) {
            log('Failed to initialize elements');
            return;
        }
        
        // Add scroll listener with throttling
        var ticking = false;
        function requestTick() {
            if (!ticking) {
                requestAnimationFrame(handleScroll);
                ticking = true;
                setTimeout(function() { ticking = false; }, 16); // ~60fps
            }
        }
        
        window.addEventListener('scroll', requestTick, { passive: true });
        window.addEventListener('resize', requestTick, { passive: true });
        
        // Initial call
        handleScroll();
        
        isInitialized = true;
        log('Parallax scroll initialized');
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();