/**
 * School Portal & Library System - Main JavaScript
 * Fully responsive & adaptive for mobile, tablet, and desktop
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Sidebar Elements
  const sidebar = document.getElementById('sidebar');
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebarCloseBtn = document.getElementById('sidebarCloseBtn');
  const sidebarBackdrop = document.getElementById('sidebarBackdrop');
  const mobileMenuBtn = document.getElementById('mobileMenuBtn');

  // Desktop Collapse / Expand Toggle
  if (sidebar && sidebarToggle) {
    const isCollapsed = localStorage.getItem('school_sidebar_collapsed') === 'true';
    if (isCollapsed && window.innerWidth > 992) {
      sidebar.classList.add('collapsed');
    }

    sidebarToggle.addEventListener('click', () => {
      if (window.innerWidth > 992) {
        sidebar.classList.toggle('collapsed');
        const collapsedNow = sidebar.classList.contains('collapsed');
        localStorage.setItem('school_sidebar_collapsed', collapsedNow);
      }
    });
  }

  // Helper functions for mobile drawer
  function openMobileSidebar() {
    if (!sidebar) return;
    sidebar.classList.add('mobile-open');
    if (sidebarBackdrop) sidebarBackdrop.classList.add('active');
    document.body.classList.add('drawer-open');
  }

  function closeMobileSidebar() {
    if (!sidebar) return;
    sidebar.classList.remove('mobile-open');
    if (sidebarBackdrop) sidebarBackdrop.classList.remove('active');
    document.body.classList.remove('drawer-open');
  }

  if (mobileMenuBtn) {
    mobileMenuBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (sidebar && sidebar.classList.contains('mobile-open')) {
        closeMobileSidebar();
      } else {
        openMobileSidebar();
      }
    });
  }

  if (sidebarCloseBtn) {
    sidebarCloseBtn.addEventListener('click', closeMobileSidebar);
  }

  if (sidebarBackdrop) {
    sidebarBackdrop.addEventListener('click', closeMobileSidebar);
  }

  // 2. Public Mobile Drawer (for logged-out users)
  const publicMenuBtn = document.getElementById('publicMenuBtn');
  const publicMobileDrawer = document.getElementById('publicMobileDrawer');
  const publicDrawerBackdrop = document.getElementById('publicDrawerBackdrop');
  const publicDrawerCloseBtn = document.getElementById('publicDrawerCloseBtn');

  function openPublicDrawer() {
    if (publicMobileDrawer) publicMobileDrawer.classList.add('open');
    if (publicDrawerBackdrop) publicDrawerBackdrop.classList.add('active');
    document.body.classList.add('drawer-open');
  }

  function closePublicDrawer() {
    if (publicMobileDrawer) publicMobileDrawer.classList.remove('open');
    if (publicDrawerBackdrop) publicDrawerBackdrop.classList.remove('active');
    document.body.classList.remove('drawer-open');
  }

  if (publicMenuBtn) {
    publicMenuBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      openPublicDrawer();
    });
  }
  if (publicDrawerCloseBtn) {
    publicDrawerCloseBtn.addEventListener('click', closePublicDrawer);
  }
  if (publicDrawerBackdrop) {
    publicDrawerBackdrop.addEventListener('click', closePublicDrawer);
  }

  // 3. Close drawers and modals on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeMobileSidebar();
      closePublicDrawer();
      document.querySelectorAll('.modal-overlay.open').forEach(modal => {
        modal.classList.remove('open');
      });
    }
  });

  // Handle window resize cleanly
  window.addEventListener('resize', () => {
    if (window.innerWidth > 992) {
      closeMobileSidebar();
      closePublicDrawer();
    }
  });

  // 4. Sidebar Live Search
  const sidebarSearch = document.getElementById('sidebarSearch');
  if (sidebarSearch) {
    sidebarSearch.addEventListener('input', (e) => {
      const term = e.target.value.toLowerCase().trim();
      const navLinks = document.querySelectorAll('.sidebar-nav .nav-link');
      const groupTitles = document.querySelectorAll('.sidebar-nav .nav-group-title');

      navLinks.forEach(link => {
        const text = link.textContent.toLowerCase();
        if (text.includes(term)) {
          link.style.display = 'flex';
        } else {
          link.style.display = 'none';
        }
      });

      // Hide group headers if searching
      groupTitles.forEach(title => {
        title.style.display = term ? 'none' : 'block';
      });
    });
  }

  // 5. Modal Open/Close Controls
  document.querySelectorAll('[data-open-modal]').forEach(trigger => {
    trigger.addEventListener('click', (e) => {
      e.preventDefault();
      const modalId = trigger.getAttribute('data-open-modal');
      const modal = document.getElementById(modalId);
      if (modal) {
        modal.classList.add('open');
        document.body.classList.add('modal-open');
      }
    });
  });

  document.querySelectorAll('[data-close-modal]').forEach(btn => {
    btn.addEventListener('click', () => {
      const modal = btn.closest('.modal-overlay');
      if (modal) {
        modal.classList.remove('open');
        document.body.classList.remove('modal-open');
      }
    });
  });

  // Close modal on backdrop click
  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) {
        overlay.classList.remove('open');
        document.body.classList.remove('modal-open');
      }
    });
  });

  // 6. Active Tab horizontal scroll centering
  const activeTab = document.querySelector('.nav-tabs .tab-btn.active');
  if (activeTab) {
    const parent = activeTab.closest('.nav-tabs');
    if (parent && parent.scrollWidth > parent.clientWidth) {
      activeTab.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
    }
  }

  // 7. Auto dismiss alerts after 6 seconds
  const alerts = document.querySelectorAll('.alert-box');
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-10px)';
      setTimeout(() => alert.remove(), 400);
    }, 6000);
  });
});
