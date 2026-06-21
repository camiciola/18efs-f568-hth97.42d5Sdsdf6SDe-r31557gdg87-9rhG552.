// Gestione della navigazione tra le tab
document.addEventListener('DOMContentLoaded', function() {
    const navButtons = document.querySelectorAll('.nav-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const filterChips = document.querySelectorAll('.chip');

    // Cambio tab
    navButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');
            
            // Rimuovi active da tutti
            navButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(tab => tab.classList.remove('active'));
            
            // Aggiungi active al selezionato
            this.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
        });
    });

    // Gestione filtri
    filterChips.forEach(chip => {
        chip.addEventListener('click', function() {
            filterChips.forEach(c => c.classList.remove('active'));
            this.classList.add('active');
            
            const filter = this.getAttribute('data-filter');
            console.log('Filtro selezionato:', filter);
            // Qui in futuro filtreremo le notizie
        });
    });

    // Pulsante refresh
    document.getElementById('btn-refresh').addEventListener('click', function() {
        console.log('Refresh notizie...');
        // Qui in futuro ricaricheremo le notizie
        alert('Funzione refresh in sviluppo');
    });

    // Gestione notifiche
    const toggleNotifications = document.getElementById('toggle-notifications');
    const toggleHotNews = document.getElementById('toggle-hot-news');

    toggleNotifications.addEventListener('change', function() {
        if (this.checked) {
            requestNotificationPermission();
        }
        localStorage.setItem('notifications', this.checked);
    });

    toggleHotNews.addEventListener('change', function() {
        localStorage.setItem('hotNews', this.checked);
    });

    // Carica impostazioni salvate
    toggleNotifications.checked = localStorage.getItem('notifications') !== 'false';
    toggleHotNews.checked = localStorage.getItem('hotNews') !== 'false';

    // Richiedi permesso notifiche
    if (toggleNotifications.checked) {
        requestNotificationPermission();
    }

    // Registra il Service Worker
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('sw.js')
            .then(reg => console.log('Service Worker registrato'))
            .catch(err => console.log('Errore Service Worker:', err));
    }
});

// Richiedi permesso per notifiche push
function requestNotificationPermission() {
    if ('Notification' in window) {
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                console.log('Permessi notifiche concessi');
                // Qui in futuro salveremo il token per Firebase
            }
        });
    }
}

// Funzione per mostrare una notizia (da implementare con i dati reali)
function showNews(newsData) {
    // newsData sarà un array di oggetti con: title, summary, link, category, date
    console.log('Mostra notizie:', newsData);
}
