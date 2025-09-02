// Reality Lab Image Slider - Pure JS Implementation
(function() {
    'use strict';
    
    var currentIndex = 0;
    var sliderImages = null;
    var researchTabs = null;
    var slideTimer = null;
    var SLIDE_INTERVAL = 7000; // 7 seconds exactly
    
    function log(message) {
        console.log('[RealityLab Slider]', new Date().toISOString(), message);
    }
    
    function initializeElements() {
        sliderImages = document.querySelectorAll('.image-slider .slider-image');
        researchTabs = document.querySelectorAll('.research-tabs .research-tab');
        
        log('Found ' + sliderImages.length + ' images and ' + researchTabs.length + ' tabs');
        
        if (sliderImages.length === 0 || researchTabs.length === 0) {
            log('No slider elements found - exiting');
            return false;
        }
        return true;
    }
    
    function showSlide(index) {
        log('Showing slide ' + index);
        
        // Remove active class from all
        for (var i = 0; i < sliderImages.length; i++) {
            sliderImages[i].classList.remove('active');
        }
        for (var j = 0; j < researchTabs.length; j++) {
            researchTabs[j].classList.remove('active');
        }
        
        // Add active to current
        if (sliderImages[index]) {
            sliderImages[index].classList.add('active');
        }
        if (researchTabs[index]) {
            researchTabs[index].classList.add('active');
            
            // Auto-scroll the active tab into view
            scrollTabIntoView(researchTabs[index]);
        }
        
        currentIndex = index;
    }
    
    function scrollTabIntoView(activeTab) {
        var tabsContainer = document.querySelector('.research-tabs');
        if (!tabsContainer || !activeTab) return;
        
        var containerRect = tabsContainer.getBoundingClientRect();
        var tabRect = activeTab.getBoundingClientRect();
        var scrollLeft = tabsContainer.scrollLeft;
        
        // Calculate if tab is visible
        var tabLeftVisible = tabRect.left >= containerRect.left;
        var tabRightVisible = tabRect.right <= containerRect.right;
        
        if (!tabLeftVisible || !tabRightVisible) {
            // Calculate scroll position to center the active tab
            var tabOffset = activeTab.offsetLeft;
            var tabWidth = activeTab.offsetWidth;
            var containerWidth = tabsContainer.offsetWidth;
            
            var scrollTo = tabOffset - (containerWidth / 2) + (tabWidth / 2);
            
            // Smooth scroll to position
            tabsContainer.scrollTo({
                left: Math.max(0, scrollTo),
                behavior: 'smooth'
            });
        }
    }
    
    function nextSlide() {
        currentIndex = (currentIndex + 1) % sliderImages.length;
        log('Auto advancing to slide ' + currentIndex);
        showSlide(currentIndex);
    }
    
    function startTimer() {
        if (slideTimer) {
            clearInterval(slideTimer);
            slideTimer = null;
        }
        
        log('Starting timer with ' + SLIDE_INTERVAL + 'ms interval');
        slideTimer = setInterval(nextSlide, SLIDE_INTERVAL);
    }
    
    function handleTabClick(event) {
        var clickedIndex = parseInt(event.target.closest('.research-tab').getAttribute('data-index'), 10);
        log('Tab clicked: ' + clickedIndex);
        
        showSlide(clickedIndex);
        startTimer(); // Restart timer
    }
    
    function init() {
        if (!initializeElements()) {
            return;
        }
        
        // Add click listeners to tabs
        for (var i = 0; i < researchTabs.length; i++) {
            researchTabs[i].addEventListener('click', handleTabClick);
        }
        
        // Initialize first slide
        showSlide(0);
        
        // Start timer
        startTimer();
        
        log('Initialization complete');
    }
    
    // Wait for DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();