(() => {
    let discoveredUrls = new Set();
    let debounceTimer = null;

    if (window.activeMediaObserver) {
        window.activeMediaObserver.disconnect();
    }
    const existingUi = document.getElementById('media-inspector-ui');
    if (existingUi) existingUi.remove();

    const ui = document.createElement('div');
    ui.id = 'media-inspector-ui';
    ui.style = `
        position: fixed; top: 20px; right: 20px; width: 240px; max-height: 85vh;
        background: rgba(255, 255, 255, 0.98); backdrop-filter: blur(12px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.25); border-radius: 14px;
        z-index: 999999; display: flex; flex-direction: column;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        border: 1px solid rgba(0,0,0,0.15); overflow: hidden;
    `;

    const header = document.createElement('div');
    header.style = 'padding: 12px; background: #e74c3c; color: white; display: flex; align-items: center; justify-content: space-between; font-weight: bold; font-size: 13px; transition: background 0.3s;';

    const titleSpan = document.createElement('span');
    titleSpan.style = 'flex-grow: 1;';
    titleSpan.innerText = '📸 Feed (0)';
    header.appendChild(titleSpan);

    const resetBtn = document.createElement('button');
    resetBtn.innerText = 'Clear';
    resetBtn.style = 'background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.4); color: white; cursor: pointer; font-size: 10px; padding: 3px 6px; border-radius: 4px; margin-right: 8px; font-weight: bold;';
    resetBtn.onclick = () => {
        discoveredUrls.clear();
        listContainer.innerHTML = '';
        titleSpan.innerText = '📸 Feed (0)';
    };
    header.appendChild(resetBtn);

    const closeBtn = document.createElement('button');
    closeBtn.innerText = '✕';
    closeBtn.style = 'background: none; border: none; color: white; cursor: pointer; font-size: 14px; font-weight: bold;';
    header.appendChild(closeBtn);
    ui.appendChild(header);

    const listContainer = document.createElement('div');
    listContainer.style = 'overflow-y: auto; padding: 10px; flex-grow: 1; display: flex; flex-direction: column; gap: 8px; background: #f8f9fa;';
    ui.appendChild(listContainer);
    document.body.appendChild(ui);

    function scrapePageMedia() {
        const imgUrls = Array.from(document.querySelectorAll('img')).map(img => img.currentSrc || img.src).filter(Boolean);
        const videoUrls = Array.from(document.querySelectorAll('video, video source')).map(vid => vid.src).filter(Boolean);
        const bgUrls = Array.from(document.querySelectorAll('*')).map(el => {
            const bg = window.getComputedStyle(el).backgroundImage;
            if (bg && bg !== 'none' && bg.startsWith('url')) {
                const match = bg.match(/url\(['"]?([^'"]+)['"]?\)/);
                return match ? match[1] : null;
            }
            return null;
        }).filter(Boolean);

        const rawCollected = [...imgUrls, ...videoUrls, ...bgUrls];
        let newItemsFound = false;

        rawCollected.forEach(url => {
            if (!url.startsWith('data:') && !url.startsWith('blob:') && !url.includes('1x1') && !discoveredUrls.has(url)) {
                discoveredUrls.add(url);
                newItemsFound = true;
                renderAssetItem(url);
            }
        });

        if (newItemsFound) {
            titleSpan.innerText = `📸 Feed (${discoveredUrls.size})`;
            header.style.background = '#2ecc71';
            setTimeout(() => { header.style.background = '#e74c3c'; }, 400);
        }
    }

    function renderAssetItem(url) {
        const item = document.createElement('div');
        item.style = 'display: flex; align-items: center; justify-content: space-between; padding: 8px; background: white; border-radius: 8px; border: 1px solid #e9ecef; box-shadow: 0 2px 4px rgba(0,0,0,0.02);';

        const thumb = document.createElement('img');
        thumb.src = url;
        thumb.style = 'width: 90px; height: 90px; object-fit: cover; border-radius: 6px; background: #e9ecef; border: 1px solid #dee2e6; cursor: zoom-in;';
        thumb.onmouseenter = (e) => showLargePreview(url, e);
        thumb.onmouseleave = () => hideLargePreview();

        const downloadBtn = document.createElement('a');
        downloadBtn.href = url;
        downloadBtn.target = '_blank';
        downloadBtn.innerText = '💾';
        downloadBtn.title = 'Open full resolution resource file';
        downloadBtn.style = 'text-decoration: none; font-size: 20px; cursor: pointer; padding: 10px; background: #f8f9fa; border-radius: 8px; border: 1px solid #e9ecef; transition: all 0.2s;';

        downloadBtn.onmouseenter = () => {
            downloadBtn.style.background = '#e8f4fd';
            downloadBtn.style.borderColor = '#3498db';
        };
        downloadBtn.onmouseleave = () => {
            downloadBtn.style.background = '#f8f9fa';
            downloadBtn.style.borderColor = '#e9ecef';
        };

        item.appendChild(thumb);
        item.appendChild(downloadBtn);

        listContainer.prepend(item);
    }

    const observer = new MutationObserver(() => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            scrapePageMedia();
        }, 300);
    });

    window.activeMediaObserver = observer;
    observer.observe(document.body, { childList: true, subtree: true });

    closeBtn.onclick = () => {
        observer.disconnect();
        window.activeMediaObserver = null;
        ui.remove();
        hideLargePreview();
    };

    const hoverPreview = document.createElement('div');
    hoverPreview.id = 'media-inspector-hover';
    hoverPreview.style = 'position: fixed; z-index: 1000000; pointer-events: none; display: none; background: white; padding: 6px; border-radius: 8px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); border: 1px solid #ccc; max-width: 380px;';
    const hoverImg = document.createElement('img');
    hoverImg.style = 'max-width: 100%; max-height: 340px; display: block; border-radius: 4px;';
    hoverPreview.appendChild(hoverImg);
    document.body.appendChild(hoverPreview);

    function showLargePreview(url, event) {
        hoverImg.src = url;
        hoverPreview.style.display = 'block';
        positionPreview(event);
        document.onmousemove = positionPreview;
    }

    function hideLargePreview() {
        hoverPreview.style.display = 'none';
        document.onmousemove = null;
    }

    function positionPreview(e) {
        hoverPreview.style.left = `${e.clientX - 410}px`;
        hoverPreview.style.top = `${Math.min(e.clientY - 50, window.innerHeight - 360)}px`;
    }

    scrapePageMedia();
    console.log("%c[Minimal Inspector] Clean visual strip initialized successfully.", "color: #2ecc71; font-weight: bold;");
})();
