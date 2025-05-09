// Initialize Owl Carousel for sliders
$(document).ready(function(){
    if ($('.owl-carousel').length) {
        $('.owl-carousel').owlCarousel({
            loop: true,
            margin: 10,
            nav: true,
            responsive: {
                0: { items: 1 },
                600: { items: 3 },
                1000: { items: 5 }
            }
        });
    }

    // Get CSRF token from cookie
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    // Function to handle cart operations
    function handleCartOperation(url, productId) {
        console.log('Handling cart operation:', url, 'for product:', productId);
        
        if (!productId) {
            console.error('Product ID not found');
            return;
        }

        $.ajax({
            url: url,
            type: 'POST',
            headers: {
                'X-CSRFToken': csrftoken
            },
            data: {
                prod_id: productId
            },
            success: function(data) {
                console.log('Cart operation response:', data);
                try {
                    if (typeof data === 'string') {
                        data = JSON.parse(data);
                    }
                    
                    if (data.status === 'success') {
                        const cartItem = $(`#cart-item-${productId}`);
                        
                        if (data.quantity === 0 || url === '/removecart/') {
                            // Remove the item from the cart
                            cartItem.fadeOut(300, function() {
                                $(this).remove();
                                // Update cart totals after removal
                                $('#amount').text('$' + data.amount);
                                $('#totalamount').text('$' + data.totalamount);
                                
                                // If cart is empty, reload the page
                                if ($('.cart-item').length === 0) {
                                    location.reload();
                                }
                            });
                        } else {
                            // Update quantity display
                            $(`#quantity-${productId}`).text(data.quantity);
                            cartItem.find('.quantity-controls span.mx-2').text(data.quantity);
                            
                            // Update total for the specific product
                            $(`#total-${productId}`).text('$' + data.total);
                            
                            // Update cart totals
                            $('#amount').text('$' + data.amount);
                            $('#totalamount').text('$' + data.totalamount);
                        }
                    } else {
                        console.error('Error:', data.message || 'Unknown error occurred');
                    }
                } catch (e) {
                    console.error('Error parsing response:', e);
                }
            },
            error: function(xhr, status, error) {
                console.error('AJAX Error:', error);
                console.error('Status:', status);
                console.error('Response:', xhr.responseText);
            }
        });
    }

    // Plus Cart
    $(document).on('click', '.plus-cart', function(e) {
        e.preventDefault();
        const productId = $(this).data('product-id');
        console.log('Plus cart clicked for product:', productId);
        handleCartOperation('/pluscart/', productId);
    });

    // Minus Cart
    $(document).on('click', '.minus-cart', function(e) {
        e.preventDefault();
        const productId = $(this).data('product-id');
        console.log('Minus cart clicked for product:', productId);
        handleCartOperation('/minuscart/', productId);
    });

    // Remove Cart
    $(document).on('click', '.remove-cart', function(e) {
        e.preventDefault();
        const productId = $(this).data('product-id');
        console.log('Remove cart clicked for product:', productId);
        handleCartOperation('/removecart/', productId);
    });
});   