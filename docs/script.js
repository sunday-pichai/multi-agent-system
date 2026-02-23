// ==================== Dark Mode Toggle ====================
const mobileHeaderThemeToggle = document.getElementById("mobileHeaderThemeToggle");
const desktopThemeToggle = document.getElementById("desktopThemeToggle");

function toggleDarkMode() {
  document.body.classList.toggle("dark-mode");
  const isDarkMode = document.body.classList.contains("dark-mode");
  localStorage.setItem("darkMode", isDarkMode);
}

// Check for saved dark mode preference
const savedDarkMode = localStorage.getItem("darkMode") === "true";
if (savedDarkMode) {
  document.body.classList.add("dark-mode");
}

// Mobile header theme toggle
if (mobileHeaderThemeToggle) {
  mobileHeaderThemeToggle.addEventListener("click", toggleDarkMode);
}

// Desktop sidebar theme toggle
if (desktopThemeToggle) {
  desktopThemeToggle.addEventListener("click", toggleDarkMode);
}

// ==================== Desktop Sidebar Active Link ====================
function updateActiveNavLink() {
  const sections = document.querySelectorAll('.doc-section, .algo-card');
  const navLinks = document.querySelectorAll('.nav-link');
  
  let currentSection = '';
  const scrollPosition = window.scrollY + 150;
  
  sections.forEach(section => {
    const sectionTop = section.offsetTop;
    const sectionHeight = section.offsetHeight;
    
    if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
      currentSection = section.getAttribute('id');
    }
  });
  
  navLinks.forEach(link => {
    link.classList.remove('active');
    if (link.getAttribute('href') === `#${currentSection}`) {
      link.classList.add('active');
    }
  });
}

// Update active link on scroll
window.addEventListener('scroll', updateActiveNavLink);
window.addEventListener('load', updateActiveNavLink);

// ==================== Mobile Navigation System ====================
class MobileNavigation {
  constructor() {
    this.toggle = document.getElementById("mobileMenuToggle");
    this.menu = document.getElementById("mobileFullscreenMenu");
    this.isOpen = false;
    
    if (this.toggle && this.menu) {
      this.init();
    }
  }
  
  init() {
    // Toggle button click
    this.toggle.addEventListener("click", (e) => {
      e.stopPropagation();
      this.toggleMenu();
    });
    
    // Click nav links to close menu
    this.menu.querySelectorAll(".mobile-nav-link").forEach(link => {
      link.addEventListener("click", (e) => {
        const href = link.getAttribute("href");
        if (href && href.startsWith("#")) {
          e.preventDefault();
          this.handleNavClick(href);
        }
      });
    });
    
    // Keyboard support
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && this.isOpen) {
        this.close();
      }
    });
    
    // Set initial active link
    this.setActiveLink(window.location.hash || "#overview");
  }
  
  toggleMenu() {
    this.isOpen ? this.close() : this.open();
  }
  
  open() {
    this.isOpen = true;
    document.body.classList.add("mobile-menu-open");
    this.toggle.setAttribute("aria-expanded", "true");
  }
  
  close() {
    this.isOpen = false;
    document.body.classList.remove("mobile-menu-open");
    this.toggle.setAttribute("aria-expanded", "false");
  }
  
  handleNavClick(href) {
    // Set active link
    this.setActiveLink(href);
    
    // Close menu
    this.close();
    
    // Scroll to section
    setTimeout(() => {
      const target = document.querySelector(href);
      if (target) {
        target.scrollIntoView({ behavior: "smooth", block: "start" });
        history.pushState(null, null, href);
      }
    }, 200);
  }
  
  setActiveLink(href) {
    this.menu.querySelectorAll(".mobile-nav-link").forEach(link => {
      link.classList.remove("active");
    });
    const activeLink = this.menu.querySelector(`a[href="${href}"]`);
    if (activeLink) {
      activeLink.classList.add("active");
    }
  }
}

// Initialize navigation
let mobileNav;

function initNavigation() {
  mobileNav = new MobileNavigation();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initNavigation);
} else {
  initNavigation();
}

// ==================== Sidebar Toggle (Mobile) ====================
// Removed - no longer using sidebar

// ==================== Active Link Highlighting ====================
// Removed - no longer using active link highlighting

// ==================== Canvas Demos - Responsive Setup ====================
const CANVAS_MIN_HEIGHT = (() => {
  if (typeof window === "undefined") {
    return 1444;
  }
  const width = window.innerWidth;
  // Mobile-first responsive breakpoints
  if (width <= 380) return 300;      // Small phones
  if (width <= 480) return 360;      // Standard phones
  if (width <= 600) return 420;      // Large phones
  if (width <= 768) return 540;      // Tablets (portrait)
  if (width <= 1024) return 720;     // Tablets (landscape) / Small screens
  return 1444;                        // Desktop
})();

function createHiResCanvas(canvas, minHeight = CANVAS_MIN_HEIGHT) {
  const ctx = canvas.getContext("2d");
  let lastWidth = 0;
  let lastHeight = 0;
  let lastScale = 0;

  function resize(force = false) {
    const rect = canvas.getBoundingClientRect();
    if (!rect.width || !rect.height) {
      return { width: 0, height: 0, scale: 1 };
    }

    // Scale canvas resolution for high-DPI displays (retina, etc)
    // but keep drawing viewport at actual CSS display size
    const dpr = window.devicePixelRatio || 1;
    // Only use devicePixelRatio for crisp rendering, not minHeight (prevents zoom)
    const scale = dpr;
    const width = Math.max(1, Math.round(rect.width * scale));
    const height = Math.max(1, Math.round(rect.height * scale));

    if (force || width !== lastWidth || height !== lastHeight || scale !== lastScale) {
      canvas.width = width;
      canvas.height = height;
      ctx.setTransform(scale, 0, 0, scale, 0, 0);
      lastWidth = width;
      lastHeight = height;
      lastScale = scale;
    }

    return { width: rect.width, height: rect.height, scale };
  }

  return { ctx, resize };
}

const steps = {
  plan: {
    title: "Plan (Cooperative Space-Time A*)",
    text:
      "Agents plan in a time-expanded grid. Earlier agents reserve cells/edges, later agents route around those reservations, and stalled agents use deterministic escape actions.",
    code: `Cooperative planner:
- global assignment (Hungarian)
- time-expanded grid
- reservation table (vertex + edge)
- rolling reservation window
- deadlock escape`,
  },
  symmetry: {
    title: "Symmetry Reduction",
    text:
      "Agents are grouped into role orbits (idle vs carrying requested). Canonicalization maps symmetric permutations to a single quotient state.",
    code: `Orbits:
- group by role
- canonicalize positions
- shrink state space`,
  },
  verify: {
    title: "Verify on Quotient",
    text:
      "Bounded verification checks collisions and minimum separation over the quotient. If unsafe, it returns a counterexample trace.",
    code: `Verify:
- run trials
- track collisions
- compute delta_q`,
  },
  refine: {
    title: "Refine with Constraints",
    text:
      "Counterexamples are converted to hard constraints. The planner avoids these moves and verification repeats.",
    code: `Refine:
- extract conflict
- add constraint
- re-verify`,
  },
};

// ==================== Flow Chart Demo ====================
const flowSection = document.getElementById("refinement");
const flowButtons = flowSection ? flowSection.querySelectorAll("[data-flow]") : [];
const flowChart = document.getElementById("flowChart");
const flowChartCaption = document.getElementById("flowChartCaption");
const flowChartSurface = flowChart ? createHiResCanvas(flowChart) : null;

