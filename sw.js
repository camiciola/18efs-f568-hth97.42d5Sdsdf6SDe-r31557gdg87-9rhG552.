// Service Worker per gestire le notifiche push
self.addEventListener('install', event => {
    console.log('Service Worker installato');
    self.skipWaiting();
});

self.addEventListener('activate', event => {
    console.log('Service Worker attivato');
    event.waitUntil(clients.claim());
});

// Gestisce le notifiche push
self.addEventListener('push', event => {
    const data = event.data ? event.data.json() : {};
    const title = data.title || 'Nuova Notizia';
    const options = {
        body: data.body || 'Clicca per leggere',
        icon: 'icon-192.png',
        badge: 'icon-192.png',
        vibrate: [200, 100, 200],
        data: {
            url: data.url || '/'
        }
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

// Quando l'utente clicca sulla notifica
self.addEventListener('notificationclick', event => {
    event.notification.close();
    event.waitUntil(
        clients.openWindow(event.notification.data.url)
    );
});
