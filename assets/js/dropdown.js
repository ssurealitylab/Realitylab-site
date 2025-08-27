// Enhanced dropdown functionality for better mobile and accessibility support
document.addEventListener('DOMContentLoaded', function() {
    const dropdownToggles = document.querySelectorAll('.dropdown-toggle');
    
    dropdownToggles.forEach(toggle => {
        // Add click support for mobile
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Only use JavaScript toggle on mobile/tablet screens
            if (window.innerWidth < 992) {
                const dropdownId = this.getAttribute('data-dropdown');
                const dropdown = document.getElementById(dropdownId);
                
                if (dropdown) {
                    const isShown = dropdown.classList.contains('show');
                    
                    // Close all other dropdowns first
                    document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
                        if (menu.id !== dropdownId) {
                            menu.classList.remove('show');
                        }
                    });
                    
                    // Toggle current dropdown
                    if (isShown) {
                        dropdown.classList.remove('show');
                    } else {
                        dropdown.classList.add('show');
                    }
                }
            }
        });
    });
});

// Close dropdowns when clicking outside
document.addEventListener('click', function(event) {
    if (!event.target.closest('.dropdown')) {
        document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
            menu.classList.remove('show');
        });
        document.querySelectorAll('.fa-chevron-down').forEach(chevron => {
            chevron.style.transform = '';
        });
    }
});