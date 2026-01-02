from pathlib import Path
import shutil
from typing import List, Optional


async def create_landing_page(
    project_name: str,
    hero_title: str = "The Next Big Thing",
    hero_subtitle: str = "Revolutionizing the way you do things. Built in a cave. Powered by caffeine.",
    features: List[str] = [],
    github_url: str = "https://github.com",
    target_path: str = ".",
    author_name: str = "Joe Shmoe",
    author_bio: str = "I build things in my subterranean headquarters. Powered by free meals and cola courtesy of mum.",
    donate_link: str = "#",
    hero_image: str = "technology",  # Keyword, URL, or local path
    feature_images: Optional[List[str]] = None,
) -> str:
    """
    Creates a premium, multi-page landing page site for a startup/project.

    Generates a complete static site with:
    - index.html (Hero, Features, CTA)
    - bio.html (Developer bio with humor)
    - download.html (Download links)
    - donate.html (Donation page)
    - how_it_works.html (Technical explanation)
    - styles.css (High-end "WOW" design)

    Args:
    Args:
        project_name: Name of the startup/project
        hero_title: Main headline for the hero section
        hero_subtitle: Sub-headline/description
        features: List of "Title: Description" strings for feature cards
        github_url: URL to the GitHub repository
        target_path: Path to generate the site in
        author_name: Name of the developer
        author_bio: Short bio for the developer
        donate_link: Link to donation platform (Patreon, Ko-fi, etc.)
        hero_image: Keyword to auto-generate image, or URL, or local file path
        feature_images: List of keywords/URLs/paths for feature cards (1:1 mapping with features)
    """

    output_dir = Path(target_path) / project_name.lower().replace(" ", "-") / "www"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process Images Helper
    def process_image(img_input: str, width: int = 800, height: int = 600) -> str:
        """
        Handles image inputs:
        1. URL: Returns as-is
        2. Local File: Copies to assets/images/ and returns relative path
        3. Keyword: Generates loremflickr URL
        """
        if not img_input:
            return f"https://loremflickr.com/{width}/{height}/abstract"

        # Check if URL
        if img_input.startswith(("http://", "https://")):
            return img_input

        # Check if Local File
        local_path = Path(img_input)
        if local_path.exists() and local_path.is_file():
            img_dir = output_dir / "assets" / "images"
            img_dir.mkdir(parents=True, exist_ok=True)
            dest_path = img_dir / local_path.name
            shutil.copy2(local_path, dest_path)
            return f"assets/images/{local_path.name}"

        # Treat as Keyword
        return f"https://loremflickr.com/{width}/{height}/{img_input.replace(' ', ',')}"

    # Default features if none provided
    if not features:
        features = [
            "Blazing Fast: Engineered for maximum velocity and minimum drag.",
            "Secure by Design: Fort Knox level security for your data.",
            "Open Source: Transparency is key. Code is law.",
        ]

    # Process Hero Image
    hero_img_url = process_image(hero_image, 1200, 600)

    # Process Feature Images (Smart defaulting)
    processed_feature_imgs = []
    if feature_images:
        processed_feature_imgs = [
            process_image(img, 400, 300) for img in feature_images
        ]
    else:
        # Generate keywords based on feature titles if no images provided
        for feat in features:
            keyword = feat.split(":")[0].strip() if ":" in feat else "tech"
            processed_feature_imgs.append(process_image(keyword, 400, 300))

    # --- CSS Generation (The "WOW" Factor) ---
    css_content = """
/* 
 * Design System: "Void Premium" 
 * Core: Deep Space (#050505), Bioluminescence (#00f3ff), Neon Purple (#bd00ff)
 * Texture: Grain Overlay
 */
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;700;900&display=swap');

:root {
    --bg-dark: #050505;
    --bg-card: rgba(255, 255, 255, 0.02);
    --border-color: rgba(255, 255, 255, 0.08);
    --primary-glow: #00f3ff;
    --secondary-glow: #bd00ff;
    --text-main: #ffffff;
    --text-muted: #94a3b8;
    --font-main: 'Outfit', sans-serif;
    --card-hover-border: rgba(255, 255, 255, 0.2);
}

* { box-sizing: border-box; margin: 0; padding: 0; }

html {
    scroll-behavior: smooth;
}

body {
    background-color: var(--bg-dark);
    color: var(--text-main);
    font-family: var(--font-main);
    line-height: 1.6;
    overflow-x: hidden;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

/* Noise Overlay for Texture */
body::before {
    content: "";
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.05'/%3E%3C/svg%3E");
    pointer-events: none;
    z-index: 9000;
}

/* Ambient Glow Orbs */
.glow-orb {
    position: fixed;
    border-radius: 50%;
    filter: blur(80px);
    z-index: -1;
    opacity: 0.4;
    animation: float 20s infinite alternate;
}

.orb-1 {
    top: -10%;
    left: -10%;
    width: 50vw;
    height: 50vw;
    background: radial-gradient(circle, var(--primary-glow) 0%, transparent 70%);
}

.orb-2 {
    bottom: -10%;
    right: -10%;
    width: 60vw;
    height: 60vw;
    background: radial-gradient(circle, var(--secondary-glow) 0%, transparent 70%);
    animation-delay: -5s;
}

@keyframes float {
    0% { transform: translate(0, 0); }
    100% { transform: translate(30px, 50px); }
}

/* Animations */
.reveal {
    opacity: 0;
    transform: translateY(30px);
    transition: all 0.8s cubic-bezier(0.5, 0, 0, 1);
}

.reveal.active {
    opacity: 1;
    transform: translateY(0);
}

/* Navigation */
nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem 5%;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    background: rgba(5, 5, 5, 0.5);
    position: sticky;
    top: 0;
    z-index: 100;
    border-bottom: 1px solid rgba(255,255,255,0.03);
}

.logo {
    font-weight: 900;
    font-size: 1.8rem;
    letter-spacing: -0.05em;
    color: #fff;
    text-decoration: none;
    position: relative;
    z-index: 1;
}

.nav-links {
    display: flex;
    gap: 2.5rem;
    background: rgba(255, 255, 255, 0.03);
    padding: 0.7rem 2rem;
    border-radius: 100px;
    border: 1px solid rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
}

.nav-links a {
    color: var(--text-muted);
    text-decoration: none;
    font-weight: 500;
    font-size: 0.95rem;
    transition: all 0.3s ease;
    position: relative;
}

.nav-links a:hover, .nav-links a.active {
    color: #fff;
}

.nav-links a.active::after {
    content: '';
    position: absolute;
    bottom: -5px;
    left: 50%;
    transform: translateX(-50%);
    width: 4px;
    height: 4px;
    border-radius: 50%;
    background: var(--primary-glow);
    box-shadow: 0 0 10px var(--primary-glow);
}

.btn-github {
    background: rgba(255,255,255,0.05);
    color: white;
    padding: 0.7rem 1.4rem;
    border-radius: 12px;
    text-decoration: none;
    font-weight: 600;
    border: 1px solid rgba(255,255,255,0.08);
    transition: all 0.3s ease;
    display: inline-flex;
    align-items: center;
    gap: 0.6rem;
}

.btn-github:hover {
    background: rgba(255,255,255,0.1);
    transform: translateY(-2px);
    border-color: rgba(255, 255, 255, 0.2);
    box-shadow: 0 5px 20px rgba(0,0,0,0.2);
}

/* Hero Section */
.hero {
    position: relative;
    text-align: center;
    padding: 10rem 2rem;
    max-width: 1200px;
    margin: 0 auto;
    z-index: 2;
}

.hero h1 {
    font-size: 6rem;
    font-weight: 900;
    line-height: 1;
    margin-bottom: 2rem;
    letter-spacing: -0.04em;
    background: linear-gradient(135deg, #ffffff 0%, #b0b0b0 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: fadeUp 1s cubic-bezier(0.5, 0, 0, 1) forwards;
}

.hero p {
    font-size: 1.6rem;
    color: var(--text-muted);
    max-width: 650px;
    margin: 0 auto 3.5rem;
    font-weight: 300;
    animation: fadeUp 1s cubic-bezier(0.5, 0, 0, 1) forwards 0.2s;
    opacity: 0;
}

.hero-visual {
    margin-bottom: 2rem;
    border-radius: 20px;
    overflow: hidden;
    box-shadow: 0 20px 50px rgba(0,0,0,0.5);
    border: 1px solid rgba(255,255,255,0.1);
    animation: fadeUp 1s cubic-bezier(0.5, 0, 0, 1) forwards;
}

.hero-visual img {
    width: 100%;
    max-height: 500px;
    object-fit: cover;
    display: block;
    transform: scale(1.02);
    transition: transform 0.8s;
}

.hero-visual:hover img {
    transform: scale(1.05);
}

@keyframes fadeUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.hero-btns {
    display: flex;
    gap: 1.5rem;
    justify-content: center;
    animation: fadeUp 1s cubic-bezier(0.5, 0, 0, 1) forwards 0.4s;
    opacity: 0;
}

.btn-primary {
    background: #fff;
    color: #000;
    padding: 1.1rem 2.2rem;
    border-radius: 100px;
    font-weight: 700;
    text-decoration: none;
    transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
    position: relative;
    overflow: hidden;
}

.btn-primary::before {
    content: '';
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    background: linear-gradient(45deg, var(--primary-glow), var(--secondary-glow));
    opacity: 0;
    transition: opacity 0.4s ease;
    z-index: 1;
}

.btn-primary span {
    position: relative;
    z-index: 2;
}

.btn-primary:hover {
    transform: scale(1.05);
    box-shadow: 0 0 30px rgba(255, 255, 255, 0.3);
}

.btn-primary:hover::before {
    opacity: 0.1;
}

.btn-secondary {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    color: white;
    padding: 1.1rem 2.2rem;
    border-radius: 100px;
    font-weight: 600;
    text-decoration: none;
    transition: all 0.3s ease;
    backdrop-filter: blur(10px);
}

.btn-secondary:hover {
    background: rgba(255,255,255,0.1);
    border-color: rgba(255,255,255,0.3);
    transform: translateY(-2px);
}

/* Features Grid */
.features {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 2.5rem;
    max-width: 1200px;
    margin: 4rem auto 10rem;
    padding: 0 2rem;
}

.feature-card {
    background: linear-gradient(180deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.01) 100%);
    border: 1px solid var(--border-color);
    padding: 2.5rem;
    border-radius: 24px;
    transition: all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
    cursor: default;
    position: relative;
    overflow: hidden;
}

.feature-img {
    width: 100%;
    height: 200px;
    object-fit: cover;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    opacity: 0.8;
    transition: all 0.5s ease;
}

.feature-card:hover .feature-img {
    opacity: 1;
    transform: scale(1.03);
}

.feature-card:hover {
    transform: translateY(-8px);
    border-color: var(--card-hover-border);
    box-shadow: 0 20px 40px rgba(0,0,0,0.3);
}

.feature-card h3 {
    font-size: 1.5rem;
    margin-bottom: 1rem;
    background: linear-gradient(to right, #fff, #cbd5e1);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.feature-card p {
    color: var(--text-muted);
    font-size: 1.05rem;
    line-height: 1.7;
}

/* Content Pages */
.content-container {
    max-width: 900px;
    margin: 6rem auto;
    padding: 0 2rem;
    position: relative;
    z-index: 2;
}

.content-card {
    background: rgba(10, 10, 12, 0.6);
    border: 1px solid var(--border-color);
    padding: 4rem;
    border-radius: 32px;
    backdrop-filter: blur(20px);
    box-shadow: 0 40px 100px rgba(0,0,0,0.3);
}

.tech-spec-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 2rem;
    margin-top: 3rem;
}

.spec-item {
    background: rgba(255,255,255,0.02);
    padding: 1.5rem;
    border-radius: 16px;
    border: 1px solid rgba(255,255,255,0.05);
    transition: 0.3s;
}

.spec-item:hover {
    background: rgba(255,255,255,0.04);
    border-color: rgba(255,255,255,0.1);
    transform: scale(1.02);
}

.spec-label {
    display: block;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-muted);
    margin-bottom: 0.5rem;
}

.spec-value {
    font-weight: 600;
    font-size: 1.2rem;
    color: #fff;
}

/* Canvas for Particles */
#canvas-container {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 0;
    pointer-events: none;
    opacity: 0.6;
}

/* Footer */
footer {
    border-top: 1px solid rgba(255,255,255,0.03);
    padding: 4rem 5%;
    text-align: center;
    margin-top: auto;
    color: var(--text-muted);
    background: rgba(0,0,0,0.2);
    backdrop-filter: blur(10px);
}

.footer-links {
    display: flex;
    justify-content: center;
    gap: 2.5rem;
    margin-bottom: 2rem;
}

.footer-links a {
    color: var(--text-muted);
    text-decoration: none;
    transition: 0.3s;
    font-weight: 500;
}

.footer-links a:hover {
    color: white;
    text-shadow: 0 0 10px rgba(255,255,255,0.5);
}

/* Mobile */
@media (max-width: 768px) {
    .hero h1 { font-size: 3.5rem; }
    .hero-btns { flex-direction: column; }
    .nav-links { display: none; } 
    .tech-spec-grid { grid-template-columns: 1fr; }
    .content-card { padding: 2rem; }
}
    """

    # --- JS Generation (Dynamic Particles) ---
    js_content = """
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
"""

    # --- HTML Templates ---

    def generate_nav(active_page: str, project_name: str) -> str:
        links = {
            "index.html": "Home",
            "how_it_works.html": "How It Works",
            "download.html": "Download",
            "donate.html": "Donate",
            "bio.html": "About Dev",
        }
        nav_html = f'<nav><a href="index.html" class="logo">{project_name}</a><div class="nav-links">'
        for file, label in links.items():
            active_class = ' class="active"' if file == active_page else ""
            nav_html += f'<a href="{file}"{active_class}>{label}</a>'
        nav_html += f'</div><a href="{github_url}" class="btn-github" target="_blank"><span>GitHub</span></a></nav>'
        return nav_html

    def generate_html(title: str, content: str, active_page: str) -> str:
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | {project_name}</title>
    <link rel="stylesheet" href="styles.css">
    <meta name="description" content="{hero_subtitle}">
