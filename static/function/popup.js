document.addEventListener('DOMContentLoaded', function () {
    const popupContainer = document.getElementById('popupContainer');
    const yesButton = document.querySelector('.yes-button');
    const noButton = document.querySelector('.no-button');
    const closeButton = document.querySelector('.close-button');

    function showPopup() {
        popupContainer.style.display = 'block';
    }

    function hidePopup() {
        popupContainer.style.display = 'none';
    }

    yesButton.addEventListener('click', function () {
        document.getElementById('popupForm').submit(); // Submit the form for 'Yes'
    });

    noButton.addEventListener('click', function () {
        window.location.href = '/login'; // Redirect to Login Page for 'No'
    });

    function disableClickOutside(event) {
        if (!event.target.closest('.popup')) {
            event.stopPropagation();
        }
    }

    document.addEventListener('click', disableClickOutside);
});