function drawFlowChart(active) {
  if (!flowChart || !flowChartSurface) return;
  const ctx = flowChartSurface.ctx;
  const size = flowChartSurface.resize();
  const width = size.width;
  const height = size.height;

  ctx.clearRect(0, 0, width, height);
  const bg = ctx.createLinearGradient(0, 0, width, height);
  bg.addColorStop(0, "#0f1318");
  bg.addColorStop(1, "#18202a");
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, width, height);

  // Dynamic responsive positioning based on canvas size
  const centerX = width / 2;
  const centerY = height / 2;
  
  // Mobile-responsive spacing
  let spacing, vSpacing, nodeWidth, nodeHeight, fontSize;
  
  if (width < 400) {
    spacing = Math.min(width * 0.25, 80);
    vSpacing = Math.min(height * 0.25, 60);
    nodeWidth = Math.max(60, width * 0.18);
    nodeHeight = Math.max(35, height * 0.15);
    fontSize = Math.max(10, width * 0.035);
  } else if (width < 600) {
    spacing = Math.min(width * 0.3, 120);
    vSpacing = Math.min(height * 0.28, 80);
    nodeWidth = Math.max(90, width * 0.22);
    nodeHeight = Math.max(40, height * 0.18);
    fontSize = Math.max(12, width * 0.04);
  } else {
    spacing = Math.min(width * 0.35, 180);
    vSpacing = Math.min(height * 0.3, 100);
    nodeWidth = Math.min(width * 0.25, 140);
    nodeHeight = Math.min(height * 0.15, 50);
    fontSize = Math.max(14, width * 0.045);
  }
  
  const nodes = [
    { key: "plan", label: "Plan", x: centerX - spacing, y: centerY - vSpacing },
    { key: "symmetry", label: "Symmetry", x: centerX + spacing * 0.25, y: centerY - vSpacing },
    { key: "verify", label: "Verify", x: centerX + spacing * 0.25, y: centerY + vSpacing * 0.3 },
    { key: "refine", label: "Refine", x: centerX - spacing, y: centerY + vSpacing * 0.3 },
  ];

  // Constrain node positions to stay within canvas bounds
  const padding = 20;
  nodes.forEach((n) => {
    n.x = Math.max(padding, Math.min(n.x, width - nodeWidth - padding));
    n.y = Math.max(padding, Math.min(n.y, height - nodeHeight - padding));
  });

  function roundedRect(x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h - r);
    ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    ctx.lineTo(x + r, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - r);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.closePath();
  }

  function arrow(fromX, fromY, toX, toY) {
    ctx.strokeStyle = "rgba(255,255,255,0.35)";
    ctx.lineWidth = Math.max(1.5, width * 0.003);
    ctx.beginPath();
    ctx.moveTo(fromX, fromY);
    ctx.lineTo(toX, toY);
    ctx.stroke();
    const angle = Math.atan2(toY - fromY, toX - fromX);
    const head = Math.max(5, width * 0.012);
    ctx.beginPath();
    ctx.moveTo(toX, toY);
    ctx.lineTo(toX - head * Math.cos(angle - Math.PI / 6), toY - head * Math.sin(angle - Math.PI / 6));
    ctx.lineTo(toX - head * Math.cos(angle + Math.PI / 6), toY - head * Math.sin(angle + Math.PI / 6));
    ctx.closePath();
    ctx.fillStyle = "rgba(255,255,255,0.35)";
    ctx.fill();
  }

  // Draw arrows between nodes
  arrow(nodes[0].x + nodeWidth, nodes[0].y + nodeHeight/2, nodes[1].x, nodes[1].y + nodeHeight/2);
  arrow(nodes[1].x + nodeWidth/2, nodes[1].y + nodeHeight, nodes[2].x + nodeWidth/2, nodes[2].y);
  arrow(nodes[2].x, nodes[2].y + nodeHeight/2, nodes[3].x + nodeWidth, nodes[3].y + nodeHeight/2);
  arrow(nodes[3].x + nodeWidth/2, nodes[3].y, nodes[0].x + nodeWidth/2, nodes[0].y + nodeHeight);

  nodes.forEach((n) => {
    const isActive = n.key === active;
    ctx.save();
    ctx.shadowColor = isActive ? "rgba(255, 214, 102, 0.5)" : "rgba(0,0,0,0.35)";
    ctx.shadowBlur = isActive ? 18 : 12;
    ctx.shadowOffsetY = Math.max(3, height * 0.018);
    ctx.fillStyle = isActive ? "#c85d3d" : "#1f2a33";
    ctx.strokeStyle = isActive ? "#ffd166" : "#2d3a45";
    ctx.lineWidth = Math.max(1.5, width * 0.003);
    roundedRect(n.x, n.y, nodeWidth, nodeHeight, Math.max(6, width * 0.015));
    ctx.fill();
    ctx.stroke();
    ctx.restore();

    ctx.fillStyle = "#f2f2f2";
    ctx.font = `600 ${fontSize}px 'Space Grotesk', sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    const textX = n.x + nodeWidth / 2;
    const textY = n.y + nodeHeight / 2;
    ctx.fillText(n.label, textX, textY);
    
    // Reset text alignment
    ctx.textAlign = "left";
    ctx.textBaseline = "alphabetic";
  });
}

// Redraw on resize for responsive behavior
let resizeTimeout;
window.addEventListener('resize', () => {
  // Debounce resize events
  clearTimeout(resizeTimeout);
  resizeTimeout = setTimeout(() => {
    const activeBtn = document.querySelector('[data-flow].is-active');
    if (activeBtn && flowChart) {
      drawFlowChart(activeBtn.dataset.flow);
    }
    
    // Force redraw of other canvases
    if (algoCanvas && algoSurface) {
      algoSurface.resize(true);
    }
    if (symmetryCanvas && symmetrySurface) {
      symmetrySurface.resize(true);
    }
    if (verifyCanvas && verifySurface) {
      verifySurface.resize(true);
    }
  }, 250); // Debounce for 250ms
});

function updateFlow(active) {
  flowButtons.forEach((b) => b.classList.toggle("is-active", b.dataset.flow === active));
  const captions = {
    plan: "Plan: cooperative space-time A* with rolling reservations.",
    symmetry: "Symmetry: role-orbit reduction and canonicalization.",
    verify: "Verify: bounded safety checks on the quotient model.",
    refine: "Refine: constraints injected from counterexamples.",
  };
  if (flowChartCaption) {
    flowChartCaption.textContent = steps[active]?.title || captions[active] || "";
  }
  drawFlowChart(active);
}

flowButtons.forEach((btn) => {
  btn.addEventListener("click", () => updateFlow(btn.dataset.flow));
});

updateFlow("plan");

// Canvas interactive explainer - minimal design
const canvas = document.getElementById("flowCanvas");
const caption = document.getElementById("canvasCaption");
const modeButtons = document.querySelectorAll("[data-mode]");

if (canvas) {
  const ctx = canvas.getContext("2d");
  const W = canvas.width;
  const H = canvas.height;

  // Simplified grid - 6x4
  const gridSize = 6;
  const cellSize = 60;
  const gridX = (W - gridSize * cellSize) / 2;
  const gridY = (H - 4 * cellSize) / 2;

  // Minimal agent data - 2 agents with original and refined paths
  const agent1PathOriginal = [
    { x: 0, y: 1 }, { x: 1, y: 1 }, { x: 2, y: 1 }, { x: 3, y: 1 }, { x: 4, y: 1 }, { x: 5, y: 1 }
  ];
  const agent2PathOriginal = [
    { x: 0, y: 2 }, { x: 1, y: 2 }, { x: 2, y: 2 }, { x: 3, y: 2 }, { x: 4, y: 2 }, { x: 5, y: 2 }
  ];
  
  // Refined paths that avoid conflict zone
  const agent1PathRefined = [
    { x: 0, y: 1 }, { x: 1, y: 1 }, { x: 2, y: 0 }, { x: 3, y: 0 }, { x: 4, y: 1 }, { x: 5, y: 1 }
  ];
  const agent2PathRefined = [
    { x: 0, y: 2 }, { x: 1, y: 2 }, { x: 2, y: 3 }, { x: 3, y: 3 }, { x: 4, y: 2 }, { x: 5, y: 2 }
  ];

  // Verify paths - agents stop before hitting obstacle
  const agent1PathVerify = [
    { x: 0, y: 1 }, { x: 1, y: 1 }
  ];
  const agent2PathVerify = [
    { x: 0, y: 2 }, { x: 1, y: 2 }
  ];

  let mode = "plan";
  let stepIndex = 0;
  let playing = true;
  let lastTick = 0;

  function toPx(gx, gy) {
    return {
      x: gridX + gx * cellSize + cellSize / 2,
      y: gridY + gy * cellSize + cellSize / 2,
    };
  }

  function drawMinimalGrid() {
    ctx.strokeStyle = "rgba(255,255,255,0.1)";
    ctx.lineWidth = 1;
    for (let i = 0; i <= gridSize; i++) {
      ctx.beginPath();
      ctx.moveTo(gridX + i * cellSize, gridY);
      ctx.lineTo(gridX + i * cellSize, gridY + 4 * cellSize);
      ctx.stroke();
    }
    for (let j = 0; j <= 4; j++) {
      ctx.beginPath();
      ctx.moveTo(gridX, gridY + j * cellSize);
      ctx.lineTo(gridX + gridSize * cellSize, gridY + j * cellSize);
      ctx.stroke();
    }
  }

  function drawPath(path, color, opacity = 0.5) {
    ctx.strokeStyle = color;
    ctx.globalAlpha = opacity;
    ctx.lineWidth = 2;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    const start = toPx(path[0].x, path[0].y);
    ctx.moveTo(start.x, start.y);
    for (let i = 1; i < path.length; i++) {
      const p = toPx(path[i].x, path[i].y);
      ctx.lineTo(p.x, p.y);
    }
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.globalAlpha = 1;
  }

  function drawAgent(path, color, label) {
    const pos = path[Math.min(stepIndex, path.length - 1)];
    const p = toPx(pos.x, pos.y);
    
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(p.x, p.y, 18, 0, Math.PI * 2);
    ctx.fill();
    
    ctx.fillStyle = "#fff";
    ctx.font = "bold 14px Arial";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(label, p.x, p.y);
  }

  function drawGoal(x, y, label) {
    const p = toPx(x, y);
    ctx.strokeStyle = "#ffd166";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(p.x, p.y, 8, 0, Math.PI * 2);
    ctx.stroke();
    
    ctx.fillStyle = "#ffd166";
    ctx.font = "9px Arial";
    ctx.textAlign = "center";
    ctx.fillText(label, p.x, p.y - 15);
  }

  function drawConflictZone() {
    const p = toPx(2.5, 1.5);
    ctx.strokeStyle = "#ef5350";
    ctx.fillStyle = "rgba(239, 83, 80, 0.15)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(p.x, p.y, 18, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
  }

  function drawObstacle() {
    const p1 = toPx(2, 1);
    const p2 = toPx(3, 2);
    ctx.fillStyle = "#555";
    ctx.strokeStyle = "#888";
    ctx.lineWidth = 2;
    ctx.fillRect(p1.x - 12, p1.y - 12, 24, 24);
    ctx.fillRect(p2.x - 12, p2.y - 12, 24, 24);
    ctx.strokeRect(p1.x - 12, p1.y - 12, 24, 24);
    ctx.strokeRect(p2.x - 12, p2.y - 12, 24, 24);
  }

  function drawSymmetryGroup() {
    // Group 1
    const p1 = toPx(agent1PathOriginal[stepIndex].x, agent1PathOriginal[stepIndex].y);
    const p2 = toPx(agent2PathOriginal[stepIndex].x, agent2PathOriginal[stepIndex].y);
    
    ctx.strokeStyle = "#4fc3f7";
    ctx.lineWidth = 3;
    ctx.setLineDash([5, 5]);
    ctx.beginPath();
    ctx.moveTo(p1.x, p1.y);
    ctx.lineTo(p2.x, p2.y);
    ctx.stroke();
    ctx.setLineDash([]);
  }

  function render() {
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = "#0a0e13";
    ctx.fillRect(0, 0, W, H);
    
    drawMinimalGrid();

    if (mode === "plan") {
      drawPath(agent1PathOriginal, "#66bb6a", 0.6);
      drawPath(agent2PathOriginal, "#4fc3f7", 0.6);
      drawGoal(5, 1, "G1");
      drawGoal(5, 2, "G2");
      drawAgent(agent1PathOriginal, "#66bb6a", "1");
      drawAgent(agent2PathOriginal, "#4fc3f7", "2");
      caption.textContent = "Plan: Agents follow conflict-free paths to their goals.";
    } else if (mode === "symmetry") {
      drawAgent(agent1PathOriginal, "#66bb6a", "1");
      drawAgent(agent2PathOriginal, "#4fc3f7", "2");
      drawSymmetryGroup();
      caption.textContent = "Symmetry: Agents in the same role are grouped (blue connection).";
    } else if (mode === "verify") {
      drawPath(agent1PathVerify, "#66bb6a", 0.4);
      drawPath(agent2PathVerify, "#4fc3f7", 0.4);
      drawObstacle();
      drawConflictZone();
      drawAgent(agent1PathVerify, "#66bb6a", "1");
      drawAgent(agent2PathVerify, "#4fc3f7", "2");
      caption.textContent = "Verify: Agents stop - detected obstacles (gray) blocking paths.";
    } else if (mode === "refine") {
      // Show old paths in faded color
      drawPath(agent1PathOriginal, "#888", 0.2);
      drawPath(agent2PathOriginal, "#888", 0.2);
      
      // Show new refined paths
      drawPath(agent1PathRefined, "#66bb6a", 0.7);
      drawPath(agent2PathRefined, "#4fc3f7", 0.7);
      
      drawAgent(agent1PathRefined, "#66bb6a", "1");
      drawAgent(agent2PathRefined, "#4fc3f7", "2");
      
      caption.textContent = "Refine: New paths (colored) avoid conflict zone, old paths (gray) discarded.";
    }
  }

  function tick(ts) {
    if (!lastTick) lastTick = ts;
    const elapsed = ts - lastTick;
    if (playing && elapsed > 600) {
      stepIndex++;
      lastTick = ts;
    }
    render();
    requestAnimationFrame(tick);
  }

  requestAnimationFrame(tick);

  modeButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      modeButtons.forEach((b) => b.classList.remove("is-active"));
      btn.classList.add("is-active");
      mode = btn.dataset.mode;
      stepIndex = 0;
    });
  });
}

// ==================== Shared Scenario Data (Global Scope) ====================
// Declare these as global variables so all canvas sections can access them
let symmetryScenarios, quotientComparisonScenarios, quotientKeyScenarios, verificationScenarios, refinementScenarios, verifyRefineLoopScenarios;

// Algorithm demo canvas
const algoCanvas = document.getElementById("algoCanvas");
const algoCaption = document.getElementById("algoCaption");
const algoSection = document.getElementById("planning");
const algoButtons = algoSection ? algoSection.querySelectorAll("[data-algo]") : [];
const algoPauseButton = algoSection ? algoSection.querySelector("[data-control='algo-pause']") : null;
const algoSurface = algoCanvas ? createHiResCanvas(algoCanvas) : null;

const debugDiv = document.getElementById('debugStatus');
if (debugDiv) {
  setTimeout(() => {
    debugDiv.innerHTML = `
      algoCanvas: ${algoCanvas ? '✓' : '✗'}<br>
      symmetryCanvas: ${document.getElementById('symmetryCanvas') ? '✓' : '✗'}<br>
      verifyCanvas: ${document.getElementById('verifyCanvas') ? '✓' : '✗'}<br>
      symmetryScenarios: ${typeof symmetryScenarios !== 'undefined' && symmetryScenarios ? symmetryScenarios.length + ' items' : '✗ UNDEFINED'}<br>
      Animation: ${algoCanvas ? '✓ Running' : '✗ Stopped'}
    `;
  }, 1000);
}

console.log('algoCanvas:', algoCanvas, 'algoCaption:', algoCaption, 'algoButtons:', algoButtons.length);

if (algoCanvas) {
  console.log('Initializing algoCanvas...');
  const ctx = algoSurface.ctx;
  const grid = 10;
  let cell = 32; // Will be adjusted based on canvas size
  let canvasWidth = 0;
  let canvasHeight = 0;
  let offsetX = 0;
  let offsetY = 0;
  let algoMode = "astar";
  let tick = 0;
  let algoPlaying = true;
  let lastAlgoTick = 0;

  function syncAlgoPauseButton() {
    if (!algoPauseButton) return;
    algoPauseButton.textContent = algoPlaying ? "Pause" : "Resume";
    algoPauseButton.classList.toggle("is-paused", !algoPlaying);
    algoPauseButton.setAttribute("aria-pressed", String(!algoPlaying));
  }

  function updateAlgoLayout() {
    const size = algoSurface.resize();
    canvasWidth = size.width;
    canvasHeight = size.height;
    // Responsive cell size: scale grid to fit canvas
    cell = Math.min(canvasWidth / (grid + 2), canvasHeight / (grid + 2), 40);
    cell = Math.max(cell, 16); // Min cell size of 16px
    offsetX = (canvasWidth - grid * cell) / 2;
    offsetY = (canvasHeight - grid * cell) / 2;
    return size;
  }

  // Calculate agent radius based on cell size
  function getAgentRadius(multiplier = 0.45) {
    return Math.max(7, Math.min(cell * multiplier, 15));
  }

  const astarStart = { x: 1, y: 1 };
  const astarGoal = { x: 8, y: 7 };
  const astarWalls = [
    { x: 3, y: 1 }, { x: 3, y: 2 }, { x: 3, y: 3 }, { x: 3, y: 4 },
    { x: 5, y: 5 }, { x: 6, y: 5 }, { x: 7, y: 5 },
  ];
  const astarPath = [
    { x: 1, y: 1 }, { x: 2, y: 1 }, { x: 2, y: 2 }, { x: 2, y: 3 }, { x: 2, y: 4 },
    { x: 2, y: 5 }, { x: 3, y: 5 }, { x: 4, y: 5 }, { x: 4, y: 6 }, { x: 5, y: 6 },
    { x: 6, y: 6 }, { x: 7, y: 6 }, { x: 8, y: 6 }, { x: 8, y: 7 },
  ];
  const astarSearchStages = [
    {
      label: "1) Initialize",
      current: { x: 1, y: 1 },
      closed: [],
      open: [{ x: 2, y: 1 }, { x: 1, y: 2 }],
      showPathLen: 0,
      caption: "A*: Start node selected. Open set gets valid neighbors.",
    },
    {
      label: "2) Expand Lowest f",
      current: { x: 2, y: 1 },
      closed: [{ x: 1, y: 1 }],
      open: [{ x: 1, y: 2 }, { x: 2, y: 2 }],
      showPathLen: 0,
      caption: "A*: Pop lowest-f node from open set; move it into closed set.",
    },
    {
      label: "3) Continue Expansion",
      current: { x: 2, y: 2 },
      closed: [{ x: 1, y: 1 }, { x: 2, y: 1 }],
      open: [{ x: 1, y: 2 }, { x: 2, y: 3 }],
      showPathLen: 0,
      caption: "A*: Evaluate neighbors and update open set scores.",
    },
    {
      label: "4) Push Along Corridor",
      current: { x: 2, y: 3 },
      closed: [{ x: 1, y: 1 }, { x: 2, y: 1 }, { x: 2, y: 2 }],
      open: [{ x: 1, y: 3 }, { x: 2, y: 4 }],
      showPathLen: 0,
      caption: "A*: Vertical wall blocks direct east moves, so search goes down.",
    },
    {
      label: "5) Reach Detour Row",
      current: { x: 2, y: 5 },
      closed: [{ x: 1, y: 1 }, { x: 2, y: 1 }, { x: 2, y: 2 }, { x: 2, y: 3 }, { x: 2, y: 4 }],
      open: [{ x: 1, y: 5 }, { x: 3, y: 5 }],
      showPathLen: 0,
      caption: "A*: Search reaches the gap and can now route around obstacles.",
    },
    {
      label: "6) Turn Toward Goal",
      current: { x: 4, y: 5 },
      closed: [{ x: 1, y: 1 }, { x: 2, y: 1 }, { x: 2, y: 2 }, { x: 2, y: 3 }, { x: 2, y: 4 }, { x: 2, y: 5 }, { x: 3, y: 5 }],
      open: [{ x: 4, y: 6 }, { x: 5, y: 6 }],
      showPathLen: 0,
      caption: "A*: Best frontier shifts diagonally toward the goal region.",
    },
    {
      label: "7) Goal Reached",
      current: { x: 8, y: 7 },
      closed: [{ x: 1, y: 1 }, { x: 2, y: 1 }, { x: 2, y: 2 }, { x: 2, y: 3 }, { x: 2, y: 4 }, { x: 2, y: 5 }, { x: 3, y: 5 }, { x: 4, y: 5 }, { x: 4, y: 6 }, { x: 5, y: 6 }, { x: 6, y: 6 }, { x: 7, y: 6 }, { x: 8, y: 6 }],
      open: [{ x: 7, y: 7 }],
      showPathLen: 0,
      caption: "A*: Goal dequeued from open set. Stop searching.",
    },
    {
      label: "8) Reconstruct Path",
      current: { x: 8, y: 7 },
      closed: [{ x: 1, y: 1 }, { x: 2, y: 1 }, { x: 2, y: 2 }, { x: 2, y: 3 }, { x: 2, y: 4 }, { x: 2, y: 5 }, { x: 3, y: 5 }, { x: 4, y: 5 }, { x: 4, y: 6 }, { x: 5, y: 6 }, { x: 6, y: 6 }, { x: 7, y: 6 }, { x: 8, y: 6 }],
      open: [],
      showPathLen: astarPath.length,
      caption: "A*: Follow parent pointers backward to produce final shortest path.",
    },
  ];
  const reservationStages = [
    {
      label: "1) Agent A planned first",
      aPos: { x: 2, y: 4 },
      bPos: { x: 2, y: 6 },
      reserved: [{ x: 3, y: 4 }, { x: 4, y: 4 }, { x: 5, y: 4 }],
      bPreview: [{ x: 2, y: 6 }, { x: 3, y: 5 }, { x: 4, y: 4 }, { x: 5, y: 4 }, { x: 6, y: 4 }],
      reroute: [],
      caption: "WHCA*: Agent A reserves a short time window on row y=4.",
    },
    {
      label: "2) Agent B checks reservations",
      aPos: { x: 3, y: 4 },
      bPos: { x: 3, y: 5 },
      reserved: [{ x: 3, y: 4 }, { x: 4, y: 4 }, { x: 5, y: 4 }],
      bPreview: [{ x: 2, y: 6 }, { x: 3, y: 5 }, { x: 4, y: 4 }, { x: 5, y: 4 }, { x: 6, y: 4 }],
      reroute: [],
      caption: "Agent B's shortest route intersects reserved cells (orange).",
    },
    {
      label: "3) Reservation-aware reroute",
      aPos: { x: 4, y: 4 },
      bPos: { x: 3, y: 6 },
      reserved: [{ x: 4, y: 4 }, { x: 5, y: 4 }, { x: 6, y: 4 }],
      bPreview: [{ x: 2, y: 6 }, { x: 3, y: 5 }, { x: 4, y: 4 }, { x: 5, y: 4 }, { x: 6, y: 4 }],
      reroute: [{ x: 2, y: 6 }, { x: 3, y: 6 }, { x: 4, y: 6 }, { x: 5, y: 5 }, { x: 6, y: 4 }],
      caption: "B is replanned through free-time cells instead of reserved row y=4.",
    },
    {
      label: "4) Conflict avoided",
      aPos: { x: 5, y: 4 },
      bPos: { x: 5, y: 5 },
      reserved: [{ x: 5, y: 4 }, { x: 6, y: 4 }, { x: 7, y: 4 }],
      bPreview: [],
      reroute: [{ x: 2, y: 6 }, { x: 3, y: 6 }, { x: 4, y: 6 }, { x: 5, y: 5 }, { x: 6, y: 4 }],
      caption: "Result: both agents progress without a same-time vertex conflict.",
    },
  ];

  const edgeSwapStages = [
    {
      label: "1) Opposite intents",
      aFrom: { x: 4, y: 4 }, aTo: { x: 5, y: 4 },
      bFrom: { x: 5, y: 4 }, bTo: { x: 4, y: 4 },
      resolved: null,
      caption: "Two agents intend to swap edges in the same timestep.",
    },
    {
      label: "2) Detect swap conflict",
      aFrom: { x: 4, y: 4 }, aTo: { x: 5, y: 4 },
      bFrom: { x: 5, y: 4 }, bTo: { x: 4, y: 4 },
      resolved: null,
      caption: "Edge-swap conflict detected: A->B and B->A are mutually unsafe.",
    },
    {
      label: "3) Priority resolve",
      aFrom: { x: 4, y: 4 }, aTo: { x: 5, y: 4 },
      bFrom: { x: 5, y: 4 }, bTo: { x: 5, y: 4 },
      resolved: "B waits",
      caption: "Sanitization: lower-priority agent waits; higher-priority move proceeds.",
    },
    {
      label: "4) Next timestep",
      aFrom: { x: 5, y: 4 }, aTo: { x: 6, y: 4 },
      bFrom: { x: 5, y: 4 }, bTo: { x: 4, y: 4 },
      resolved: "Safe progression",
      caption: "After one wait, both can continue without edge swap collision.",
    },
  ];

  const assignmentStages = [
    {
      label: "1) Build cost matrix",
      matrix: [
        [2, 5, 6],
        [4, 1, 3],
        [5, 4, 2],
      ],
      chosen: [],
      caption: "Hungarian setup: Manhattan distances form robot->shelf cost matrix.",
    },
    {
      label: "2) Solve matching",
      matrix: [
        [2, 5, 6],
        [4, 1, 3],
        [5, 4, 2],
      ],
      chosen: [[0, 0], [1, 1], [2, 2]],
      caption: "Hungarian algorithm chooses minimum total cost assignment.",
    },
    {
      label: "3) Commit assignments",
      matrix: [
        [2, 5, 6],
        [4, 1, 3],
        [5, 4, 2],
      ],
      chosen: [[0, 0], [1, 1], [2, 2]],
      caption: "Assignments become planner targets: R1->S1, R2->S2, R3->S3.",
    },
  ];

  // Conflict-resolution demo: two agents fetching shelves
  // Agent 1 (orange): moves to shelf at (2,5), then to goal at (8,1)
  // Agent 2 (blue): moves to shelf at (7,3), then to goal at (1,8)
  // They conflict at position (5,5) at the same time
  
  const cbsAgent1Shelf = { x: 2, y: 5, label: "S1" }; // Shelf 1
  const cbsAgent1Goal = { x: 8, y: 1, label: "G1" };  // Goal 1
  const cbsAgent2Shelf = { x: 7, y: 3, label: "S2" }; // Shelf 2
  const cbsAgent2Goal = { x: 1, y: 8, label: "G2" };  // Goal 2
  
  // Initial conflicting paths (both agents pass through (5,5) at same time step)
  const cbsAgent1Initial = [
    { x: 1, y: 7 }, { x: 2, y: 6 }, { x: 2, y: 5 }, { x: 3, y: 5 }, { x: 4, y: 5 }, 
    { x: 5, y: 5 }, { x: 6, y: 5 }, { x: 7, y: 4 }, { x: 8, y: 3 }, { x: 8, y: 2 }, { x: 8, y: 1 }
  ];
  const cbsAgent2Initial = [
    { x: 9, y: 2 }, { x: 8, y: 3 }, { x: 7, y: 4 }, { x: 6, y: 5 }, { x: 5, y: 5 },
    { x: 4, y: 5 }, { x: 3, y: 6 }, { x: 2, y: 7 }, { x: 1, y: 7 }, { x: 1, y: 8 }
  ];
  
  // Replanned paths after conflict-aware rerouting avoids (5,5)
  const cbsAgent1Replanned = [
    { x: 1, y: 7 }, { x: 2, y: 6 }, { x: 2, y: 5 }, { x: 3, y: 5 }, { x: 4, y: 5 },
    { x: 4, y: 4 }, { x: 5, y: 4 }, { x: 6, y: 4 }, { x: 7, y: 3 }, { x: 8, y: 2 }, { x: 8, y: 1 }
  ];
  const cbsAgent2Replanned = [
    { x: 9, y: 2 }, { x: 8, y: 3 }, { x: 7, y: 4 }, { x: 6, y: 5 }, { x: 5, y: 6 },
    { x: 4, y: 6 }, { x: 3, y: 6 }, { x: 2, y: 7 }, { x: 1, y: 7 }, { x: 1, y: 8 }
  ];

  // Symmetry Reduction Demo
  // Accurately show how agents are grouped into orbits by role and canonicalized
  symmetryScenarios = [
    {
      // Scenario 1: Initial state with labeled agents
      agents: [
        { x: 2, y: 3, role: 'idle', id: 'A', dir: '→' },
        { x: 6, y: 5, role: 'idle', id: 'B', dir: '↓' },
        { x: 4, y: 2, role: 'idle', id: 'C', dir: '←' },
      ],
      text: "Original State with 3 Idle Agents",
      caption: "State 1: Three idle agents → A at (2,3), B at (6,5), C at (4,2) with directions.",
    },
    {
      // Scenario 2: Detect role orbits
      agents: [
        { x: 2, y: 3, role: 'idle', id: 'A', dir: '→', highlight: true },
        { x: 6, y: 5, role: 'idle', id: 'B', dir: '↓', highlight: true },
        { x: 4, y: 2, role: 'idle', id: 'C', dir: '←', highlight: true },
      ],
      text: "Orbit Detection: All roles = IDLE (0,0)",
      caption: "Group agents by role type. All agents idle → Single orbit (green highlight).",
    },
    {
      // Scenario 3: Extract tuples
      agents: [
        { x: 2, y: 3, role: 'idle', id: 'A', dir: '→', showTuple: true },
        { x: 6, y: 5, role: 'idle', id: 'B', dir: '↓', showTuple: true },
        { x: 4, y: 2, role: 'idle', id: 'C', dir: '←', showTuple: true },
      ],
      text: "Extract Tuples: (x, y, dir, role)",
      tuples: ["A: (2, 3, 0, 0)", "B: (6, 5, 2, 0)", "C: (4, 2, 1, 0)"],
      caption: "Encode each agent as tuple (x-pos, y-pos, direction-code, role-code).",
    },
    {
      // Scenario 4: Sort tuples
      agents: [
        { x: 2, y: 3, role: 'idle', id: '1', dir: '→', canonical: true },
        { x: 4, y: 2, role: 'idle', id: '2', dir: '←', canonical: true },
        { x: 6, y: 5, role: 'idle', id: '3', dir: '↓', canonical: true },
      ],
      text: "Canonical Ordering (Sorted)",
      tuples: ["(2, 3, 0, 0)", "(4, 2, 1, 0)", "(6, 5, 2, 0)"],
      sorted: true,
      caption: "Sort tuples lexicographically → Canonical representative for quotient state.",
    },
    {
      // Scenario 5: Different permutation (State 2)
      agents: [
        { x: 4, y: 2, role: 'idle', id: 'A', dir: '←' },
        { x: 2, y: 3, role: 'idle', id: 'B', dir: '→' },
        { x: 6, y: 5, role: 'idle', id: 'C', dir: '↓' },
      ],
      text: "Different Agent Labels (Permutation)",
      caption: "State 2: Same positions, different naming → A(4,2), B(2,3), C(6,5).",
    },
    {
      // Scenario 6: Same orbit
      agents: [
        { x: 4, y: 2, role: 'idle', id: 'A', dir: '←', highlight: true },
        { x: 2, y: 3, role: 'idle', id: 'B', dir: '→', highlight: true },
        { x: 6, y: 5, role: 'idle', id: 'C', dir: '↓', highlight: true },
      ],
      text: "Orbit Detection: All roles = IDLE (0,0)",
      caption: "Re-check orbits. All idle again → Same single orbit (green highlight).",
    },
    {
      // Scenario 7: Extract and sort - same result
      agents: [
        { x: 2, y: 3, role: 'idle', id: '1', dir: '→', canonical: true },
        { x: 4, y: 2, role: 'idle', id: '2', dir: '←', canonical: true },
        { x: 6, y: 5, role: 'idle', id: '3', dir: '↓', canonical: true },
      ],
      text: "SAME Canonical Form After Sort",
      tuples: ["(2, 3, 0, 0)", "(4, 2, 1, 0)", "(6, 5, 2, 0)"],
      sorted: true,
      caption: "Extract & sort → IDENTICAL canonical form as State 1!",
    },
    {
      // Scenario 8: Equivalence
      agents: [
        { x: 4, y: 4, role: 'idle', id: '✓', size: 'large' },
      ],
      text: "State 1 ≡ State 2 (Symmetry Detected)",
      stateCount: "3! = 6 permutations",
      quotientCount: "→ 1 quotient state",
      caption: "Both states are symmetric permutations → Mapped to same quotient state!",
    },
    {
      // Scenario 9: Mixed roles example
      agents: [
        { x: 2, y: 2, role: 'idle', id: 'A', dir: '→' },
        { x: 6, y: 2, role: 'idle', id: 'B', dir: '←' },
        { x: 2, y: 6, role: 'carrying', id: 'C', dir: '↑' },
        { x: 6, y: 6, role: 'carrying', id: 'D', dir: '↓' },
      ],
      text: "Multi-Role Scenario",
      caption: "New state: 2 idle agents (blue) + 2 carrying agents (orange).",
    },
    {
      // Scenario 10: Separate orbits
      agents: [
        { x: 2, y: 2, role: 'idle', id: 'A', dir: '→', orbitA: true },
        { x: 6, y: 2, role: 'idle', id: 'B', dir: '←', orbitA: true },
        { x: 2, y: 6, role: 'carrying', id: 'C', dir: '↑', orbitB: true },
        { x: 6, y: 6, role: 'carrying', id: 'D', dir: '↓', orbitB: true },
      ],
      text: "Orbit 1 (IDLE) | Orbit 2 (CARRYING)",
      caption: "Different roles → Two separate orbits. Blue border = idle, orange = carrying.",
    },
    {
      // Scenario 11: Canonicalize each orbit
      agents: [
        { x: 2, y: 2, role: 'idle', id: '1', dir: '→', orbitA: true, canonical: true },
        { x: 6, y: 2, role: 'idle', id: '2', dir: '←', orbitA: true, canonical: true },
        { x: 2, y: 6, role: 'carrying', id: '1', dir: '↑', orbitB: true, canonical: true },
        { x: 6, y: 6, role: 'carrying', id: '2', dir: '↓', orbitB: true, canonical: true },
      ],
      text: "Canonicalize Each Orbit Independently",
      tuples: ["Idle orbit: [(2,2,0,0), (6,2,1,0)]", "Carry orbit: [(2,6,3,1), (6,6,2,1)]"],
      caption: "Sort tuples within each orbit separately to get canonical form.",
    },
    {
      // Scenario 12: State space reduction
      agents: [
        { x: 4, y: 4, role: 'idle', id: '✓', size: 'large' },
      ],
      text: "Symmetry Reduction Achieved",
      stateCount: "2! × 2! = 4 permutations",
      quotientCount: "→ 1 quotient state",
      caption: "4 possible labelings of (2 idle + 2 carrying) → Reduced to 1 quotient state!",
    },
  ];

  function toCell(px, py) {
    return {
      x: offsetX + px * cell,
      y: offsetY + py * cell,
    };
  }

  function drawGrid() {
    ctx.strokeStyle = "rgba(255,255,255,0.08)";
    for (let i = 0; i <= grid; i++) {
      const x = offsetX + i * cell;
      ctx.beginPath();
      ctx.moveTo(x, offsetY);
      ctx.lineTo(x, offsetY + grid * cell);
      ctx.stroke();
      const y = offsetY + i * cell;
      ctx.beginPath();
      ctx.moveTo(offsetX, y);
      ctx.lineTo(offsetX + grid * cell, y);
      ctx.stroke();
    }
  }

  function drawCell(pos, color) {
    const p = toCell(pos.x, pos.y);
    ctx.fillStyle = color;
    ctx.fillRect(p.x + 2, p.y + 2, cell - 4, cell - 4);
  }

  function drawAStar() {
    const stage = astarSearchStages[tick % astarSearchStages.length];

    function manhattan(a, b) {
      return Math.abs(a.x - b.x) + Math.abs(a.y - b.y);
    }

    // Obstacles
    astarWalls.forEach((w) => drawCell(w, "#24313d"));

    // Closed and open set overlays
    stage.closed.forEach((p) => drawCell(p, "rgba(124,77,255,0.35)"));
    stage.open.forEach((p) => drawCell(p, "rgba(79,195,247,0.45)"));

    // Final path (shown only in reconstruction stage)
    if (stage.showPathLen > 0) {
      astarPath.slice(0, stage.showPathLen).forEach((p) => drawCell(p, "rgba(255,200,100,0.75)"));
    }

    // Start/goal + current node
    drawCell(astarStart, "#66bb6a");
    drawCell(astarGoal, "#ffd166");
    drawCell(stage.current, "#ff8a65");

    // Draw f = g + h hints for up to 3 open nodes
    const hintNodes = stage.open.slice(0, 3);
    hintNodes.forEach((node) => {
      const p = toCell(node.x, node.y);
      const g = manhattan(astarStart, node);
      const h = manhattan(node, astarGoal);
      const f = g + h;
      ctx.fillStyle = "rgba(255,255,255,0.85)";
      ctx.font = `${Math.max(9, Math.floor(cell * 0.22))}px monospace`;
      ctx.textAlign = "left";
      ctx.textBaseline = "top";
      ctx.fillText(`f${f}`, p.x + 4, p.y + 3);
    });

    // Labels on start/goal/current
    [
      { pos: astarStart, txt: "S", color: "#0f1318" },
      { pos: astarGoal, txt: "G", color: "#0f1318" },
      { pos: stage.current, txt: "C", color: "#0f1318" },
    ].forEach((item) => {
      const p = toCell(item.pos.x, item.pos.y);
      ctx.fillStyle = item.color;
      ctx.font = `bold ${Math.max(10, Math.floor(cell * 0.35))}px monospace`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(item.txt, p.x + cell / 2, p.y + cell / 2);
    });

    // Compact legend panel (placed outside the grid area when possible)
    const legendW = Math.min(Math.max(190, cell * 6.6), Math.max(190, canvasWidth - 24));
    const legendH = 104;
    let legendX = offsetX + 6;
    let legendY = offsetY - legendH - 8; // preferred: above grid

    // Fallback 1: below grid if above is not available
    if (legendY < 8) {
      legendY = offsetY + grid * cell + 8;
    }
    // Fallback 2: right of grid if below also doesn't fit
    if (legendY + legendH > canvasHeight - 8) {
      legendX = offsetX + grid * cell + 8;
      legendY = offsetY + 6;
    }
    // Final clamp to viewport bounds
    legendX = Math.max(8, Math.min(legendX, canvasWidth - legendW - 8));
    legendY = Math.max(8, Math.min(legendY, canvasHeight - legendH - 8));

    ctx.fillStyle = "rgba(12,18,27,0.86)";
    ctx.fillRect(legendX, legendY, legendW, legendH);
    ctx.strokeStyle = "rgba(255,255,255,0.16)";
    ctx.lineWidth = 1;
    ctx.strokeRect(legendX, legendY, legendW, legendH);

    const legendItems = [
      ["#ff8a65", "Current"],
      ["rgba(79,195,247,0.65)", "Open Set"],
      ["rgba(124,77,255,0.65)", "Closed Set"],
      ["rgba(255,200,100,0.9)", "Final Path"],
    ];
    legendItems.forEach((entry, i) => {
      const y = legendY + 27 + i * 18;
      ctx.fillStyle = entry[0];
      ctx.fillRect(legendX + 10, y - 9, 12, 12);
      ctx.fillStyle = "rgba(255,255,255,0.92)";
      ctx.font = "11px monospace";
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      ctx.fillText(entry[1], legendX + 28, y - 2);
    });
    ctx.fillStyle = "rgba(255,255,255,0.96)";
    ctx.font = "bold 12px monospace";
    ctx.fillText(stage.label, legendX + 10, legendY + 14);

    algoCaption.textContent = stage.caption;
  }

  function drawPrioritized() {
    // Phase 1 (tick 0-8): Show initial conflicting paths
    // Phase 2 (tick 9-18): Show replanned conflict-free paths
    const phase1Duration = 9;
    const phase2Duration = 10;
    const totalDuration = phase1Duration + phase2Duration;
    
    const currentTick = tick % totalDuration;
    const isPhase1 = currentTick < phase1Duration;
    
    if (isPhase1) {
      // Phase 1: Show initial paths with conflict
      const t = Math.min(currentTick, cbsAgent1Initial.length - 1);
      
      // Draw shelves and goals
      const pS1 = toCell(cbsAgent1Shelf.x, cbsAgent1Shelf.y);
      const pG1 = toCell(cbsAgent1Goal.x, cbsAgent1Goal.y);
      const pS2 = toCell(cbsAgent2Shelf.x, cbsAgent2Shelf.y);
      const pG2 = toCell(cbsAgent2Goal.x, cbsAgent2Goal.y);
      
      // Draw shelf locations (green)
      ctx.fillStyle = "#66bb6a";
      ctx.fillRect(pS1.x + 4, pS1.y + 4, cell - 8, cell - 8);
      ctx.fillStyle = "#fff";
      ctx.font = "10px monospace";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("S1", pS1.x + cell/2, pS1.y + cell/2);
      
      ctx.fillStyle = "#66bb6a";
      ctx.fillRect(pS2.x + 4, pS2.y + 4, cell - 8, cell - 8);
      ctx.fillStyle = "#fff";
      ctx.fillText("S2", pS2.x + cell/2, pS2.y + cell/2);
      
      // Draw goal locations (gold outline)
      ctx.strokeStyle = "#ffd166";
      ctx.lineWidth = 2;
      ctx.strokeRect(pG1.x + 4, pG1.y + 4, cell - 8, cell - 8);
      ctx.fillStyle = "#fff";
      ctx.font = "10px monospace";
      ctx.fillText("G1", pG1.x + cell/2, pG1.y + cell/2);
      
      ctx.strokeStyle = "#ffd166";
      ctx.strokeRect(pG2.x + 4, pG2.y + 4, cell - 8, cell - 8);
      ctx.fillText("G2", pG2.x + cell/2, pG2.y + cell/2);
      
      // Draw full paths in faint colors
      cbsAgent1Initial.forEach((p) => {
        drawCell(p, "rgba(240,140,58,0.15)");
      });
      cbsAgent2Initial.forEach((p) => {
        drawCell(p, "rgba(79,195,247,0.15)");
      });
      
      // Highlight conflict zone prominently at (5,5)
      drawCell({ x: 5, y: 5 }, "rgba(239,83,80,0.9)");
      
      // Draw current agent positions with labels
      const a = cbsAgent1Initial[t];
      const b = cbsAgent2Initial[t];
      const pA = toCell(a.x, a.y);
      const pB = toCell(b.x, b.y);
      
      // Agent 1 (orange) - fetching from shelf
      ctx.fillStyle = "#f08c3a";
      ctx.beginPath();
      ctx.arc(pA.x + cell/2, pA.y + cell/2, getAgentRadius(), 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = "#fff";
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.fillStyle = "#fff";
      ctx.font = "bold 16px monospace";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("1", pA.x + cell/2, pA.y + cell/2);
      
      // Agent 2 (blue) - fetching from shelf
      ctx.fillStyle = "#4fc3f7";
      ctx.beginPath();
      ctx.arc(pB.x + cell/2, pB.y + cell/2, getAgentRadius(), 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = "#fff";
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.fillStyle = "#fff";
      ctx.font = "bold 16px monospace";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("2", pB.x + cell/2, pB.y + cell/2);
      
      if (t >= 5) {
        algoCaption.textContent = "Cooperative planner phase 1: initial trajectories conflict at (5,5), time step " + t + ".";
      } else {
        algoCaption.textContent = "Cooperative planner phase 1: independent plans before reservation and constraint handling.";
      }
    } else {
      // Phase 2: Show replanned paths
      const t = Math.min(currentTick - phase1Duration, cbsAgent1Replanned.length - 1);
      
      // Draw shelves and goals
      const pS1 = toCell(cbsAgent1Shelf.x, cbsAgent1Shelf.y);
      const pG1 = toCell(cbsAgent1Goal.x, cbsAgent1Goal.y);
      const pS2 = toCell(cbsAgent2Shelf.x, cbsAgent2Shelf.y);
      const pG2 = toCell(cbsAgent2Goal.x, cbsAgent2Goal.y);
      
      // Draw shelf locations (green)
      ctx.fillStyle = "#66bb6a";
      ctx.fillRect(pS1.x + 4, pS1.y + 4, cell - 8, cell - 8);
      ctx.fillStyle = "#fff";
      ctx.font = "10px monospace";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("S1", pS1.x + cell/2, pS1.y + cell/2);
      
      ctx.fillStyle = "#66bb6a";
      ctx.fillRect(pS2.x + 4, pS2.y + 4, cell - 8, cell - 8);
      ctx.fillStyle = "#fff";
      ctx.fillText("S2", pS2.x + cell/2, pS2.y + cell/2);
      
      // Draw goal locations (gold outline)
      ctx.strokeStyle = "#ffd166";
      ctx.lineWidth = 2;
      ctx.strokeRect(pG1.x + 4, pG1.y + 4, cell - 8, cell - 8);
      ctx.fillStyle = "#fff";
      ctx.font = "10px monospace";
      ctx.fillText("G1", pG1.x + cell/2, pG1.y + cell/2);
      
      ctx.strokeStyle = "#ffd166";
      ctx.strokeRect(pG2.x + 4, pG2.y + 4, cell - 8, cell - 8);
      ctx.fillText("G2", pG2.x + cell/2, pG2.y + cell/2);
      
      // Draw old conflicting paths in very faint gray
      cbsAgent1Initial.forEach((p) => {
        drawCell(p, "rgba(150,150,150,0.08)");
      });
      cbsAgent2Initial.forEach((p) => {
        drawCell(p, "rgba(150,150,150,0.08)");
      });
      
      // Draw new replanned paths with full color
      cbsAgent1Replanned.forEach((p, i) => {
        if (i < t) {
          drawCell(p, "rgba(240,140,58,0.4)");
        }
      });
      cbsAgent2Replanned.forEach((p, i) => {
        if (i < t) {
          drawCell(p, "rgba(79,195,247,0.4)");
        }
      });
      
      // Draw constraint zone (the avoided conflict area) with warning color
      drawCell({ x: 5, y: 5 }, "rgba(255,152,0,0.4)");
      
      // Draw current agent positions
      const a = cbsAgent1Replanned[t];
      const b = cbsAgent2Replanned[t];
      const pA = toCell(a.x, a.y);
      const pB = toCell(b.x, b.y);
      
      // Agent 1 (orange)
      ctx.fillStyle = "#f08c3a";
      ctx.beginPath();
      ctx.arc(pA.x + cell/2, pA.y + cell/2, getAgentRadius(), 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = "#fff";
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.fillStyle = "#fff";
      ctx.font = "bold 16px monospace";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("1", pA.x + cell/2, pA.y + cell/2);
      
      // Agent 2 (blue)
      ctx.fillStyle = "#4fc3f7";
      ctx.beginPath();
      ctx.arc(pB.x + cell/2, pB.y + cell/2, getAgentRadius(), 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = "#fff";
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.fillStyle = "#fff";
      ctx.font = "bold 16px monospace";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("2", pB.x + cell/2, pB.y + cell/2);
      
      if (t < 4) {
        algoCaption.textContent = "Cooperative planner phase 2: reservation-aware rerouting and timed occupancy checks avoid (5,5).";
      } else {
        algoCaption.textContent = "Cooperative planner phase 2: conflict resolved and both agents reach goals safely.";
      }
    }
  }

  function drawReservation() {
    const stage = reservationStages[tick % reservationStages.length];

    // Reserved time-window cells
    stage.reserved.forEach((p) => drawCell(p, "rgba(255,152,0,0.55)"));

    // Naive B route (shows blocked intention)
    stage.bPreview.forEach((p) => drawCell(p, "rgba(239,83,80,0.20)"));

    // Rerouted B route
    stage.reroute.forEach((p) => drawCell(p, "rgba(102,187,106,0.32)"));

    // Agent A
    const pA = toCell(stage.aPos.x, stage.aPos.y);
    ctx.fillStyle = "#f08c3a";
    ctx.beginPath();
    ctx.arc(pA.x + cell/2, pA.y + cell/2, getAgentRadius(), 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#fff";
    ctx.font = "bold 13px monospace";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText("A", pA.x + cell/2, pA.y + cell/2);

    // Agent B
    const pB = toCell(stage.bPos.x, stage.bPos.y);
    ctx.fillStyle = "#4fc3f7";
    ctx.beginPath();
    ctx.arc(pB.x + cell/2, pB.y + cell/2, getAgentRadius(), 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#fff";
    ctx.fillText("B", pB.x + cell/2, pB.y + cell/2);

    // Legend
    ctx.fillStyle = "rgba(12,18,27,0.84)";
    ctx.fillRect(offsetX + 8, offsetY + 8, Math.min(270, cell * 7.4), 88);
    ctx.strokeStyle = "rgba(255,255,255,0.15)";
    ctx.strokeRect(offsetX + 8, offsetY + 8, Math.min(270, cell * 7.4), 88);
    const items = [
      ["rgba(255,152,0,0.85)", "Reserved window"],
      ["rgba(239,83,80,0.85)", "Blocked naive route"],
      ["rgba(102,187,106,0.85)", "Replanned route"],
    ];
    items.forEach((entry, i) => {
      const y = offsetY + 28 + i * 20;
      ctx.fillStyle = entry[0];
      ctx.fillRect(offsetX + 18, y - 8, 12, 12);
      ctx.fillStyle = "rgba(255,255,255,0.92)";
      ctx.font = "11px monospace";
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      ctx.fillText(entry[1], offsetX + 36, y - 1);
    });

    algoCaption.textContent = stage.caption;
  }

  function drawEdgeSwap() {
    const stage = edgeSwapStages[tick % edgeSwapStages.length];
    const aFrom = toCell(stage.aFrom.x, stage.aFrom.y);
    const aTo = toCell(stage.aTo.x, stage.aTo.y);
    const bFrom = toCell(stage.bFrom.x, stage.bFrom.y);
    const bTo = toCell(stage.bTo.x, stage.bTo.y);

    function drawArrow(fromCell, toCell, color) {
      const x1 = fromCell.x + cell/2;
      const y1 = fromCell.y + cell/2;
      const x2 = toCell.x + cell/2;
      const y2 = toCell.y + cell/2;
      ctx.strokeStyle = color;
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.stroke();
      const ang = Math.atan2(y2 - y1, x2 - x1);
      const ah = Math.max(6, cell * 0.2);
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.moveTo(x2, y2);
      ctx.lineTo(x2 - ah * Math.cos(ang - 0.35), y2 - ah * Math.sin(ang - 0.35));
      ctx.lineTo(x2 - ah * Math.cos(ang + 0.35), y2 - ah * Math.sin(ang + 0.35));
      ctx.closePath();
      ctx.fill();
    }

    // Conflict highlight between swap cells
    drawCell(stage.aFrom, "rgba(239,83,80,0.22)");
    drawCell({ x: stage.aTo.x, y: stage.aTo.y }, "rgba(239,83,80,0.22)");
    drawArrow(aFrom, aTo, "#f08c3a");
    drawArrow(bFrom, bTo, "#4fc3f7");

    // Agent markers
    [
      { p: aFrom, c: "#f08c3a", id: "A" },
      { p: bFrom, c: "#4fc3f7", id: "B" },
    ].forEach((agent) => {
      ctx.fillStyle = agent.c;
      ctx.beginPath();
      ctx.arc(agent.p.x + cell/2, agent.p.y + cell/2, getAgentRadius(), 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "#fff";
      ctx.font = "bold 13px monospace";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(agent.id, agent.p.x + cell/2, agent.p.y + cell/2);
    });

    // Status strip
    ctx.fillStyle = "rgba(12,18,27,0.86)";
    ctx.fillRect(offsetX + 8, offsetY + 8, Math.min(300, cell * 8), 34);
    ctx.strokeStyle = "rgba(255,255,255,0.15)";
    ctx.strokeRect(offsetX + 8, offsetY + 8, Math.min(300, cell * 8), 34);
    ctx.fillStyle = stage.resolved ? "#81c784" : "#ef9a9a";
    ctx.font = "bold 12px monospace";
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    const status = stage.resolved ? `Resolve: ${stage.resolved}` : "Detecting edge-swap conflict";
    ctx.fillText(`${stage.label} | ${status}`, offsetX + 14, offsetY + 25);

    algoCaption.textContent = stage.caption;
  }

  function drawAssignment() {
    const stage = assignmentStages[tick % assignmentStages.length];

    const robots = [{ x: 1, y: 2, id: "R1" }, { x: 1, y: 5, id: "R2" }, { x: 1, y: 8, id: "R3" }];
    const shelves = [{ x: 8, y: 2, id: "S1" }, { x: 8, y: 5, id: "S2" }, { x: 8, y: 8, id: "S3" }];

    robots.forEach((r) => {
      const p = toCell(r.x, r.y);
      ctx.fillStyle = "#4fc3f7";
      ctx.beginPath();
      ctx.arc(p.x + cell/2, p.y + cell/2, getAgentRadius(), 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "#fff";
      ctx.font = "bold 11px monospace";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(r.id, p.x + cell/2, p.y + cell/2);
    });

    shelves.forEach((s) => {
      const p = toCell(s.x, s.y);
      ctx.fillStyle = "#66bb6a";
      ctx.fillRect(p.x + 4, p.y + 4, cell - 8, cell - 8);
      ctx.fillStyle = "#fff";
      ctx.font = "bold 11px monospace";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(s.id, p.x + cell/2, p.y + cell/2);
    });

    // Draw selected assignments as lines
    stage.chosen.forEach(([ri, si]) => {
      const pr = toCell(robots[ri].x, robots[ri].y);
      const ps = toCell(shelves[si].x, shelves[si].y);
      ctx.strokeStyle = "#ffd166";
      ctx.lineWidth = 2.8;
      ctx.beginPath();
      ctx.moveTo(pr.x + cell/2, pr.y + cell/2);
      ctx.lineTo(ps.x + cell/2, ps.y + cell/2);
      ctx.stroke();
    });

    // Matrix panel
    const panelW = Math.min(240, cell * 6.7);
    const panelH = 132;
    const panelX = Math.max(offsetX + 6, offsetX + grid * cell - panelW - 6);
    const panelY = offsetY + 6;
    ctx.fillStyle = "rgba(12,18,27,0.88)";
    ctx.fillRect(panelX, panelY, panelW, panelH);
    ctx.strokeStyle = "rgba(255,255,255,0.15)";
    ctx.strokeRect(panelX, panelY, panelW, panelH);
    ctx.fillStyle = "rgba(255,255,255,0.95)";
    ctx.font = "bold 12px monospace";
    ctx.textAlign = "left";
    ctx.textBaseline = "top";
    ctx.fillText(stage.label, panelX + 10, panelY + 8);
    ctx.font = "11px monospace";
    const cellW = 36;
    const startX = panelX + 48;
    const startY = panelY + 32;

    ["S1", "S2", "S3"].forEach((h, j) => ctx.fillText(h, startX + j * cellW + 10, startY - 16));
    ["R1", "R2", "R3"].forEach((h, i) => ctx.fillText(h, startX - 24, startY + i * 24 + 4));

    stage.matrix.forEach((row, i) => {
      row.forEach((val, j) => {
        const isChosen = stage.chosen.some(([ri, sj]) => ri === i && sj === j);
        if (isChosen) {
          ctx.fillStyle = "rgba(255,209,102,0.35)";
          ctx.fillRect(startX + j * cellW - 4, startY + i * 24 - 2, 28, 18);
        }
        ctx.fillStyle = "rgba(255,255,255,0.92)";
        ctx.fillText(String(val), startX + j * cellW + 4, startY + i * 24 + 2);
      });
    });

    algoCaption.textContent = stage.caption;
  }

  function drawSymmetry() {
    const scenarioIndex = tick % symmetryScenarios.length;
    const scenario = symmetryScenarios[scenarioIndex];
    
    // Draw agents
    scenario.agents.forEach((agent) => {
      const p = toCell(agent.x, agent.y);
      
      // Determine color based on role
      let color = agent.role === 'carrying' ? '#f08c3a' : '#4fc3f7';
      
      // Draw highlighting for orbit grouping
      if (agent.highlight) {
        ctx.fillStyle = 'rgba(102,187,106,0.3)';
        ctx.fillRect(p.x - 2, p.y - 2, cell + 4, cell + 4);
      }
      
      // Draw orbit borders
      if (agent.orbitA) {
        ctx.strokeStyle = '#4fc3f7';
        ctx.lineWidth = 2;
        ctx.strokeRect(p.x - 2, p.y - 2, cell + 4, cell + 4);
      }
      
      if (agent.orbitB) {
        ctx.strokeStyle = '#f08c3a';
        ctx.lineWidth = 2;
        ctx.strokeRect(p.x - 2, p.y - 2, cell + 4, cell + 4);
      }
      
      // Draw agent circle
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(p.x + cell/2, p.y + cell/2, agent.size === "large" ? 18 : 15, 0, Math.PI * 2);
      ctx.fill();
      
      // Draw direction arrow or ID
      ctx.fillStyle = '#fff';
      ctx.font = agent.canonical ? 'bold 20px monospace' : 'bold 20px monospace';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      
      if (agent.canonical) {
        ctx.fillStyle = '#66bb6a';
      }
      
      ctx.fillText(agent.id, p.x + cell/2, p.y + cell/2);
      
      // Draw direction below agent for tuple scenarios
      if (agent.dir && agent.showTuple) {
        ctx.fillStyle = 'rgba(255,255,255,0.6)';
        ctx.font = '11px monospace';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        ctx.fillText(agent.dir, p.x + cell/2, p.y + cell + 3);
      }
    });
    
    // Draw text label (for role info)
    if (scenario.text) {
      ctx.fillStyle = 'rgba(255,255,255,0.95)';
      ctx.font = "bold 13px monospace";
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.fillText(scenario.text, canvasWidth / 2, 20);
    }
    
    // Draw tuples - positioned in lower section
    if (scenario.tuples) {
      ctx.fillStyle = scenario.sorted ? '#66bb6a' : 'rgba(255,255,255,0.85)';
      ctx.font = "14px monospace";
      ctx.textAlign = 'left';
      ctx.textBaseline = 'top';
      
      const startX = 80;
      const startY = 450;
      
      scenario.tuples.forEach((tuple, i) => {
        const y = startY + i * 38;
        ctx.fillText(tuple, startX, y);
      });
      
      if (scenario.sorted) {
        // Draw "sorted" arrow and label
        ctx.strokeStyle = '#66bb6a';
        ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.moveTo(50, startY - 25);
        ctx.lineTo(50, startY - 5);
        ctx.stroke();
        
        // Arrowhead
        ctx.beginPath();
        ctx.moveTo(50, startY - 5);
        ctx.lineTo(44, startY - 15);
        ctx.lineTo(56, startY - 15);
        ctx.closePath();
        ctx.fillStyle = '#66bb6a';
        ctx.fill();
        
        ctx.fillStyle = '#66bb6a';
        ctx.font = "bold 13px monospace";
        ctx.textAlign = 'center';
        ctx.textBaseline = 'bottom';
        ctx.fillText('SORTED', 50, startY - 32);
      }
    }
    
    // Draw state space reduction info
    if (scenario.stateCount) {
      ctx.fillStyle = 'rgba(255,255,255,0.95)';
      ctx.font = "bold 16px monospace";
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(scenario.stateCount, canvasWidth / 2, 200);
      
      // Draw arrow
      ctx.strokeStyle = '#66bb6a';
      ctx.lineWidth = 5;
      ctx.beginPath();
      ctx.moveTo(canvasWidth / 2, 230);
      ctx.lineTo(canvasWidth / 2, 280);
      ctx.stroke();
      
      // Draw arrowhead
      ctx.beginPath();
      ctx.moveTo(canvasWidth / 2, 280);
      ctx.lineTo(canvasWidth / 2 - 12, 265);
      ctx.lineTo(canvasWidth / 2 + 12, 265);
      ctx.closePath();
      ctx.fillStyle = '#66bb6a';
      ctx.fill();
      
      ctx.fillStyle = '#66bb6a';
      ctx.font = "bold 16px monospace";
      ctx.fillText(scenario.quotientCount, canvasWidth / 2, 315);
    }
    
    algoCaption.textContent = scenario.caption;
  }

  // Quotient State Comparison scenarios
  quotientComparisonScenarios = [
    {
      agents: [
        { x: 1, y: 1, id: 'A' },
        { x: 3, y: 3, id: 'B' },
      ],
      caption: "Initial quotient state: Two agents at positions A(1,1) and B(3,3).",
    },
    {
      agents: [
        { x: 2, y: 2, id: 'A' },
        { x: 4, y: 4, id: 'B' },
      ],
      caption: "Quotient transition: Agents move closer to their goals.",
    },
    {
      agents: [
        { x: 3, y: 3, id: 'A' },
        { x: 5, y: 5, id: 'B' },
      ],
      caption: "Final quotient state: Agents reach their goal positions.",
    },
  ];

  // Verification Demo scenarios
  verificationScenarios = [
    {
      obstacles: [
        { x: 3, y: 3 },
        { x: 5, y: 5 },
      ],
      agents: [
        { x: 1, y: 1, id: 'A' },
        { x: 7, y: 7, id: 'B' },
      ],
      caption: "Verification: Initial state with agents and obstacles (gray blocks).",
    },
    {
      obstacles: [
        { x: 3, y: 3 },
        { x: 5, y: 5 },
      ],
      agents: [
        { x: 2, y: 2, id: 'A', stopped: true },
        { x: 6, y: 6, id: 'B', stopped: true },
      ],
      caption: "Verification: Agents (red) stop before obstacles - safety verified!",
    },
  ];

  refinementScenarios = [
    {
      unsafe: true,
      path: [
        { x: 1, y: 1 }, { x: 2, y: 1 }, { x: 3, y: 1 }, { x: 4, y: 1 }, { x: 5, y: 1 }
      ],
      constraint: null,
      caption: "Refinement Step 1: Unsafe path detected during verification.",
    },
    {
      unsafe: true,
      path: [
        { x: 1, y: 1 }, { x: 2, y: 1 }, { x: 3, y: 1 }, { x: 4, y: 1 }, { x: 5, y: 1 }
      ],
      constraint: { x: 3, y: 1, t: 2, label: "Constraint:\n(3,1,t=2)" },
      caption: "Refinement Step 2: Extract constraint from counterexample - block (3,1) at time step 2.",
    },
    {
      unsafe: false,
      path: [
        { x: 1, y: 1 }, { x: 2, y: 1 }, { x: 2, y: 2 }, { x: 3, y: 2 }, { x: 4, y: 2 }, { x: 5, y: 2 }
      ],
      constraint: { x: 3, y: 1, t: 2, label: "Constraint:\n(3,1,t=2)" },
      caption: "Refinement Step 3: Replan path avoiding constraint - new safe path found!",
    },
    {
      unsafe: false,
      path: [
        { x: 1, y: 1 }, { x: 2, y: 1 }, { x: 2, y: 2 }, { x: 3, y: 2 }, { x: 4, y: 2 }, { x: 5, y: 2 }
      ],
      constraint: { x: 3, y: 1, t: 2, label: "Constraint:\n(3,1,t=2)" },
      caption: "Refinement Step 4: Verification on new plan passes - refinement complete!",
    },
  ];

  quotientKeyScenarios = [
    {
      title: "Raw Labeled State",
      leftLabel: "State A",
      rightLabel: "State B (same roles, swapped labels)",
      rawA: "[(A:2,3,UP,idle),(B:6,5,DOWN,idle),(C:4,2,RIGHT,idle)]",
      rawB: "[(A:4,2,RIGHT,idle),(B:2,3,UP,idle),(C:6,5,DOWN,idle)]",
      keyA: "canonical(A)=((2,3,0,0),(4,2,1,0),(6,5,2,0))",
      keyB: "canonical(B)=((2,3,0,0),(4,2,1,0),(6,5,2,0))",
      equal: true,
      caption: "Different labels, same role orbit permutation -> identical quotient key.",
    },
    {
      title: "Role-Different State",
      leftLabel: "State C",
      rightLabel: "State D (role changed)",
      rawA: "[(A:2,3,UP,idle),(B:6,5,DOWN,carry_req)]",
      rawB: "[(A:2,3,UP,carry_req),(B:6,5,DOWN,idle)]",
      keyA: "canonical(C)=(((2,3,0,0),),((6,5,2,1),))",
      keyB: "canonical(D)=(((2,3,0,1),),((6,5,2,0),))",
      equal: false,
      caption: "Role change alters orbit partition -> quotient keys are different.",
    },
  ];

  verifyRefineLoopScenarios = [
    {
      phase: "Step 1 - Verify",
      safe: false,
      agents: [
        { x: 2, y: 6, id: "A", color: "#4fc3f7" },
        { x: 6, y: 2, id: "B", color: "#ab47bc" },
      ],
      pathA: [{ x: 2, y: 6 }, { x: 3, y: 5 }, { x: 4, y: 4 }, { x: 5, y: 3 }],
      pathB: [{ x: 6, y: 2 }, { x: 5, y: 3 }, { x: 4, y: 4 }, { x: 3, y: 5 }],
      conflict: { type: "vertex", x: 4, y: 4 },
      caption: "Step 1 (Verify): Planned trajectories collide at (4,4), so the run is UNSAFE.",
    },
    {
      phase: "Step 2 - Extract Conflict",
      safe: false,
      agents: [
        { x: 2, y: 6, id: "A", color: "#4fc3f7" },
        { x: 6, y: 2, id: "B", color: "#ab47bc" },
      ],
      pathA: [{ x: 2, y: 6 }, { x: 3, y: 5 }, { x: 4, y: 4 }, { x: 5, y: 3 }],
      pathB: [{ x: 6, y: 2 }, { x: 5, y: 3 }, { x: 4, y: 4 }, { x: 3, y: 5 }],
      conflict: { type: "vertex", x: 4, y: 4, label: "conflict: vertex@t=2" },
      caption: "Step 2 (Extract): Counterexample trace yields a vertex conflict for refinement.",
    },
    {
      phase: "Step 3 - Add Constraint",
      safe: false,
      agents: [
        { x: 2, y: 6, id: "A", color: "#4fc3f7" },
        { x: 6, y: 2, id: "B", color: "#ab47bc" },
      ],
      pathA: [{ x: 2, y: 6 }, { x: 3, y: 5 }, { x: 4, y: 4 }, { x: 5, y: 3 }],
      pathB: [{ x: 6, y: 2 }, { x: 5, y: 3 }, { x: 4, y: 4 }, { x: 3, y: 5 }],
      constraint: { x: 4, y: 4, t: 3, label: "forbid (4,4,t=3)" },
      caption: "Step 3 (Refine): Add hard planner constraint to block the unsafe space-time cell.",
    },
    {
      phase: "Step 4 - Replan",
      safe: true,
      agents: [
        { x: 2, y: 6, id: "A", color: "#4fc3f7" },
        { x: 6, y: 2, id: "B", color: "#ab47bc" },
      ],
      pathA: [{ x: 2, y: 6 }, { x: 3, y: 5 }, { x: 3, y: 4 }, { x: 4, y: 3 }, { x: 5, y: 3 }],
      pathB: [{ x: 6, y: 2 }, { x: 5, y: 3 }, { x: 5, y: 4 }, { x: 4, y: 5 }, { x: 3, y: 5 }],
      constraint: { x: 4, y: 4, t: 3, label: "forbid (4,4,t=3)" },
      caption: "Step 4 (Replan): Planner reroutes both agents to satisfy the injected constraint.",
    },
    {
      phase: "Step 5 - Re-Verify",
      safe: true,
      agents: [
        { x: 5, y: 3, id: "A", color: "#4fc3f7" },
        { x: 3, y: 5, id: "B", color: "#ab47bc" },
      ],
      pathA: [{ x: 2, y: 6 }, { x: 3, y: 5 }, { x: 3, y: 4 }, { x: 4, y: 3 }, { x: 5, y: 3 }],
      pathB: [{ x: 6, y: 2 }, { x: 5, y: 3 }, { x: 5, y: 4 }, { x: 4, y: 5 }, { x: 3, y: 5 }],
      constraint: { x: 4, y: 4, t: 3, label: "forbid (4,4,t=3)" },
      caption: "Step 5 (Re-Verify): No collisions under the new constraints. Status turns SAFE.",
    },
  ];

  function drawQuotientComparison() {
    const scenarioIndex = tick % quotientComparisonScenarios.length;
    const scenario = quotientComparisonScenarios[scenarioIndex];
    
    scenario.agents.forEach((agent) => {
      const p = toCell(agent.x, agent.y);
      
      // Draw agent circle
      ctx.fillStyle = "#4fc3f7";
      ctx.beginPath();
      ctx.arc(p.x + cell/2, p.y + cell/2, 15, 0, Math.PI * 2);
      ctx.fill();
      
      // Draw agent ID
      ctx.fillStyle = "#fff";
      ctx.font = "bold 12px monospace";
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(agent.id, p.x + cell/2, p.y + cell/2);
    });
    
    algoCaption.textContent = scenario.caption;
  }

  function drawVerification() {
    const scenarioIndex = tick % verificationScenarios.length;
    const scenario = verificationScenarios[scenarioIndex];
    
    // Draw obstacles
    scenario.obstacles.forEach((obs) => {
      const p = toCell(obs.x, obs.y);
      ctx.fillStyle = "#555";
      ctx.strokeStyle = "#888";
      ctx.lineWidth = 2;
      ctx.fillRect(p.x + 4, p.y + 4, cell - 8, cell - 8);
      ctx.strokeRect(p.x + 4, p.y + 4, cell - 8, cell - 8);
    });
    
    // Draw agents
    scenario.agents.forEach((agent) => {
      const p = toCell(agent.x, agent.y);
      
      // Draw agent circle
      ctx.fillStyle = agent.stopped ? "#ef5350" : "#4fc3f7";
      ctx.beginPath();
      ctx.arc(p.x + cell/2, p.y + cell/2, 15, 0, Math.PI * 2);
      ctx.fill();
      
      // Draw agent ID
      ctx.fillStyle = "#fff";
      ctx.font = "bold 12px monospace";
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(agent.id, p.x + cell/2, p.y + cell/2);
    });
    
    algoCaption.textContent = scenario.caption;
  }

  function drawRefinement() {
    const scenarioIndex = tick % refinementScenarios.length;
    const scenario = refinementScenarios[scenarioIndex];
    
    // Draw path cells
    scenario.path.forEach((p, i) => {
      const cellPos = toCell(p.x, p.y);
      
      if (scenario.unsafe && i === 2) {
        // Highlight unsafe cell at time step 2
        ctx.fillStyle = "rgba(239,83,80,0.7)";
        ctx.fillRect(cellPos.x + 2, cellPos.y + 2, cell - 4, cell - 4);
      } else if (!scenario.unsafe) {
        // Safe path - show in green
        ctx.fillStyle = "rgba(102,187,106,0.3)";
        ctx.fillRect(cellPos.x + 2, cellPos.y + 2, cell - 4, cell - 4);
      } else {
        // Unsafe path - show faded
        ctx.fillStyle = "rgba(79,195,247,0.2)";
        ctx.fillRect(cellPos.x + 2, cellPos.y + 2, cell - 4, cell - 4);
      }
      
      // Draw time label on top-right of cell
      ctx.fillStyle = "rgba(255,255,255,0.7)";
      ctx.font = "13px monospace";
      ctx.textAlign = "right";
      ctx.textBaseline = "top";
      ctx.fillText("t=" + i, cellPos.x + cell - 5, cellPos.y + 3);
    });
    
    // Draw current agent position
    const current = scenario.path[0];
    const pCurrent = toCell(current.x, current.y);
    
    ctx.fillStyle = scenario.unsafe ? "#ef5350" : "#66bb6a";
    ctx.beginPath();
    ctx.arc(pCurrent.x + cell/2, pCurrent.y + cell/2, 12, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = "#fff";
    ctx.lineWidth = 3;
    ctx.stroke();
    ctx.fillStyle = "#fff";
    ctx.font = "bold 12px monospace";
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText("A", pCurrent.x + cell/2, pCurrent.y + cell/2);
    
    // Draw constraint visualization if present
    if (scenario.constraint) {
      const pConstraint = toCell(scenario.constraint.x, scenario.constraint.y);
      
      // Draw constraint zone
      ctx.strokeStyle = "#ff9800";
      ctx.lineWidth = 3;
      ctx.setLineDash([4, 4]);
      ctx.strokeRect(pConstraint.x + 1, pConstraint.y + 1, cell - 2, cell - 2);
      ctx.setLineDash([]);
      
      // Draw constraint label above the constraint box
      ctx.fillStyle = "#ff9800";
      ctx.font = "bold 13px monospace";
      ctx.textAlign = "center";
      ctx.textBaseline = "bottom";
      const constraintText = "Constraint: (3,1,t=2)";
      ctx.fillText(constraintText, pConstraint.x + cell/2, pConstraint.y - 5);
    }
    
    // Draw status indicators at top
    ctx.fillStyle = scenario.unsafe ? "#ef5350" : "#66bb6a";
    ctx.font = "bold 16px monospace";
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    ctx.fillText(scenario.unsafe ? "Status: UNSAFE" : "Status: SAFE", canvasWidth / 2, 15);
    
    algoCaption.textContent = scenario.caption;
  }

  function renderAlgo() {
    const size = updateAlgoLayout();
    if (!size.width || !size.height) {
      return;
    }
    ctx.clearRect(0, 0, canvasWidth, canvasHeight);
    ctx.fillStyle = "#0f1318";
    ctx.fillRect(0, 0, canvasWidth, canvasHeight);
    
    if (algoMode !== "symmetry") {
      drawGrid();
    }
    
    if (algoMode === "astar") {
      drawAStar();
    } else if (algoMode === "prioritized") {
      drawPrioritized();
    } else if (algoMode === "reservation") {
      drawReservation();
    } else if (algoMode === "edge-swap") {
      drawEdgeSwap();
    } else if (algoMode === "assignment") {
      drawAssignment();
    } else if (algoMode === "symmetry") {
      drawSymmetry();
    } else if (algoMode === "quotient") {
      drawQuotientComparison();
    } else if (algoMode === "verification") {
      drawVerification();
    } else if (algoMode === "refinement") {
      drawRefinement();
    }
  }

  function algoTick(ts) {
    if (!lastAlgoTick) lastAlgoTick = ts;
    const elapsed = ts - lastAlgoTick;
    
    // Different timing for different algorithms
    const delay = algoMode === "astar" ? 1200 :
                  algoMode === "reservation" ? 2200 :
                  algoMode === "edge-swap" ? 2100 :
                  algoMode === "assignment" ? 2300 :
                  algoMode === "symmetry" ? 6000 : 
                  (algoMode === "prioritized" ? 3000 : 
                  (algoMode === "quotient" ? 3500 : 
                  (algoMode === "verification" ? 3000 : 
                  (algoMode === "refinement" ? 3500 : 500))));
    
    if (algoPlaying && elapsed > delay) {
      // Different tick limits for different algorithms
      let maxTick = 10;
      if (algoMode === "astar") maxTick = astarSearchStages.length;
      if (algoMode === "prioritized") maxTick = 16;
      if (algoMode === "reservation") maxTick = reservationStages.length;
      if (algoMode === "edge-swap") maxTick = edgeSwapStages.length;
      if (algoMode === "assignment") maxTick = assignmentStages.length;
      if (algoMode === "symmetry") maxTick = symmetryScenarios.length;
      if (algoMode === "quotient") maxTick = quotientComparisonScenarios.length;
      if (algoMode === "verification") maxTick = verificationScenarios.length;
      if (algoMode === "refinement") maxTick = refinementScenarios.length;
      
      tick = (tick + 1) % maxTick;
      lastAlgoTick = ts;
    }
    renderAlgo();
    requestAnimationFrame(algoTick);
  }

  algoButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      algoButtons.forEach((b) => b.classList.remove("is-active"));
      btn.classList.add("is-active");
      algoMode = btn.dataset.algo;
      tick = 0;
      lastAlgoTick = 0;
      
      // Update caption immediately on mode change
      if (algoCaption) {
        if (algoMode === "astar") {
          algoCaption.textContent = astarSearchStages[0].caption;
        } else if (algoMode === "prioritized") {
          algoCaption.textContent = "Cooperative planner phase 1: independent plans before reservation and constraint handling.";
        } else if (algoMode === "reservation") {
          algoCaption.textContent = reservationStages[0].caption;
        } else if (algoMode === "edge-swap") {
          algoCaption.textContent = edgeSwapStages[0].caption;
        } else if (algoMode === "assignment") {
          algoCaption.textContent = assignmentStages[0].caption;
        } else if (algoMode === "symmetry") {
          algoCaption.textContent = symmetryScenarios[0].caption;
        } else if (algoMode === "quotient") {
          algoCaption.textContent = quotientComparisonScenarios[0].caption;
        } else if (algoMode === "verification") {
          algoCaption.textContent = verificationScenarios[0].caption;
        } else if (algoMode === "refinement") {
          algoCaption.textContent = refinementScenarios[0].caption;
        }
      }
      renderAlgo(); // Immediately render new mode
    });
  });

  if (algoPauseButton) {
    algoPauseButton.addEventListener("click", () => {
      algoPlaying = !algoPlaying;
      if (algoPlaying) {
        lastAlgoTick = performance.now();
      }
      syncAlgoPauseButton();
    });
  }

  // Initialize with first render
  syncAlgoPauseButton();
  renderAlgo();
  requestAnimationFrame(algoTick);
}

// ==================== Symmetry Canvas Setup ====================
const symmetryCanvas = document.getElementById("symmetryCanvas");
const symmetryCaption = document.getElementById("symmetryCaption");
const symmetrySection = document.getElementById("symmetry");
const symmetryButtons = symmetrySection
  ? symmetrySection.querySelectorAll("[data-algo='symmetry'], [data-algo='quotient'], [data-algo='quotient-key']")
  : [];
const symmetryPauseButton = symmetrySection ? symmetrySection.querySelector("[data-control='symmetry-pause']") : null;
const symmetrySurface = symmetryCanvas ? createHiResCanvas(symmetryCanvas) : null;

console.log('symmetryCanvas:', symmetryCanvas, 'symmetryCaption:', symmetryCaption);

if (symmetryCanvas) {
  console.log('Initializing symmetryCanvas...');
  const sctx = symmetrySurface.ctx;
  const sgrid = 10;
  let scell = 32; // Will be adjusted based on canvas size
  let sWidth = 0;
  let sHeight = 0;
  let soffsetX = 0;
  let soffsetY = 0;
  let sMode = "symmetry";
  let sTickCount = 0;
  let sPlaying = true;
  let sLastTick = 0;

  function syncSymmetryPauseButton() {
    if (!symmetryPauseButton) return;
    symmetryPauseButton.textContent = sPlaying ? "Pause" : "Resume";
    symmetryPauseButton.classList.toggle("is-paused", !sPlaying);
    symmetryPauseButton.setAttribute("aria-pressed", String(!sPlaying));
  }

  function updateSymmetryLayout() {
    const size = symmetrySurface.resize();
    sWidth = size.width;
    sHeight = size.height;
    // Responsive cell size: scale grid to fit canvas
    scell = Math.min(sWidth / (sgrid + 2), sHeight / (sgrid + 2), 40);
    scell = Math.max(scell, 16); // Min cell size of 16px
    soffsetX = (sWidth - sgrid * scell) / 2;
    soffsetY = (sHeight - sgrid * scell) / 2;
    return size;
  }

  // Calculate agent radius based on cell size
  function getSAgentRadius(multiplier = 0.45) {
    return Math.max(7, Math.min(scell * multiplier, 15));
  }
  
  function sToCell(px, py) {
    return {
      x: soffsetX + px * scell,
      y: soffsetY + py * scell,
    };
  }
  
  function sDrawGrid() {
    sctx.strokeStyle = "rgba(255,255,255,0.08)";
    for (let i = 0; i <= sgrid; i++) {
      const x = soffsetX + i * scell;
      sctx.beginPath();
      sctx.moveTo(x, soffsetY);
      sctx.lineTo(x, soffsetY + sgrid * scell);
      sctx.stroke();
      const y = soffsetY + i * scell;
      sctx.beginPath();
      sctx.moveTo(soffsetX, y);
      sctx.lineTo(soffsetX + sgrid * scell, y);
      sctx.stroke();
    }
  }
  
  function sRenderSymmetry() {
    sctx.clearRect(0, 0, sWidth, sHeight);
    sctx.fillStyle = "#0f1318";
    sctx.fillRect(0, 0, sWidth, sHeight);
    
    const scenarioIndex = sTickCount % symmetryScenarios.length;
    const scenario = symmetryScenarios[scenarioIndex];
    
    // Draw agents
    scenario.agents.forEach((agent) => {
      const p = sToCell(agent.x, agent.y);
      
      let color = agent.role === 'carrying' ? '#f08c3a' : '#4fc3f7';
      
      if (agent.highlight) {
        sctx.fillStyle = 'rgba(102,187,106,0.3)';
        sctx.fillRect(p.x - 2, p.y - 2, scell + 4, scell + 4);
      }
      
      if (agent.orbitA) {
        sctx.strokeStyle = '#4fc3f7';
        sctx.lineWidth = 2;
        sctx.strokeRect(p.x - 2, p.y - 2, scell + 4, scell + 4);
      }
      
      if (agent.orbitB) {
        sctx.strokeStyle = '#f08c3a';
        sctx.lineWidth = 2;
        sctx.strokeRect(p.x - 2, p.y - 2, scell + 4, scell + 4);
      }
      
      sctx.fillStyle = color;
      sctx.beginPath();
      sctx.arc(p.x + scell/2, p.y + scell/2, agent.size === "large" ? getSAgentRadius(0.6) : getSAgentRadius(), 0, Math.PI * 2);
      sctx.fill();
      
      sctx.fillStyle = '#fff';
      sctx.font = "bold 13px monospace";
      sctx.textAlign = 'center';
      sctx.textBaseline = 'middle';
      sctx.fillText(agent.id, p.x + scell/2, p.y + scell/2);
    });
    
    if (scenario.text) {
      sctx.fillStyle = 'rgba(255,255,255,0.95)';
      sctx.font = "bold 13px monospace";
      sctx.textAlign = 'center';
      sctx.textBaseline = 'top';
      sctx.fillText(scenario.text, sWidth / 2, 20);
    }
    
    if (scenario.tuples) {
      sctx.fillStyle = scenario.sorted ? '#66bb6a' : 'rgba(255,255,255,0.85)';
      sctx.font = "14px monospace";
      sctx.textAlign = 'left';
      sctx.textBaseline = 'top';
      
      const startX = 80;
      const startY = 450;
      
      scenario.tuples.forEach((tuple, i) => {
        const y = startY + i * 38;
        sctx.fillText(tuple, startX, y);
      });
      
      if (scenario.sorted) {
        sctx.strokeStyle = '#66bb6a';
        sctx.lineWidth = 4;
        sctx.beginPath();
        sctx.moveTo(50, startY - 25);
        sctx.lineTo(50, startY - 5);
        sctx.stroke();
        
        sctx.beginPath();
        sctx.moveTo(50, startY - 5);
        sctx.lineTo(44, startY - 15);
        sctx.lineTo(56, startY - 15);
        sctx.closePath();
        sctx.fillStyle = '#66bb6a';
        sctx.fill();
        
        sctx.fillStyle = '#66bb6a';
        sctx.font = "bold 13px monospace";
        sctx.textAlign = 'center';
        sctx.textBaseline = 'bottom';
        sctx.fillText('SORTED', 50, startY - 32);
      }
    }
    
    if (scenario.stateCount) {
      sctx.fillStyle = 'rgba(255,255,255,0.95)';
      sctx.font = "bold 16px monospace";
      sctx.textAlign = 'center';
      sctx.textBaseline = 'middle';
      sctx.fillText(scenario.stateCount, sWidth / 2, 200);
      
      sctx.strokeStyle = '#66bb6a';
      sctx.lineWidth = 5;
      sctx.beginPath();
      sctx.moveTo(sWidth / 2, 230);
      sctx.lineTo(sWidth / 2, 280);
      sctx.stroke();
      
      sctx.beginPath();
      sctx.moveTo(sWidth / 2, 280);
      sctx.lineTo(sWidth / 2 - 12, 265);
      sctx.lineTo(sWidth / 2 + 12, 265);
      sctx.closePath();
      sctx.fillStyle = '#66bb6a';
      sctx.fill();
      
      sctx.fillStyle = '#66bb6a';
      sctx.font = "bold 16px monospace";
      sctx.fillText(scenario.quotientCount, sWidth / 2, 315);
    }
    
    if (symmetryCaption) {
      symmetryCaption.textContent = scenario.caption;
    }
  }
  
  function sRenderQuotient() {
    sctx.clearRect(0, 0, sWidth, sHeight);
    sctx.fillStyle = "#0f1318";
    sctx.fillRect(0, 0, sWidth, sHeight);
    
    sDrawGrid();
    
    const scenarioIndex = sTickCount % quotientComparisonScenarios.length;
    const scenario = quotientComparisonScenarios[scenarioIndex];
    
    scenario.agents.forEach((agent) => {
      const p = sToCell(agent.x, agent.y);
      
      sctx.fillStyle = "#4fc3f7";
      sctx.beginPath();
      sctx.arc(p.x + scell/2, p.y + scell/2, getSAgentRadius(), 0, Math.PI * 2);
      sctx.fill();
      
      sctx.fillStyle = "#fff";
      sctx.font = "bold 12px monospace";
      sctx.textAlign = 'center';
      sctx.textBaseline = 'middle';
      sctx.fillText(agent.id, p.x + scell/2, p.y + scell/2);
    });
    
    if (symmetryCaption) {
      symmetryCaption.textContent = scenario.caption;
    }
  }

  function sRenderQuotientKey() {
    sctx.clearRect(0, 0, sWidth, sHeight);
    sctx.fillStyle = "#0f1318";
    sctx.fillRect(0, 0, sWidth, sHeight);

    const scenario = quotientKeyScenarios[sTickCount % quotientKeyScenarios.length];
    const pad = 18;
    const colGap = 14;
    const boxW = Math.floor((sWidth - pad * 2 - colGap) / 2);
    const boxH = Math.min(170, Math.floor(sHeight * 0.45));
    const topY = 24;

    function drawBox(x, y, w, h, title, raw, key) {
      sctx.fillStyle = "rgba(12,18,27,0.9)";
      sctx.fillRect(x, y, w, h);
      sctx.strokeStyle = "rgba(255,255,255,0.16)";
      sctx.strokeRect(x, y, w, h);
      sctx.fillStyle = "rgba(255,255,255,0.95)";
      sctx.font = "bold 12px monospace";
      sctx.textAlign = "left";
      sctx.textBaseline = "top";
      sctx.fillText(title, x + 10, y + 8);

      sctx.fillStyle = "rgba(200,215,255,0.92)";
      sctx.font = "11px monospace";
      sctx.fillText("raw:", x + 10, y + 30);
      sctx.fillStyle = "rgba(255,255,255,0.82)";
      sctx.fillText(raw, x + 10, y + 46, w - 20);

      sctx.fillStyle = "rgba(255,222,130,0.96)";
      sctx.fillText("canonical key:", x + 10, y + 82);
      sctx.fillStyle = "rgba(255,255,255,0.90)";
      sctx.fillText(key, x + 10, y + 98, w - 20);
    }

    drawBox(pad, topY, boxW, boxH, scenario.leftLabel, scenario.rawA, scenario.keyA);
    drawBox(pad + boxW + colGap, topY, boxW, boxH, scenario.rightLabel, scenario.rawB, scenario.keyB);

    // Equality verdict strip
    const verdictY = topY + boxH + 16;
    const verdictW = Math.min(sWidth - 2 * pad, 620);
    const verdictX = (sWidth - verdictW) / 2;
    sctx.fillStyle = scenario.equal ? "rgba(102,187,106,0.2)" : "rgba(239,83,80,0.2)";
    sctx.fillRect(verdictX, verdictY, verdictW, 44);
    sctx.strokeStyle = scenario.equal ? "#66bb6a" : "#ef5350";
    sctx.lineWidth = 2;
    sctx.strokeRect(verdictX, verdictY, verdictW, 44);
    sctx.fillStyle = scenario.equal ? "#81c784" : "#ef9a9a";
    sctx.font = "bold 14px monospace";
    sctx.textAlign = "center";
    sctx.textBaseline = "middle";
    sctx.fillText(scenario.equal ? "quotient(A) == quotient(B)" : "quotient(C) != quotient(D)", sWidth / 2, verdictY + 22);

    sctx.fillStyle = "rgba(255,255,255,0.88)";
    sctx.font = "bold 13px monospace";
    sctx.textAlign = "center";
    sctx.textBaseline = "top";
    sctx.fillText(scenario.title, sWidth / 2, 6);

    if (symmetryCaption) {
      symmetryCaption.textContent = scenario.caption;
    }
  }
  
  function sRender() {
    const size = updateSymmetryLayout();
    if (!size.width || !size.height) {
      return;
    }
    if (sMode === "symmetry") {
      sRenderSymmetry();
    } else if (sMode === "quotient") {
      sRenderQuotient();
    } else if (sMode === "quotient-key") {
      sRenderQuotientKey();
    }
  }
  
  function sAnimationLoop(ts) {
    if (!sLastTick) sLastTick = ts;
    const elapsed = ts - sLastTick;
    
    const delay = sMode === "symmetry" ? 6000 : (sMode === "quotient-key" ? 4200 : 3500);
    
    if (sPlaying && elapsed > delay) {
      let maxTick = quotientComparisonScenarios.length;
      if (sMode === "symmetry") maxTick = symmetryScenarios.length;
      if (sMode === "quotient-key") maxTick = quotientKeyScenarios.length;
      sTickCount = (sTickCount + 1) % maxTick;
      sLastTick = ts;
    }
    sRender();
    requestAnimationFrame(sAnimationLoop);
  }
  
  // Handle button clicks
  symmetryButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      sMode = btn.dataset.algo;
      sTickCount = 0;
      sLastTick = 0;
      sRender();
    });
  });

  if (symmetryPauseButton) {
    symmetryPauseButton.addEventListener("click", () => {
      sPlaying = !sPlaying;
      if (sPlaying) {
        sLastTick = performance.now();
      }
      syncSymmetryPauseButton();
    });
  }
  
  syncSymmetryPauseButton();
  sRender();
  requestAnimationFrame(sAnimationLoop);
}

// ==================== Verification Canvas Setup ====================
const verifyCanvas = document.getElementById("verifyCanvas");
const verifyCaption = document.getElementById("verifyCaption");
const verifySection = document.getElementById("verification");
const verifyButtons = verifySection
  ? verifySection.querySelectorAll("[data-algo='verification'], [data-algo='verify-refine-loop']")
  : [];
const verifyPauseButton = verifySection ? verifySection.querySelector("[data-control='verify-pause']") : null;
const verifySurface = verifyCanvas ? createHiResCanvas(verifyCanvas) : null;

console.log('verifyCanvas:', verifyCanvas, 'verifyCaption:', verifyCaption);

if (verifyCanvas) {
  console.log('Initializing verifyCanvas...');
  const vctx = verifySurface.ctx;
  const vgrid = 10;
  let vcell = 32;
  let vWidth = 0;
  let vHeight = 0;
  let voffsetX = 0;
  let voffsetY = 0;
  let vHeaderY = 0;
  let vFooterY = 0;
  let vHeaderHeight = 0;
  let vFooterHeight = 0;
  let vPadding = 0;
  let vLegendX = 0;
  let vLegendY = 0;
  let vLegendWidth = 0;
  let vMode = "verification";
  let vTickCount = 0;
  let vLastTick = 0;
  let vPlaying = true;
  let vTime = 0;
  let vScenarioStart = 0;
  let vPausedScenarioElapsed = 0;

  function syncVerifyPauseButton() {
    if (!verifyPauseButton) return;
    verifyPauseButton.textContent = vPlaying ? "Pause" : "Resume";
    verifyPauseButton.classList.toggle("is-paused", !vPlaying);
    verifyPauseButton.setAttribute("aria-pressed", String(!vPlaying));
  }

  function updateVerifyLayout() {
    const size = verifySurface.resize();
    vWidth = size.width;
    vHeight = size.height;
    vPadding = 0;
    vHeaderHeight = 0;
    vFooterHeight = 0;
    vLegendWidth = 0;

    const maxCell = 32;
    vcell = Math.max(18, Math.min(maxCell, Math.floor(Math.min(vWidth, vHeight) / vgrid)));
    const gridWidth = vcell * vgrid;
    const gridHeight = vcell * vgrid;

    voffsetX = Math.max(0, (vWidth - gridWidth) / 2);
    voffsetY = Math.max(0, (vHeight - gridHeight) / 2);

    vHeaderY = 0;
    vFooterY = vHeight;
    vLegendX = 0;
    vLegendY = 0;
    return size;
  }

  // Calculate agent radius based on cell size
  function getVAgentRadius(multiplier = 0.45) {
    return Math.max(7, Math.min(vcell * multiplier, 15));
  }
  
  function vToCell(px, py) {
    return {
      x: voffsetX + px * vcell,
      y: voffsetY + py * vcell,
    };
  }
  
  function vDrawGrid() {
    vctx.strokeStyle = "rgba(255,255,255,0.08)";
    for (let i = 0; i <= vgrid; i++) {
      const x = voffsetX + i * vcell;
      vctx.beginPath();
      vctx.moveTo(x, voffsetY);
      vctx.lineTo(x, voffsetY + vgrid * vcell);
      vctx.stroke();
      const y = voffsetY + i * vcell;
      vctx.beginPath();
      vctx.moveTo(voffsetX, y);
      vctx.lineTo(voffsetX + vgrid * vcell, y);
      vctx.stroke();
    }
  }

  function vRoundRect(x, y, w, h, r) {
    if (typeof vctx.roundRect === "function") {
      vctx.beginPath();
      vctx.roundRect(x, y, w, h, r);
      return;
    }
    const radius = Math.min(r, w / 2, h / 2);
    vctx.beginPath();
    vctx.moveTo(x + radius, y);
    vctx.lineTo(x + w - radius, y);
    vctx.quadraticCurveTo(x + w, y, x + w, y + radius);
    vctx.lineTo(x + w, y + h - radius);
    vctx.quadraticCurveTo(x + w, y + h, x + w - radius, y + h);
    vctx.lineTo(x + radius, y + h);
    vctx.quadraticCurveTo(x, y + h, x, y + h - radius);
    vctx.lineTo(x, y + radius);
    vctx.quadraticCurveTo(x, y, x + radius, y);
  }
  
  function vRenderVerification() {
    vctx.clearRect(0, 0, vWidth, vHeight);
    vctx.fillStyle = "#0f1318";
    vctx.fillRect(0, 0, vWidth, vHeight);

    vDrawGrid();
    
    const scenarioIndex = vTickCount % verificationScenarios.length;
    const scenario = verificationScenarios[scenarioIndex];
    
    scenario.obstacles.forEach((obs) => {
      const p = vToCell(obs.x, obs.y);
      vctx.fillStyle = "#555";
      vctx.strokeStyle = "#888";
      vctx.lineWidth = 2;
      vctx.fillRect(p.x + 4, p.y + 4, vcell - 8, vcell - 8);
      vctx.strokeRect(p.x + 4, p.y + 4, vcell - 8, vcell - 8);
    });
    
    scenario.agents.forEach((agent) => {
      const p = vToCell(agent.x, agent.y);
      
      vctx.fillStyle = agent.stopped ? "#ef5350" : "#4fc3f7";
      vctx.beginPath();
      vctx.arc(p.x + vcell/2, p.y + vcell/2, getVAgentRadius(), 0, Math.PI * 2);
      vctx.fill();
      
      vctx.fillStyle = "#fff";
      vctx.font = "bold 12px monospace";
      vctx.textAlign = 'center';
      vctx.textBaseline = 'middle';
      vctx.fillText(agent.id, p.x + vcell/2, p.y + vcell/2);
    });
    
    if (verifyCaption) {
      verifyCaption.textContent = scenario.caption;
    }
  }
  
  function vRenderRefinement() {
    vctx.clearRect(0, 0, vWidth, vHeight);
    vctx.fillStyle = "#0f1318";
    vctx.fillRect(0, 0, vWidth, vHeight);

    vDrawGrid();
    
    const scenarioIndex = vTickCount % refinementScenarios.length;
    const scenario = refinementScenarios[scenarioIndex];

    const stepDelay = 450;
    const stepIndex = Math.min(
      Math.floor((vTime - vScenarioStart) / stepDelay),
      scenario.path.length - 1
    );

    // Draw path line
    vctx.strokeStyle = scenario.unsafe ? "rgba(239,83,80,0.6)" : "rgba(102,187,106,0.55)";
    vctx.lineWidth = Math.max(2, vcell * 0.12);
    vctx.lineCap = "round";
    vctx.lineJoin = "round";
    vctx.beginPath();
    scenario.path.forEach((p, i) => {
      const cellPos = vToCell(p.x, p.y);
      const cx = cellPos.x + vcell / 2;
      const cy = cellPos.y + vcell / 2;
      if (i === 0) {
        vctx.moveTo(cx, cy);
      } else {
        vctx.lineTo(cx, cy);
      }
    });
    vctx.stroke();

    // Draw step markers
    scenario.path.forEach((p, i) => {
      const cellPos = vToCell(p.x, p.y);
      const cx = cellPos.x + vcell / 2;
      const cy = cellPos.y + vcell / 2;
      const isActive = i === stepIndex;
      vctx.fillStyle = isActive ? "#ffffff" : "rgba(255,255,255,0.4)";
      vctx.beginPath();
      vctx.arc(cx, cy, isActive ? Math.max(6, vcell * 0.2) : Math.max(3, vcell * 0.12), 0, Math.PI * 2);
      vctx.fill();

    });

    const current = scenario.path[Math.max(0, stepIndex)];
    const pCurrent = vToCell(current.x, current.y);

    vctx.fillStyle = scenario.unsafe ? "#ef5350" : "#66bb6a";
    vctx.beginPath();
    vctx.arc(pCurrent.x + vcell / 2, pCurrent.y + vcell / 2, Math.max(10, vcell * 0.3), 0, Math.PI * 2);
    vctx.fill();
    vctx.strokeStyle = "rgba(255,255,255,0.9)";
    vctx.lineWidth = 2.5;
    vctx.stroke();
    vctx.fillStyle = "#0f1318";
    vctx.font = "700 12px 'Space Grotesk', sans-serif";
    vctx.textAlign = "center";
    vctx.textBaseline = "middle";
    vctx.fillText("A", pCurrent.x + vcell / 2, pCurrent.y + vcell / 2);
    
    if (scenario.constraint) {
      const pConstraint = vToCell(scenario.constraint.x, scenario.constraint.y);

      vctx.fillStyle = "rgba(255,152,0,0.12)";
      vctx.fillRect(pConstraint.x + 2, pConstraint.y + 2, vcell - 4, vcell - 4);
      vctx.strokeStyle = "#ffb74d";
      vctx.lineWidth = 2.5;
      vctx.setLineDash([6, 4]);
      vctx.strokeRect(pConstraint.x + 2, pConstraint.y + 2, vcell - 4, vcell - 4);
      vctx.setLineDash([]);

    }
    
    if (verifyCaption) {
      verifyCaption.textContent = scenario.caption;
    }
  }

  function vRenderVerifyRefineLoop() {
    vctx.clearRect(0, 0, vWidth, vHeight);
    vctx.fillStyle = "#0f1318";
    vctx.fillRect(0, 0, vWidth, vHeight);

    vDrawGrid();

    const scenarioIndex = vTickCount % verifyRefineLoopScenarios.length;
    const scenario = verifyRefineLoopScenarios[scenarioIndex];

    function drawPath(path, color) {
      if (!path || path.length < 2) return;
      vctx.strokeStyle = color;
      vctx.lineWidth = Math.max(2, vcell * 0.11);
      vctx.lineCap = "round";
      vctx.lineJoin = "round";
      vctx.beginPath();
      path.forEach((pt, i) => {
        const p = vToCell(pt.x, pt.y);
        const cx = p.x + vcell / 2;
        const cy = p.y + vcell / 2;
        if (i === 0) vctx.moveTo(cx, cy);
        else vctx.lineTo(cx, cy);
      });
      vctx.stroke();
    }

    drawPath(scenario.pathA, "rgba(79,195,247,0.72)");
    drawPath(scenario.pathB, "rgba(171,71,188,0.72)");

    if (scenario.constraint) {
      const cp = vToCell(scenario.constraint.x, scenario.constraint.y);
      vctx.fillStyle = "rgba(255,152,0,0.14)";
      vctx.fillRect(cp.x + 2, cp.y + 2, vcell - 4, vcell - 4);
      vctx.strokeStyle = "#ffb74d";
      vctx.lineWidth = 2.4;
      vctx.setLineDash([6, 4]);
      vctx.strokeRect(cp.x + 2, cp.y + 2, vcell - 4, vcell - 4);
      vctx.setLineDash([]);
      vctx.fillStyle = "#ffcc80";
      vctx.font = "bold 11px monospace";
      vctx.textAlign = "center";
      vctx.textBaseline = "bottom";
      vctx.fillText(scenario.constraint.label, cp.x + vcell / 2, cp.y - 3);
    }

    if (scenario.conflict) {
      const kp = vToCell(scenario.conflict.x, scenario.conflict.y);
      vctx.strokeStyle = "#ef5350";
      vctx.lineWidth = 3;
      vctx.beginPath();
      vctx.moveTo(kp.x + 6, kp.y + 6);
      vctx.lineTo(kp.x + vcell - 6, kp.y + vcell - 6);
      vctx.stroke();
      vctx.beginPath();
      vctx.moveTo(kp.x + vcell - 6, kp.y + 6);
      vctx.lineTo(kp.x + 6, kp.y + vcell - 6);
      vctx.stroke();
      if (scenario.conflict.label) {
        vctx.fillStyle = "#ff8a80";
        vctx.font = "bold 11px monospace";
        vctx.textAlign = "center";
        vctx.textBaseline = "bottom";
        vctx.fillText(scenario.conflict.label, kp.x + vcell / 2, kp.y - 3);
      }
    }

    scenario.agents.forEach((agent) => {
      const p = vToCell(agent.x, agent.y);
      vctx.fillStyle = agent.color;
      vctx.beginPath();
      vctx.arc(p.x + vcell / 2, p.y + vcell / 2, getVAgentRadius(), 0, Math.PI * 2);
      vctx.fill();
      vctx.fillStyle = "#fff";
      vctx.font = "bold 12px monospace";
      vctx.textAlign = "center";
      vctx.textBaseline = "middle";
      vctx.fillText(agent.id, p.x + vcell / 2, p.y + vcell / 2);
    });

    const pillText = scenario.safe ? "SAFE" : "UNSAFE";
    const fullLabel = `${scenario.phase} | ${pillText}`;
    const pillX = voffsetX + 8;
    const pillY = voffsetY + 8;
    const pillH = 30;
    const maxPillW = Math.max(130, vcell * vgrid - 16);
    const padX = 12;

    vctx.font = "bold 12px monospace";
    let label = fullLabel;
    let labelW = vctx.measureText(label).width;
    const maxLabelW = Math.max(48, maxPillW - (padX * 2));
    while (labelW > maxLabelW && label.length > 6) {
      label = label.slice(0, -2).trimEnd() + "…";
      labelW = vctx.measureText(label).width;
    }

    const pillW = Math.min(maxPillW, Math.max(120, Math.ceil(labelW + padX * 2)));
    vctx.fillStyle = scenario.safe ? "rgba(102,187,106,0.2)" : "rgba(239,83,80,0.2)";
    vRoundRect(pillX, pillY, pillW, pillH, 8);
    vctx.fill();
    vctx.strokeStyle = scenario.safe ? "#66bb6a" : "#ef5350";
    vctx.lineWidth = 1.8;
    vctx.stroke();
    vctx.fillStyle = scenario.safe ? "#81c784" : "#ef9a9a";
    vctx.textAlign = "left";
    vctx.textBaseline = "middle";
    vctx.fillText(label, pillX + padX, pillY + pillH / 2 + 0.5);

    if (verifyCaption) {
      verifyCaption.textContent = scenario.caption;
    }
  }
  
  function vRender() {
    const size = updateVerifyLayout();
    if (!size.width || !size.height) {
      return;
    }
    if (vMode === "verification") {
      vRenderVerification();
    } else if (vMode === "refinement") {
      vRenderRefinement();
    } else if (vMode === "verify-refine-loop") {
      vRenderVerifyRefineLoop();
    }
  }
  
  function vAnimationLoop(ts) {
    if (!vLastTick) {
      vLastTick = ts;
      if (!vScenarioStart) {
        vScenarioStart = ts;
      }
      if (!vTime) {
        vTime = ts;
      }
    }
    if (vPlaying) {
      vTime = ts;
    }
    const elapsed = ts - vLastTick;
    
    const delay = vMode === "verify-refine-loop" ? 3200 : 3000;
    
    if (vPlaying && elapsed > delay) {
      let maxTick = refinementScenarios.length;
      if (vMode === "verification") maxTick = verificationScenarios.length;
      if (vMode === "verify-refine-loop") maxTick = verifyRefineLoopScenarios.length;
      vTickCount = (vTickCount + 1) % maxTick;
      vLastTick = ts;
      vScenarioStart = ts;
      vPausedScenarioElapsed = 0;
    }
    vRender();
    requestAnimationFrame(vAnimationLoop);
  }
  
  // Handle button clicks
  verifyButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      vMode = btn.dataset.algo;
      vTickCount = 0;
      const now = performance.now();
      vLastTick = now;
      vScenarioStart = now;
      vPausedScenarioElapsed = 0;
      vTime = now;
      vRender();
    });
  });

  if (verifyPauseButton) {
    verifyPauseButton.addEventListener("click", () => {
      vPlaying = !vPlaying;
      if (vPlaying) {
        const now = performance.now();
        vLastTick = now;
        vScenarioStart = now - vPausedScenarioElapsed;
        vTime = now;
      } else {
        vPausedScenarioElapsed = Math.max(0, vTime - vScenarioStart);
      }
      syncVerifyPauseButton();
    });
  }
  
  syncVerifyPauseButton();
  vRender();
  requestAnimationFrame(vAnimationLoop);
}
