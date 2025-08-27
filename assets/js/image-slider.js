// Reality Lab Image Slider - Isolated from Bootstrap
$(document).ready(function() {
    // Use more specific selectors to avoid Bootstrap conflicts
    var sliderImages = $('.image-slider .slider-image');
    var researchTabs = $('.research-tabs .research-tab');
    var currentIndex = 0;
    var realityLabSlideInterval = null; // Unique variable name
    
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
    
    function startRealityLabSlider() {
        // Clear existing timer with unique name
        if (realityLabSlideInterval) {
            clearInterval(realityLabSlideInterval);
            realityLabSlideInterval = null;
        }
        // Start new timer with exact 4500ms interval
        realityLabSlideInterval = setInterval(nextSlide, 4500);
    }
    
    // Initialize
    showSlide(0);
    startRealityLabSlider();
    
    // Tab click handler with namespace
    researchTabs.off('click.realitylab').on('click.realitylab', function() {
        var clickedIndex = parseInt($(this).data('index'), 10);
        
        // Show clicked slide
        showSlide(clickedIndex);
        
        // Restart timer from current position
        startRealityLabSlider();
    });
});