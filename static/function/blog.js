document.addEventListener("DOMContentLoaded", function() {
    const pic = document.getElementById('profile-circle');
    const dropdown = document.getElementById('dropdown');

    pic.addEventListener('click', function(event) {
        event.stopPropagation();
        dropdown.classList.toggle('show');
    });
    document.addEventListener('click', function(event) {
        if (!dropdown.contains(event.target) && event.target !== pic) {
            dropdown.classList.remove('show');
        }
    });
});

function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
}
document.addEventListener("DOMContentLoaded", function() {
    const toggleModeBtn = document.getElementById('toggle-mode-btn');

    toggleModeBtn.addEventListener('click', function() {
        document.body.classList.toggle('dark-mode');
    });
});



function submitForm() {
    document.getElementById("image-form").submit();
}