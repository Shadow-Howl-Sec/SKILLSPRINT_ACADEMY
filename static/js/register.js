$(document).ready(function() {
    // Pricing and discount logic (sync with HTML)
    const BASE_PRICE = 2499;
    // If discount already set in HTML, reuse it; otherwise, generate
    let discountPercent = window.discountPercent;
    let discountedPrice = window.discountedPrice;
    if (!discountPercent || !discountedPrice) {
        discountPercent = Math.floor(Math.random() * (54 - 48 + 1)) + 48;
        discountedPrice = Math.round(BASE_PRICE * (1 - discountPercent / 100));
    }
    $('#registrationForm').on('submit', function(e) {
        e.preventDefault();
        const slot = $('#slot_month').val() + ' ' + $('#slot_year').val();
        const formData = {
            name: $('#name').val(),
            mobile: $('#mobile').val(),
            college: $('#college').val(),
            year: $('#year').val(),
            branch: $('#branch').val(),
            domain: $('#domain').val(),
            slot: slot,
            email: $('#email').val()
        };
        // 1. Create Razorpay order
        $.ajax({
            url: '/create_order',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ amount: discountedPrice }), // Use discounted price
            success: function(orderData) {
                var options = {
                    key: orderData.key_id,
                    amount: orderData.amount,
                    currency: 'INR',
                    name: 'SkillSprint Academy',
                    description: 'Training Registration',
                    order_id: orderData.order_id,
                    handler: function (response) {
                        // 2. On payment success, send registration + payment info
                        formData.payment_id = response.razorpay_payment_id;
                        formData.order_id = response.razorpay_order_id;
                        $.ajax({
                            url: '/register',
                            type: 'POST',
                            contentType: 'application/json',
                            data: JSON.stringify(formData),
                            success: function(res) {
                                window.location.href = '/success';
                            },
                            error: function() {
                                $('#formAlert').removeClass('d-none alert-success').addClass('alert-danger').text('Registration failed. Please try again.');
                            }
                        });
                    },
                    prefill: {
                        name: formData.name,
                        email: formData.email,
                        contact: formData.mobile
                    },
                    theme: {
                        color: '#007bff'
                    }
                };
                var rzp = new Razorpay(options);
                rzp.open();
            },
            error: function() {
                $('#formAlert').removeClass('d-none alert-success').addClass('alert-danger').text('Could not initiate payment. Please try again.');
            }
        });
    });
}); 