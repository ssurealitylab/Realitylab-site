// Image Slider functionality
document.addEventListener('DOMContentLoaded', function() {
    const sliderImages = document.querySelectorAll('.slider-image');
    const sliderTitle = document.getElementById('sliderTitle');
    const sliderDescription = document.getElementById('sliderDescription');
    
    if (sliderImages.length === 0) return;
    
    let currentIndex = 0;
    
    function showSlide(index) {
        // Hide all images
        sliderImages.forEach((img, i) => {
            img.classList.remove('active');
        });
        
        // Show current image
        sliderImages[index].classList.add('active');
        
        // Update text content with fade effect
        const currentSlide = sliderImages[index];
        const title = currentSlide.dataset.title;
        const description = currentSlide.dataset.description;
        
        if (sliderTitle && sliderDescription) {
            // Fade out
            sliderTitle.style.opacity = '0';
            sliderDescription.style.opacity = '0';
            
            // Update content and fade in
            setTimeout(() => {
                sliderTitle.textContent = title;
                sliderDescription.textContent = description;
                sliderTitle.style.opacity = '1';
                sliderDescription.style.opacity = '1';
            }, 250);
        }
    }
    
    function nextSlide() {
        currentIndex = (currentIndex + 1) % sliderImages.length;
        showSlide(currentIndex);
    }
    
    // Initialize first slide
    showSlide(0);
    
    // Auto-advance slides every 3 seconds
    setInterval(nextSlide, 3000);
});