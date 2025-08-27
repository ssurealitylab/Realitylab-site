// Image Slider with Tab Click functionality
$(document).ready(function() {
    var sliderImages = $('.slider-image');
    var researchTabs = $('.research-tab');
    var currentIndex = 0;
    var autoSlideInterval;
    
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
        currentIndex = (currentIndex + 1) % sliderImages.length;
        showSlide(currentIndex);
    }
    
    function startAutoSlide() {
        autoSlideInterval = setInterval(nextSlide, 3000);
    }
    
    function stopAutoSlide() {
        if (autoSlideInterval) {
            clearInterval(autoSlideInterval);
        }
    }
    
    // Initialize first slide
    showSlide(0);
    
    // Start auto-advance
    startAutoSlide();
    
    // Add click handlers to research tabs
    researchTabs.on('click', function() {
        var clickedIndex = $(this).data('index');
        
        // Stop auto-advance temporarily
        stopAutoSlide();
        
        // Show clicked slide
        showSlide(clickedIndex);
        
        // Restart auto-advance after 5 seconds
        setTimeout(startAutoSlide, 5000);
    });
});