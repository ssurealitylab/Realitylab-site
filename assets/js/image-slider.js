// Image Slider with Tab Click functionality
$(document).ready(function() {
    var sliderImages = $('.slider-image');
    var researchTabs = $('.research-tab');
    var currentIndex = 0;
    var autoSlideInterval = null;
    var isUserInteracting = false;
    
    if (sliderImages.length === 0) return;
    
    function showSlide(index) {
        // Remove active from all images and tabs
        sliderImages.removeClass('active');
        researchTabs.removeClass('active');
        
        // Add active to current image and tab
        if (sliderImages.eq(index).length) {
            sliderImages.eq(index).addClass('active');
        }
        if (researchTabs.eq(index).length) {
            researchTabs.eq(index).addClass('active');
        }
        
        currentIndex = index;
    }
    
    function nextSlide() {
        if (!isUserInteracting) {
            currentIndex = (currentIndex + 1) % sliderImages.length;
            showSlide(currentIndex);
        }
    }
    
    function startAutoSlide() {
        // Clear any existing interval first
        if (autoSlideInterval) {
            clearInterval(autoSlideInterval);
            autoSlideInterval = null;
        }
        
        // Only start if user is not interacting
        if (!isUserInteracting) {
            autoSlideInterval = setInterval(nextSlide, 3000); // 3 seconds
        }
    }
    
    function stopAutoSlide() {
        if (autoSlideInterval) {
            clearInterval(autoSlideInterval);
            autoSlideInterval = null;
        }
    }
    
    // Initialize first slide
    showSlide(0);
    
    // Start auto-advance
    startAutoSlide();
    
    // Add click handlers to research tabs
    researchTabs.on('click', function() {
        var clickedIndex = $(this).data('index');
        
        // Set user interaction flag
        isUserInteracting = true;
        
        // Stop auto-advance completely
        stopAutoSlide();
        
        // Show clicked slide
        showSlide(clickedIndex);
        
        // Resume auto-advance after 5 seconds
        setTimeout(function() {
            isUserInteracting = false;
            startAutoSlide();
        }, 5000);
    });
});