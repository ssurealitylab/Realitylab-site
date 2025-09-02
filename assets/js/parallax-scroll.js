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
        var windowHeight = window.innerHeight;
        
        // Get masthead position relative to document
        var mastheadRect = masthead.getBoundingClientRect();
        var mastheadTop = mastheadRect.top + scrollY;
        var mastheadHeight = mastheadRect.height;
        
        // Find the image slider position more accurately
        var imageSlider = masthead.querySelector('.image-slider');
        var absoluteImageTop = mastheadTop + mastheadHeight * 0.6; // Default fallback
        
        if (imageSlider) {
            var sliderRect = imageSlider.getBoundingClientRect();
            // Get the ACTUAL top position of the image slider
            absoluteImageTop = sliderRect.top + scrollY;
        }
        
        // Calculate when to start fading based on EXACTLY when image top reaches viewport top
        var fadeStartPoint = absoluteImageTop - windowHeight * 0.1; // Start fade just before image top hits viewport top
        var fadeDistance = windowHeight * 1.2; // Fade over 1.2 screen heights for smoother effect
        
        // Calculate smooth scroll progress
        var scrollProgress = 0;
        if (scrollY >= fadeStartPoint) {
            scrollProgress = Math.min((scrollY - fadeStartPoint) / fadeDistance, 1);
        }
        
        // Apply easing function for smoother transitions
        var easedProgress = scrollProgress * scrollProgress * (3 - 2 * scrollProgress); // Smoothstep function
        
        // Calculate parallax effects with smoother curves
        var translateY = scrollY * 0.4; // Slightly slower parallax
        var blur = easedProgress * 12; // More blur for better effect
        var opacity = Math.max(1 - easedProgress * 1.1, 0); // Smoother fade out
        var scale = Math.max(1 - easedProgress * 0.08, 0.92); // Slightly more scale
        
        // Apply transforms with hardware acceleration
        var transform = `translate3d(0, ${translateY}px, 0) scale(${scale})`;
        var filter = `blur(${blur}px)`;
        
        // Apply styles
        parallaxContainer.style.transform = transform;
        parallaxContainer.style.filter = filter;
        parallaxContainer.style.opacity = opacity;
        parallaxContainer.style.willChange = 'transform, filter, opacity'; // Optimize for animations
        
        // Add class for additional styling when scrolled
        if (easedProgress > 0.02) {
            masthead.classList.add('scrolled');
        } else {
            masthead.classList.remove('scrolled');
        }
        
        // Debug log for troubleshooting
        if (easedProgress > 0) {
            console.log(`ScrollY: ${scrollY}, ImageTop: ${absoluteImageTop}, FadeStart: ${fadeStartPoint}, Progress: ${easedProgress.toFixed(2)}`);
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