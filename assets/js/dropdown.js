function toggleDropdown(element) {
    const dropdownId = element.getAttribute('data-dropdown');
    const dropdown = document.getElementById(dropdownId);
    const chevron = element.querySelector('.fa-chevron-down');
    
    // Close all other dropdowns
    document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
        if (menu.id !== dropdownId) {
            menu.classList.remove('show');
            const otherChevron = document.querySelector(`[data-dropdown="${menu.id}"] .fa-chevron-down`);
            if (otherChevron) {
                otherChevron.style.transform = '';
            }
        }
    });
    
    // Toggle current dropdown
    if (dropdown) {
        const isShown = dropdown.classList.contains('show');
        
        if (isShown) {
            dropdown.classList.remove('show');
            chevron.style.transform = '';
        } else {
            dropdown.classList.add('show');
            chevron.style.transform = 'rotate(180deg)';
        }
    }
    
    return false; // Prevent default link behavior
}

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