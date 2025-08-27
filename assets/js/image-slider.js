// Test script
alert('JavaScript is working!');

$(document).ready(function() {
    alert('jQuery is ready!');
    
    // Simple test - change tab opacity every 3 seconds
    var tabs = $('.research-tab');
    var currentIndex = 0;
    
    setInterval(function() {
        // Remove active from all tabs
        tabs.removeClass('active');
        
        // Add active to current tab
        tabs.eq(currentIndex).addClass('active');
        
        // Change images too
        $('.slider-image').removeClass('active');
        $('.slider-image').eq(currentIndex).addClass('active');
        
        currentIndex = (currentIndex + 1) % tabs.length;
    }, 3000);
});