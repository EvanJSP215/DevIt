
// Function to show the popup
function showPopup() {
    document.getElementById('popupContainer').style.display = 'block';
}

// Function to hide the popup
function hidePopup() {
    document.getElementById('popupContainer').style.display = 'none';
}

// Function to redirect to the blog page
function redirectToBlogPage() {
    window.location.href = '/blogPage';
}

function redirectToLoginPage() {
    window.location.href = '/login';
}

// Add event listener to the button
document.getElementById('triggerBtn').addEventListener('click', function(event) {
    event.preventDefault(); // Prevent default form submission
    showPopup(); // Show the popup
});