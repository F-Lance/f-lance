// main.js

// Handle popup open/close
document.addEventListener("DOMContentLoaded", () => {
    const openBtn = document.getElementById('openPopup');
    const closeBtn = document.getElementById('closePopup');
    const popupForm = document.getElementById('popupForm');
    const formBox = document.getElementById('formBox');
    const serviceForm = document.getElementById('serviceForm');
    const successMsg = document.getElementById('successMsg');
    //open popup
    if (openBtn) {
        openBtn.addEventListener('click', () => {
            popupForm.classList.remove('hidden');
            setTimeout(() => {
                formBox.classList.remove('scale-90', 'opacity-0');
                formBox.classList.add('scale-100', 'opacity-100');
            }, 10);
        });
    }
    // close popup
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            formBox.classList.remove('scale-100', 'opacity-100');
            formBox.classList.add('scale-90', 'opacity-0');
            setTimeout(() => {
                popupForm.classList.add('hidden');
                serviceForm.reset();
                successMsg.classList.add('hidden');
            }, 300);
        });
    }
    // form submission handler
    if (serviceForm) {
        serviceForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(serviceForm);
            const response = await fetch('/contact', {
                method: 'POST',
                body: formData
            });
            if (response.ok) {
                successMsg.classList.remove('hidden');
                serviceForm.reset();
                setTimeout(() => { closeBtn.click(); }, 1500);
            } else {
                alert('Error submitting form. Please try again.');
            }
        });
    }

    // Loader fade-out logic
    const loader = document.getElementById('loader-screen');
    if (loader) {
        setTimeout(() => {
            loader.classList.add('opacity-0', 'pointer-events-none');
            setTimeout(() => loader.remove(), 500);
        }, 1000);
    }
});
