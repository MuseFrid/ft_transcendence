/********************************* GESTION SPA *********************************/

async function loadPage(page) {
    await fetch('/' + page + '/', {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'  // Add this header to indicate an AJAX request
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.text();
        })
        .then(html => {
            document.getElementById('spa-content').innerHTML = html;
            window.history.pushState({}, '', '/' + page + '/');
            // If there are any specific scripts or functions to run for the page, you can call them here.
            // Example: if(page === 'page2') { initializePage2(); }
        })
        .catch(error => {
            console.error('There was a problem with the fetch operation:', error);
            // Optionally load an error page or show an error message
        });

    switch (page) {
        case 'friend':
            getElementFriend();
            break;
        case 'pong':
            getElementPong();
            break;
        case 'game':
            getElementGame();
            break;
        case 'settings':
            loadSettings();
            break;
        case 'profile':
            loadProfile();
            break;
        default:
            break;
    }
}

// window.onpopstate = function () {
//     // Handle the back/forward buttons properly
//     const path = window.location.pathname.replace(/^\/+|\/+$/g, ''); // Trim leading/trailing slashes
//     loadPage(path || 'index'); // Default to 'page1' if no path
// };