</head>
<body>
    <canvas id="canvas-container"></canvas>
    <div class="glow-orb orb-1"></div>
    <div class="glow-orb orb-2"></div>

    {generate_nav(active_page, project_name)}
    
    <main>
        {content}
    </main>

    <footer>
        <div class="footer-links">
            <a href="{github_url}" target="_blank">Source Code</a>
            <a href="donate.html">Buy me a Cola</a>
            <a href="bio.html">Contact</a>
        </div>
        <p>&copy; 2024 {author_name}. Built with {project_name}.</p>
    </footer>

    <script src="script.js"></script>
</body>
</html>"""

    # --- Page Content Generators ---

    # 1. Index Page
    # 1. Index Page
    feature_cards_html = ""
    for i, feat in enumerate(features):
        if ":" in feat:
            ft, fd = feat.split(":", 1)
        else:
            ft, fd = feat, "Experience the power of innovation."
        feature_cards_html += f"""
        <div class="feature-card">
            <img src="{processed_feature_imgs[i] if i < len(processed_feature_imgs) else "https://loremflickr.com/400/300/abstract"}" alt="{ft.strip()}" class="feature-img">
            <h3>{ft.strip()}</h3>
            <p>{fd.strip()}</p>
        </div>"""

    index_content = f"""
    <section class="hero">
        <div class="hero-visual">
            <img src="{hero_img_url}" alt="Hero Image">
        </div>
        <h1>{hero_title}</h1>
        <p>{hero_subtitle}</p>
        <div class="hero-btns">
            <a href="download.html" class="btn-primary">Get Started</a>
            <a href="how_it_works.html" class="btn-secondary">Learn More</a>
        </div>
    </section>
    
    <section class="features">
        {feature_cards_html}
    </section>
    """

    # 2. How It Works Page
    how_content = f"""
    <div class="content-container">
        <div class="hero">
            <h1>Under the Hood</h1>
            <p>Transparency is our core value. Here's how {project_name} actually works.</p>
        </div>
        
        <div class="content-card">
            <h2>Architecture</h2>
            <p>Built using state-of-the-art AI models and robust engineering principles. We don't just wrap ChatGPT; we orchestrate complex workflows.</p>
            
            <div class="tech-spec-grid">
                <div class="spec-item">
                    <span class="spec-label">Core Engine</span>
                    <span class="spec-value">Python / Rust</span>
                </div>
                <div class="spec-item">
                    <span class="spec-label">AI Model</span>
                    <span class="spec-value">Gemini / Claude</span>
                </div>
                <div class="spec-item">
                    <span class="spec-label">Latency</span>
                    <span class="spec-value">&lt; 50ms</span>
                </div>
                <div class="spec-item">
                    <span class="spec-label">License</span>
                    <span class="spec-value">MIT Open Source</span>
                </div>
            </div>
            
            <br>
            <p>This project was generated with the assistance of advanced AI agents, ensuring best practices and modern code standards from day one.</p>
        </div>
    </div>
    """

    # 3. Download Page
    download_content = f"""
    <div class="content-container">
        <div class="hero">
            <h1>Download {project_name}</h1>
            <p>Choose your platform. No trackers, no bloatware.</p>
        </div>
        
        <div class="features"> <!-- Reusing grid for download options -->
            <div class="feature-card" style="text-align: center;">
                <h3>Windows</h3>
                <p>Windows 10/11 (x64)</p>
                <br>
                <a href="#" class="btn-primary">Download .exe</a>
            </div>
            <div class="feature-card" style="text-align: center;">
                <h3>macOS</h3>
                <p>Apple Silicon & Intel</p>
                <br>
                <a href="#" class="btn-secondary">Download .dmg</a>
            </div>
            <div class="feature-card" style="text-align: center;">
                <h3>Linux</h3>
                <p>Ubuntu / Debian / Arch</p>
                <br>
                <a href="#" class="btn-secondary">Download .deb</a>
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 2rem;">
            <p style="color: var(--text-muted);">Current Version: v1.0.0-alpha • <a href="{github_url}/releases" style="color: var(--primary-glow);">View Changelog</a></p>
        </div>
    </div>
    """

    # 4. Donate Page
    donate_content = f"""
    <div class="content-container">
        <div class="hero">
            <h1>Support Development</h1>
            <p>Fuel the creation of {project_name}.</p>
        </div>
        
        <div class="content-card" style="text-align: center;">
            <h2>Free Software, Real Costs</h2>
            <p>I build this in my spare time. While I love coding, servers and caffeine aren't free.</p>
            <br>
            <p>If this tool saved you time or made you money, consider buying me a drink. It keeps the updates coming and the "Subterranean HQ" heated.</p>
            <br><br>
            <a href="{donate_link}" class="btn-primary" target="_blank">Support on Patreon / Ko-fi</a>
            <br><br>
            <p style="font-size: 0.9rem; color: var(--text-muted);">Crypto addresses available on GitHub profile.</p>
        </div>
    </div>
    """

    # 5. Bio Page
    bio_content = f"""
    <div class="content-container">
        <div class="hero">
            <h1>About the Developer</h1>
        </div>
        
        <div class="content-card">
            <div style="display: flex; gap: 2rem; align-items: flex-start; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 300px;">
                    <h2>Hi, I'm {author_name}.</h2>
                    <br>
                    <p>{author_bio}</p>
                    <br>
                    <p><strong>HQ Location:</strong> Subterranean Headquarters (Mom's Basement / Home Office)</p>
                    <p><strong>Fuel Source:</strong> Discount Cola & Pizza</p>
                    <p><strong>Philosophy:</strong> "It works on my machine."</p>
                    
                    <br>
                    <div style="display: flex; gap: 1rem;">
                        <a href="{github_url}" class="btn-github">Follow on GitHub</a>
                        <a href="mailto:contact@example.com" class="btn-secondary">Email Me</a>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """

    # --- File Writing ---

    files = {
        "styles.css": css_content,
        "script.js": js_content,
        "index.html": generate_html("Home", index_content, "index.html"),
        "how_it_works.html": generate_html(
            "How It Works", how_content, "how_it_works.html"
        ),
        "download.html": generate_html("Downloads", download_content, "download.html"),
        "donate.html": generate_html("Donate", donate_content, "donate.html"),
        "bio.html": generate_html("About", bio_content, "bio.html"),
    }

    created_files = []
    for filename, content in files.items():
        file_path = output_dir / filename
        file_path.write_text(content, encoding="utf-8")
        created_files.append(str(file_path))

    return f"Successfully generated landing page site in {output_dir}. Created {len(created_files)} files."
