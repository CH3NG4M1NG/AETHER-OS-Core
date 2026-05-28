// Real-time Clock controller
setInterval(() => {
  const clockEl = document.getElementById('dynamic-clock');
  if (clockEl) {
    clockEl.innerText = new Date().toLocaleTimeString();
  }
}, 1000);

// Button interaction
let clickCount = 0;
const btn = document.getElementById('action-btn');
const feedback = document.getElementById('click-feedback');

if (btn && feedback) {
  btn.addEventListener('click', () => {
    clickCount++;
    feedback.innerText = `🎉 Kamu telah mengklik tombol sebanyak ${clickCount} kali!`;
    feedback.style.color = '#38bdf8';
  });
}