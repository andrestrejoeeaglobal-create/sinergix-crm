
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('./sw.js?v=64').then(reg => {
        reg.update();
        console.log('[PWA v40] Service Worker registrado y actualizado.');
      }).catch(err => {
        console.warn('[PWA v40] Error al registrar Service Worker:', err);
      });
    });
  }
