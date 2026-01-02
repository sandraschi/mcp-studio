
class Particle {
    constructor(canvas, ctx) {
        this.canvas = canvas;
        this.ctx = ctx;
        this.x = Math.random() * canvas.width;
        this.y = Math.random() * canvas.height;
        this.vx = (Math.random() - 0.5) * 0.5;
        this.vy = (Math.random() - 0.5) * 0.5;
        this.size = Math.random() * 2 + 1;
    }

    update() {
        this.x += this.vx;
        this.y += this.vy;

        if (this.x < 0 || this.x > this.canvas.width) this.vx *= -1;
        if (this.y < 0 || this.y > this.canvas.height) this.vy *= -1;
    }

    draw() {
        this.ctx.fillStyle = `rgba(255, 255, 255, ${Math.random() * 0.3})`;
        this.ctx.beginPath();
        this.ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        this.ctx.fill();
    }
}

function initParticles() {
    const canvas = document.getElementById("canvas-container");
    const ctx = canvas.getContext("2d");
    
    // Resize handling
    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    window.addEventListener("resize", resize);
    resize();

    const particles = Array.from({ length: 50 }, () => new Particle(canvas, ctx));

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        particles.forEach(p => {
            p.update();
            p.draw();
        });
        requestAnimationFrame(animate);
    }
    animate();
}

// Scroll Animations
function initAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add("active");
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.feature-card, .content-card, .spec-item').forEach(el => {
        el.classList.add('reveal');
        observer.observe(el);
    });
}

document.addEventListener("DOMContentLoaded", () => {
    initParticles();
    initAnimations();
});
