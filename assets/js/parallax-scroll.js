// GitHub-style Parallax Scrolling Effect
(function() {
    'use strict';
    
    var masthead = null;
    var parallaxContainer = null;
    var isInitialized = false;
    var parallaxEnabled = false; // Start with parallax disabled
    
    function log(message) {
        console.log('[Parallax Scroll]', new Date().toISOString(), message);
    }
    
    function initializeElements() {
        masthead = document.querySelector('header.masthead');
        if (!masthead) {
            log('Masthead not found');
            return false;
        }
        
        // Wrap ONLY the intro-text in parallax container, not the entire content
        if (!masthead.querySelector('.parallax-container')) {
            var introText = masthead.querySelector('.intro-text');
            if (introText) {
                var parallaxDiv = document.createElement('div');
                parallaxDiv.className = 'parallax-container';
                
                // Wrap only the intro-text, not the entire container
                introText.parentNode.insertBefore(parallaxDiv, introText);
                parallaxDiv.appendChild(introText);
                
                parallaxContainer = parallaxDiv;
                log('Created parallax container around intro-text only');
            }
        } else {
            parallaxContainer = masthead.querySelector('.parallax-container');
        }
        
        return parallaxContainer !== null;
    }
    
    function handleScroll() {
        if (!parallaxContainer || !masthead) return;
        
        var scrollY = window.pageYOffset || document.documentElement.scrollTop;
        
        // Enable parallax only after significant scroll or time delay
        if (!parallaxEnabled) {
            if (scrollY > 100) { // Enable after 100px scroll
                parallaxEnabled = true;
                log('Parallax enabled after scroll');
            } else {
                // Keep content fully visible while parallax is disabled
                parallaxContainer.style.transform = 'translate3d(0, 0, 0) scale(1)';
                parallaxContainer.style.filter = 'blur(0px)';
                parallaxContainer.style.opacity = '1';
                return; // Exit early, no parallax effects
            }
        }
        var windowHeight = window.innerHeight;
        
        // Get masthead position relative to document
        var mastheadRect = masthead.getBoundingClientRect();
        var mastheadTop = mastheadRect.top + scrollY;
        var mastheadHeight = mastheadRect.height;
        
        // Find the image slider container position - this is where we want fade to start
        var imageSliderContainer = masthead.querySelector('.image-slider-container');
        var absoluteImageTop = mastheadTop + mastheadHeight * 0.5; // Default fallback
        
        // Get the EXACT top position of the image container (not intro text bottom)
        if (imageSliderContainer) {
            var containerRect = imageSliderContainer.getBoundingClientRect();
            absoluteImageTop = containerRect.top + scrollY; // Use TOP of image container
            console.log('Image container top:', absoluteImageTop, 'ScrollY:', scrollY, 'Container top from viewport:', containerRect.top);
        }
        
        // Start fade earlier - when images are about to come into view from bottom
        var fadeStartPoint = absoluteImageTop - windowHeight * 0.7; // Trigger before images enter viewport
        var fadeDistance = windowHeight * 0.4; // Smooth fade over 40% of screen height
        
        // Calculate smooth scroll progress - ensure initial state shows content clearly
        var scrollProgress = 0;
        if (scrollY >= fadeStartPoint && scrollY > 200) { // Higher minimum scroll threshold to prevent initial fade
            scrollProgress = Math.min((scrollY - fadeStartPoint) / fadeDistance, 1);
        }
        
        // Apply easing function for smoother transitions
        var easedProgress = scrollProgress * scrollProgress * (3 - 2 * scrollProgress); // Smoothstep function
        
        // Calculate parallax effects with smoother curves and safer initial values
        var translateY = scrollY * 0.3; // Slower parallax for stability
        var blur = easedProgress * 8; // Reduced blur for better visibility
        
        // Ensure full visibility at page load - no fade until significant scroll
        var opacity = 1; // Default to full opacity
        if (scrollY > 150) { // Only start fading after 150px scroll
            opacity = Math.max(1 - easedProgress * 0.9, 0.1); // Keep minimum opacity for visibility
        }
        
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
        if (scrollY > 50 && scrollY % 50 < 10) { // Log every 50px of scroll
            console.log(`📊 ScrollY: ${scrollY}, ImageContainerTop: ${absoluteImageTop}, FadeStart: ${fadeStartPoint.toFixed(0)}, Progress: ${(easedProgress * 100).toFixed(1)}%, Opacity: ${opacity.toFixed(2)}`);
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
        
        // Ensure intro text is visible on initial load
        if (parallaxContainer) {
            parallaxContainer.style.transform = 'translate3d(0, 0, 0) scale(1)';
            parallaxContainer.style.filter = 'blur(0px)';
            parallaxContainer.style.opacity = '1';
        }
        
        // Enable parallax after 0.05 seconds as backup
        setTimeout(function() {
            if (!parallaxEnabled) {
                parallaxEnabled = true;
                log('Parallax enabled after time delay');
            }
        }, 50);
        
        // Initial call
        handleScroll();
        
        isInitialized = true;
        log('Parallax scroll initialized - intro text should be visible');
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();