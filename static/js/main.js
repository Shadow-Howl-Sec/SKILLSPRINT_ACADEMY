$(document).ready(function() {
    $('#registrationForm').on('submit', function(e) {
        e.preventDefault();
        const formData = {
            name: $('#name').val(),
            email: $('#email').val(),
            phone: $('#phone').val()
        };
        $.ajax({
            url: '/register',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(formData),
            success: function(response) {
                $('#formAlert').removeClass('d-none alert-danger').addClass('alert-success').attr('aria-live', 'polite').text('Registration successful!');
                document.getElementById('formAlert').scrollIntoView({behavior: 'smooth'});
            },
            error: function() {
                $('#formAlert').removeClass('d-none alert-success').addClass('alert-danger').attr('aria-live', 'assertive').text('Registration failed. Please try again.');
                document.getElementById('formAlert').scrollIntoView({behavior: 'smooth'});
            }
        });
    });
}); 