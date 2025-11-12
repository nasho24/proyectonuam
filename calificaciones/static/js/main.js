// Funciones generales para NUAM
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar tooltips de Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // Animaciones para cards
    const cards = document.querySelectorAll('.nuam-card');
    cards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 100);
    });

    // Confirmación para eliminaciones
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('¿Está seguro de que desea eliminar este registro?')) {
                e.preventDefault();
            }
        });
    });
});

// Función para mostrar notificaciones
function showNotification(message, type = 'success') {
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.querySelector('.container').prepend(alert);
    
    setTimeout(() => {
        alert.remove();
    }, 5000);
}

// ===== NAVBAR HORIZONTAL - MENÚ HAMBURGUESA =====
document.addEventListener('DOMContentLoaded', function() {
    const toggler = document.getElementById('navbarToggler');
    const navbarNav = document.getElementById('navbarNav');
    const navUser = document.querySelector('.nav-user');
    
    if (toggler && navbarNav) {
        toggler.addEventListener('click', function() {
            navbarNav.classList.toggle('active');
            // También toggle para el usuario en móvil
            if (window.innerWidth <= 768 && navUser) {
                navUser.classList.toggle('active');
            }
        });
        
        // Cerrar menú al hacer clic en un link
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                if (window.innerWidth <= 768) {
                    navbarNav.classList.remove('active');
                    if (navUser) {
                        navUser.classList.remove('active');
                    }
                }
            });
        });
        
        // Cerrar menú al redimensionar la ventana
        window.addEventListener('resize', function() {
            if (window.innerWidth > 768) {
                navbarNav.classList.remove('active');
                if (navUser) {
                    navUser.classList.remove('active');
                }
            }
        });
        
        // Cerrar menú al hacer clic fuera de él
        document.addEventListener('click', function(event) {
            if (window.innerWidth <= 768) {
                const isClickInsideNav = navbarNav.contains(event.target);
                const isClickOnToggler = toggler.contains(event.target);
                
                if (!isClickInsideNav && !isClickOnToggler && navbarNav.classList.contains('active')) {
                    navbarNav.classList.remove('active');
                    if (navUser) {
                        navUser.classList.remove('active');
                    }
                }
            }
        });
    }
});

// ===== EFECTO DE SCROLL SUAVE PARA NAVBAR =====
window.addEventListener('scroll', function() {
    const navbar = document.querySelector('.nuam-navbar');
    if (navbar && window.scrollY > 50) {
        navbar.style.padding = '0.5rem 0';
        navbar.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.2)';
    } else if (navbar) {
        navbar.style.padding = '1rem 0';
        navbar.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
    }
});