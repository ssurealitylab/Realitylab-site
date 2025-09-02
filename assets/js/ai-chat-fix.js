// Fix AI Chat functionality on all pages
document.addEventListener('DOMContentLoaded', function() {
    console.log('AI Chat fix script loaded');
    
    // Wait a bit for other scripts to load
    setTimeout(function() {
        // Find all AI Chat dropdown items
        const aiChatLinks = document.querySelectorAll('a.dropdown-item');
        
        aiChatLinks.forEach(function(link) {
            const linkText = link.textContent.trim();
            if (linkText.includes('AI Chat') || linkText.includes('Chat with AI')) {
                console.log('Found AI Chat link, adding click handler');
                
                link.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    console.log('AI Chat clicked, calling toggleChatbot');
                    
                    // Check if toggleChatbot exists
                    if (typeof window.toggleChatbot === 'function') {
                        window.toggleChatbot();
                    } else {
                        console.log('toggleChatbot not found, trying direct method');
                        // Direct method to show chatbot
                        const container = document.getElementById('chatbot-container');
                        const chatbotWindow = document.getElementById('chatbot-window');
                        
                        if (container && chatbotWindow) {
                            container.style.display = 'block';
                            chatbotWindow.style.display = 'flex';
                            console.log('Chatbot shown directly');
                        } else {
                            console.log('Chatbot elements not found');
                        }
                    }
                    
                    return false;
                });
            }
        });
        
        // Also fix Reality Lab logo click
        const logo = document.getElementById('reality-lab-logo');
        if (logo) {
            logo.addEventListener('click', function(e) {
                // Only prevent default if we're not on homepage
                if (window.location.pathname !== '/' && window.location.pathname !== '/Realitylab-site/') {
                    e.preventDefault();
                    window.location.href = '/Realitylab-site/';
                }
            });
        }
        
    }, 1000); // Wait 1 second for all scripts to load
});