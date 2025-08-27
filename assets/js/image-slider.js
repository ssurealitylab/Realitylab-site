// Simple Image Slider with Tab Click functionality
$(document).ready(function() {
    var sliderImages = $('.slider-image');
    var researchTabs = $('.research-tab');
    var currentIndex = 0;
    var slideInterval;
    
    if (sliderImages.length === 0) return;
    
    function showSlide(index) {
        // Remove active from all
        sliderImages.removeClass('active');
        researchTabs.removeClass('active');
        
        // Add active to current
        sliderImages.eq(index).addClass('active');
        researchTabs.eq(index).addClass('active');
        
        currentIndex = index;
    }
    
    function nextSlide() {
        currentIndex = (currentIndex + 1) % sliderImages.length;
        showSlide(currentIndex);
    }
    
    function startSlider() {
        // Clear existing timer
        if (slideInterval) {
            clearInterval(slideInterval);
        }
        // Start new timer
        slideInterval = setInterval(nextSlide, 3000);
    }
    
    // Initialize
    showSlide(0);
    startSlider();
    
    // Tab click handler
    researchTabs.on('click', function() {
        var clickedIndex = $(this).data('index');
        
        // Show clicked slide
        showSlide(clickedIndex);
        
        // Restart timer from current position
        startSlider();
    });
});