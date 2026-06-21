const NEWS_DATA_URL = 'news_data.json';

let currentTab = 'home';
let currentFilter = 'all';

document.addEventListener('DOMContentLoaded', function() {
    const navButtons = document.querySelectorAll('.nav-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const filterChips = document.querySelectorAll('.chip');

    // Cambio tab - RESETTA il filtro
    navButtons.forEach(button => {
        button.addEventListener('click', function() {
            currentTab = this.getAttribute('data-tab');
            currentFilter = 'all';
            
            navButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
            document.querySelector('.chip[data-filter="all"]').classList.add('active');
            
            this.classList.add('active');
            document.getElementById(currentTab).classList.add('active');
            
            loadAndDisplay();
        });
    });

    // Gestione filtri sottocategoria
    filterChips.forEach(chip => {
        chip.addEventListener('click', function() {
            document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
            this.classList.add('active');
            currentFilter = this.getAttribute('data-filter');
            loadAndDisplay();
        });
    });

    document.getElementById('btn-refresh').addEventListener('click', function() {
        loadAndDisplay();
    });

    const toggleNotifications = document.getElementById('toggle-notifications');
    const toggleHotNews = document.getElementById('toggle-hot-news');

    toggleNotifications.addEventListener('change', function() {
        if (this.checked) requestNotificationPermission();
        localStorage.setItem('notifications', this.checked);
    });

    toggleHotNews.addEventListener('change', function() {
        localStorage.setItem('hotNews', this.checked);
    });

    toggleNotifications.checked = localStorage.getItem('notifications') !== 'false';
    toggleHotNews.checked = localStorage.getItem('hotNews') !== 'false';

    if (toggleNotifications.checked) requestNotificationPermission();

    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('sw.js')
            .then(reg => console.log('Service Worker registrato'))
            .catch(err => console.log('Errore Service Worker:', err));
    }

    loadAndDisplay();
});

async function loadAndDisplay() {
    try {
        const response = await fetch(NEWS_DATA_URL + '?t=' + Date.now());
        if (!response.ok) throw new Error('HTTP ' + response.status);
        const data = await response.json();
        displayNews(data.news);
    } catch (error) {
        console.error('Errore:', error);
        showError(error.message);
    }
}

function displayNews(allNews) {
    if (currentTab === 'home') {
        displayHome(allNews);
    } else if (currentTab === 'ndrangheta') {
        displayNdrangheta(allNews);
    } else if (currentTab === 'mondo') {
        displayMondo(allNews);
    }
}

function displayHome(allNews) {
    // HOME: top news Italia + top news Mondo
    const newsItalia = allNews.filter(n => n.section === 'italia' || n.section === 'crime_italy');
    const newsMondo = allNews.filter(n => n.section === 'mondo');
    const breaking = allNews.filter(n => n.is_high_priority);
    
    displayNewsList('breaking-news', breaking.slice(0, 5));
    displayNewsList('top-news', [...newsItalia.slice(0, 5), ...newsMondo.slice(0, 5)].slice(0, 10));
}

function displayNdrangheta(allNews) {
    // NDRANGHETA: solo notizie section='ndrangheta'
    let news = allNews.filter(n => n.section === 'ndrangheta');
    
    if (currentFilter !== 'all') {
        news = news.filter(n => n.categories.includes(currentFilter));
    }
    
    displayNewsList('ndrangheta-news', news);
}

function displayMondo(allNews) {
    // MONDO: solo notizie section='mondo'
    let news = allNews.filter(n => n.section === 'mondo');
    
    if (currentFilter !== 'all') {
        news = news.filter(n => n.categories.includes(currentFilter));
    }
    
    displayNewsList('mondo-news', news);
}

function displayNewsList(elementId, news) {
    const container = document.getElementById(elementId);
    if (!container) return;
    
    if (!news || news.length === 0) {
        container.innerHTML = '<div class="news-card"><div class="news-title">Nessuna notizia disponibile</div></div>';
        return;
    }
    
    container.innerHTML = news.map(item => {
        const categoryIcon = getCategoryIcon(item.categories, item.section);
        const priorityBadge = item.is_high_priority ? '<span style="color:#ff4444;font-weight:bold;">🚨 </span>' : '';
        
        return `
        <div class="news-card" onclick="window.open('${item.link}', '_blank')">
            <div class="news-title">${priorityBadge}${categoryIcon} ${item.title}</div>
            <div class="news-summary">${item.summary}</div>
            <div class="news-meta">
                <span>📰 ${item.source}</span>
                <span>${formatDate(item.published)}</span>
            </div>
        </div>
    `}).join('');
}

function getCategoryIcon(categories, section) {
    if (section === 'ndrangheta') {
        if (categories.includes('arresti')) return '👮';
        if (categories.includes('scarcerazioni')) return '🔓';
        if (categories.includes('droga')) return '💊';
        if (categories.includes('sangue')) return '🔫';
        return '🔍';
    } else if (section === 'mondo') {
        if (categories.includes('guerre')) return '⚔️';
        if (categories.includes('ucraina-russia')) return '🇺🇦';
        if (categories.includes('medio-oriente')) return '🇮🇱';
        if (categories.includes('leader')) return '👤';
        return '🌍';
    } else if (section === 'italia') {
        if (categories.includes('politica')) return '🏛️';
        if (categories.includes('economia')) return '💶';
        return '🇮🇹';
    } else if (section === 'crime_italy') {
        return '🚔';
    }
    return '📰';
}

function formatDate(dateString) {
    if (!dateString) return '';
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('it-IT', { 
            day: '2-digit', month: '2-digit', 
            hour: '2-digit', minute: '2-digit' 
        });
    } catch (e) {
        return '';
    }
}

function showError(message) {
    const containers = ['breaking-news', 'top-news', 'ndrangheta-news', 'mondo-news'];
    containers.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.innerHTML = `
                <div class="news-card">
                    <div class="news-title">⚠️ Errore caricamento</div>
                    <div class="news-summary">${message}</div>
                </div>
            `;
        }
    });
}

function requestNotificationPermission() {
    if ('Notification' in window) {
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') console.log('Permessi notifiche concessi');
        });
    }
}
