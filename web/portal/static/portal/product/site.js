const menuToggle = document.getElementById('mobile-menu-toggle');
const mobileDrawer = document.getElementById('mobile-drawer');
if (menuToggle && mobileDrawer) {
  menuToggle.addEventListener('click', () => {
    const expanded = menuToggle.getAttribute('aria-expanded') === 'true';
    menuToggle.setAttribute('aria-expanded', String(!expanded));
    mobileDrawer.hidden = expanded;
  });
  mobileDrawer.querySelectorAll('a').forEach(link => link.addEventListener('click', () => {
    mobileDrawer.hidden = true;
    menuToggle.setAttribute('aria-expanded', 'false');
  }));
}
document.querySelectorAll('[data-part-name]').forEach(button => {
  button.addEventListener('click', () => {
    document.querySelectorAll('[data-part-name]').forEach(item => {
      item.classList.remove('selected');
      item.setAttribute('aria-pressed', 'false');
    });
    button.classList.add('selected');
    button.setAttribute('aria-pressed', 'true');
    document.getElementById('part-name').textContent = button.dataset.partName;
    document.getElementById('part-detail').textContent = button.dataset.partDetail;
  });
});
