document.addEventListener('DOMContentLoaded', function () {
    // 1. Toast Notification Auto-Dismiss (3 seconds)
    const toastItems = document.querySelectorAll('.toast-item');
    toastItems.forEach(function (toast) {
        setTimeout(function () {
            toast.classList.add('toast-exit');
            setTimeout(function () {
                if (toast.parentNode) {
                    toast.remove();
                }
            }, 250);
        }, 3000);
    });

    // 2. Staggered Row Entry Delays for Tables (~50ms apart)
    const tableRows = document.querySelectorAll('.products-table tbody tr');
    tableRows.forEach(function (row, index) {
        row.style.animationDelay = (index * 50) + 'ms';
    });

    // 3. Mobile Sidebar Toggle
    const mobileToggle = document.getElementById('mobile-toggle');
    const sidebar = document.querySelector('.sidebar');
    if (mobileToggle && sidebar) {
        mobileToggle.addEventListener('click', function () {
            sidebar.classList.toggle('active');
        });
    }
});
