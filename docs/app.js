document.addEventListener('DOMContentLoaded', () => {
    const contentDiv = document.getElementById('content');
    const breadcrumb = document.getElementById('breadcrumb');
    const navLinks = document.querySelectorAll('.nav-link');
    const loading = document.getElementById('loading');
    const menuToggle = document.getElementById('menuToggle');
    const sidebar = document.getElementById('sidebar');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');

    let currentPath = 'introduction';
    const pages = Array.from(navLinks).map(link => link.getAttribute('data-content'));

    // Configure marked options
    marked.setOptions({
        highlight: function (code, lang) {
            if (Prism.languages[lang]) {
                return Prism.highlight(code, Prism.languages[lang], lang);
            }
            return code;
        },
        breaks: true,
        gfm: true
    });

    const loadContent = async (path) => {
        currentPath = path;
        loading.style.display = 'block';
        contentDiv.style.opacity = '0';

        try {
            const response = await fetch(`content/${path}.md`);
            if (!response.ok) throw new Error('Failed to load content');
            const markdown = await response.text();
            contentDiv.innerHTML = marked.parse(markdown);
            breadcrumb.textContent = path.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');

            // Update active link
            navLinks.forEach(link => {
                if (link.getAttribute('data-content') === path) {
                    link.classList.add('active');
                } else {
                    link.classList.remove('active');
                }
            });

            // Update footer buttons
            const currentIndex = pages.indexOf(path);
            prevBtn.style.visibility = currentIndex > 0 ? 'visible' : 'hidden';
            nextBtn.style.visibility = currentIndex < pages.length - 1 ? 'visible' : 'hidden';

            // Re-highlight code
            Prism.highlightAll();

            // Scroll to top
            document.querySelector('.content-wrapper').scrollTop = 0;

        } catch (error) {
            contentDiv.innerHTML = `<h1>Error</h1><p>Could not load the documentation for "${path}".</p>`;
        } finally {
            loading.style.setProperty('display', 'none', 'important');
            contentDiv.style.opacity = '1';
            contentDiv.style.transition = 'opacity 0.3s ease';
        }
    };

    // Navigation and routing
    const handleNavigation = (e) => {
        if (e.target.classList.contains('nav-link')) {
            e.preventDefault();
            const path = e.target.getAttribute('data-content');
            window.location.hash = path;
            loadContent(path);

            // Close sidebar on mobile
            if (window.innerWidth <= 992) {
                sidebar.classList.remove('open');
            }
        }
    };

    navLinks.forEach(link => link.addEventListener('click', handleNavigation));

    // Handle initial load and hash changes
    const initialLoad = () => {
        const hash = window.location.hash.substring(1);
        if (hash && pages.includes(hash)) {
            loadContent(hash);
        } else {
            loadContent('introduction');
        }
    };

    window.addEventListener('hashchange', initialLoad);
    initialLoad();

    // Menu Toggle
    menuToggle.addEventListener('click', () => {
        sidebar.classList.toggle('open');
    });

    // Prev/Next buttons
    prevBtn.addEventListener('click', () => {
        const currentIndex = pages.indexOf(currentPath);
        if (currentIndex > 0) {
            const newPath = pages[currentIndex - 1];
            window.location.hash = newPath;
            loadContent(newPath);
        }
    });

    nextBtn.addEventListener('click', () => {
        const currentIndex = pages.indexOf(currentPath);
        if (currentIndex < pages.length - 1) {
            const newPath = pages[currentIndex + 1];
            window.location.hash = newPath;
            loadContent(newPath);
        }
    });
});
