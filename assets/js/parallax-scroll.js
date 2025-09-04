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
        
        // Find the actual image element position, not the container
        var imageSlider = masthead.querySelector('.image-slider');
        var introText = masthead.querySelector('.intro-text');
        var absoluteImageTop = mastheadTop + mastheadHeight * 0.5; // Default fallback
        
        // Get the position where we want the fade to start - after the intro text
        if (introText) {
            var introRect = introText.getBoundingClientRect();
            // Use the bottom of intro text as the key reference point
            absoluteImageTop = introRect.bottom + scrollY;
        } else if (imageSlider) {
            var sliderRect = imageSlider.getBoundingClientRect();
            absoluteImageTop = sliderRect.top + scrollY;
        }
        
        // Calculate when to start fading - trigger much earlier, above the images
        var fadeStartPoint = absoluteImageTop - windowHeight * 0.8; // Start fade well before image appears
        var fadeDistance = windowHeight * 0.6; // Shorter distance for quicker fade
        
        // Calculate smooth scroll progress - ensure initial state shows content clearly
        var scrollProgress = 0;
        if (scrollY >= fadeStartPoint && scrollY > 100) { // Add minimum scroll threshold
            scrollProgress = Math.min((scrollY - fadeStartPoint) / fadeDistance, 1);
        }
        
        // Apply easing function for smoother transitions
        var easedProgress = scrollProgress * scrollProgress * (3 - 2 * scrollProgress); // Smoothstep function
        
        // Calculate parallax effects with smoother curves and safer initial values
        var translateY = scrollY * 0.3; // Slower parallax for stability
        var blur = easedProgress * 8; // Reduced blur for better visibility
        var opacity = Math.max(1 - easedProgress * 0.9, 0.1); // Keep minimum opacity for visibility
        var scale = Math.max(1 - easedProgress * 0.05, 0.95); // Less aggressive scaling
        
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
        if (scrollY > 50) { // Log more frequently for debugging
            console.log(`ScrollY: ${scrollY}, ImageTop: ${absoluteImageTop}, FadeStart: ${fadeStartPoint.toFixed(0)}, Progress: ${easedProgress.toFixed(2)}, WindowHeight: ${windowHeight}`);
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