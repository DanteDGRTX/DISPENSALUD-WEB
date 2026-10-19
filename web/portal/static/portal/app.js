document.querySelectorAll('[data-open-dialog]').forEach((button) => {
  button.addEventListener('click', () => document.getElementById(button.dataset.openDialog)?.showModal());
});
document.querySelectorAll('[data-close-dialog]').forEach((button) => {
  button.addEventListener('click', () => button.closest('dialog').close());
});
document.querySelectorAll('dialog').forEach((dialog) => {
  dialog.addEventListener('click', (event) => {
    const bounds = dialog.getBoundingClientRect();
    if (event.target === dialog && (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom)) dialog.close();
  });
});
const fontButton = document.querySelector('[data-font-size]');
if (fontButton) {
  let larger = false;
  try { larger = localStorage.getItem('dispensalud-large-text') === 'true'; } catch {}
  const updateFontSize = () => {
    document.body.classList.toggle('larger-text', larger);
    fontButton.setAttribute('aria-pressed', String(larger));
    fontButton.setAttribute('aria-label', larger ? 'Restablecer el tamaño del texto' : 'Aumentar el tamaño del texto');
    fontButton.textContent = larger ? 'A−' : 'A+';
  };
  updateFontSize();
  fontButton.addEventListener('click', () => {
    larger = !larger;
    try { localStorage.setItem('dispensalud-large-text', String(larger)); } catch {}
    updateFontSize();
  });
}
function updateClock() {
  document.querySelectorAll('[data-live-clock]').forEach((clock) => {
    clock.textContent = new Intl.DateTimeFormat('es-PE', {timeZone: 'America/Lima', hour: '2-digit', minute: '2-digit', hour12: false}).format(new Date());
  });
  document.querySelectorAll('[data-countdown]').forEach((element) => {
    const minutes = Math.ceil((new Date(element.dataset.countdown).getTime() - Date.now()) / 60000);
    if (!Number.isFinite(minutes)) return;
    if (minutes <= 0) element.textContent = 'Llegó la hora programada. Actualiza tu horario.';
    else if (minutes >= 60) element.textContent = `Faltan ${Math.floor(minutes / 60)} h ${minutes % 60} min`;
    else element.textContent = `Faltan ${minutes} min`;
  });
}
updateClock();
setInterval(updateClock, 30000);
document.querySelectorAll('form[method="post"]').forEach((form) => {
  form.addEventListener('submit', (event) => {
    if (event.submitter) {
      event.submitter.disabled = true;
      event.submitter.textContent = 'Un momento…';
    }
  });
});
