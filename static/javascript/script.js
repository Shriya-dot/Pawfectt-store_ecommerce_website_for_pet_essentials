document.addEventListener('DOMContentLoaded', () => {
  const deleteButtons = document.querySelectorAll('.delete');
  deleteButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      if (!confirm('Are you sure you want to delete this product?')) {
        e.preventDefault();
      }
    });
  });
});
