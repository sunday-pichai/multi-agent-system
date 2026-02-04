// Dark mode toggle functionality
const darkModeToggle = document.getElementById("darkModeToggle");
if (darkModeToggle) {
  // Check for saved dark mode preference or default to light mode
  const savedDarkMode = localStorage.getItem("darkMode") === "true";
  if (savedDarkMode) {
    document.body.classList.add("dark-mode");
  }

  darkModeToggle.addEventListener("click", () => {
    document.body.classList.toggle("dark-mode");
    const isDarkMode = document.body.classList.contains("dark-mode");
    localStorage.setItem("darkMode", isDarkMode);
  });

  // Show toggle only when scrolled down
  window.addEventListener("scroll", () => {
    if (window.scrollY > 300) {
      darkModeToggle.classList.add("visible");
    } else {
      darkModeToggle.classList.remove("visible");
    }
  });
}

const steps = {
  plan: {
    title: "Plan (Cooperative A* + CBS)",
    text:
      "Each agent plans a time-expanded path using Cooperative A*. CBS resolves conflicts by adding constraints and replanning until paths are consistent.",
    code: `Cooperative A*:
- time-expanded grid
- reservation table

CBS:
- detect conflicts
- add constraint
- replan for agent`,
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

const flowButtons = document.querySelectorAll("[data-flow]");
const flowChart = document.getElementById("flowChart");
const flowChartCaption = document.getElementById("flowChartCaption");

function drawFlowChart(active) {
  if (!flowChart) return;
  const ctx = flowChart.getContext("2d");
  ctx.clearRect(0, 0, flowChart.width, flowChart.height);
  const bg = ctx.createLinearGradient(0, 0, flowChart.width, flowChart.height);
  bg.addColorStop(0, "#0f1318");
  bg.addColorStop(1, "#18202a");
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, flowChart.width, flowChart.height);

  const nodes = [
    { key: "plan", label: "Plan", x: 60, y: 70 },
    { key: "symmetry", label: "Symmetry", x: 300, y: 70 },
    { key: "verify", label: "Verify", x: 300, y: 190 },
    { key: "refine", label: "Refine", x: 60, y: 190 },
  ];

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
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(fromX, fromY);
    ctx.lineTo(toX, toY);
    ctx.stroke();
    const angle = Math.atan2(toY - fromY, toX - fromX);
    const head = 8;
    ctx.beginPath();
    ctx.moveTo(toX, toY);
    ctx.lineTo(toX - head * Math.cos(angle - Math.PI / 6), toY - head * Math.sin(angle - Math.PI / 6));
    ctx.lineTo(toX - head * Math.cos(angle + Math.PI / 6), toY - head * Math.sin(angle + Math.PI / 6));
    ctx.closePath();
    ctx.fillStyle = "rgba(255,255,255,0.35)";
    ctx.fill();
  }

  arrow(200, 95, 300, 95);
  arrow(370, 120, 370, 190);
  arrow(300, 215, 200, 215);
  arrow(130, 190, 130, 120);

  nodes.forEach((n) => {
    const isActive = n.key === active;
    const w = 160;
    const h = 56;
    ctx.save();
    ctx.shadowColor = isActive ? "rgba(255, 214, 102, 0.5)" : "rgba(0,0,0,0.35)";
    ctx.shadowBlur = isActive ? 18 : 12;
    ctx.shadowOffsetY = 6;
    ctx.fillStyle = isActive ? "#c85d3d" : "#1f2a33";
    ctx.strokeStyle = isActive ? "#ffd166" : "#2d3a45";
    ctx.lineWidth = 2;
    roundedRect(n.x, n.y, w, h, 12);
    ctx.fill();
    ctx.stroke();
    ctx.restore();

    ctx.fillStyle = "#f2f2f2";
    ctx.font = "600 16px 'Space Grotesk', sans-serif";
    ctx.fillText(n.label, n.x + 20, n.y + 32);
  });
}

function updateFlow(active) {
  flowButtons.forEach((b) => b.classList.toggle("is-active", b.dataset.flow === active));
  const captions = {
    plan: "Plan: Cooperative A* + CBS generates conflict-free paths.",
    symmetry: "Symmetry: role-orbit reduction and canonicalization.",
    verify: "Verify: bounded safety checks on the quotient model.",
    refine: "Refine: constraints injected from counterexamples.",
  };
  flowChartCaption.textContent = captions[active] || "";
  drawFlowChart(active);
}

flowButtons.forEach((btn) => {
  btn.addEventListener("click", () => updateFlow(btn.dataset.flow));
});

updateFlow("plan");

// Canvas interactive explainer - minimal design
const canvas = document.getElementById("flowCanvas");
const caption = document.getElementById("canvasCaption");
const modeButtons = document.querySelectorAll(".chip");

if (canvas) {
  const ctx = canvas.getContext("2d");
  const W = canvas.width;
  const H = canvas.height;

  // Simplified grid - 6x4
  const gridSize = 6;
  const cellSize = 50;
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
    ctx.arc(p.x, p.y, 14, 0, Math.PI * 2);
    ctx.fill();
    
    ctx.fillStyle = "#fff";
    ctx.font = "bold 12px Arial";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(label, p.x, p.y);
  }

  function drawGoal(x, y, label) {
    const p = toPx(x, y);
    ctx.strokeStyle = "#ffd166";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(p.x, p.y, 10, 0, Math.PI * 2);
    ctx.stroke();
    
    ctx.fillStyle = "#ffd166";
    ctx.font = "10px Arial";
    ctx.textAlign = "center";
    ctx.fillText(label, p.x, p.y - 20);
  }

  function drawConflictZone() {
    const p = toPx(2.5, 1.5);
    ctx.strokeStyle = "#ef5350";
    ctx.fillStyle = "rgba(239, 83, 80, 0.15)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(p.x, p.y, 35, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
  }

  function drawObstacle() {
    const p1 = toPx(2, 1);
    const p2 = toPx(3, 2);
    ctx.fillStyle = "#555";
    ctx.strokeStyle = "#888";
    ctx.lineWidth = 2;
    ctx.fillRect(p1.x - 15, p1.y - 15, 30, 30);
    ctx.fillRect(p2.x - 15, p2.y - 15, 30, 30);
    ctx.strokeRect(p1.x - 15, p1.y - 15, 30, 30);
    ctx.strokeRect(p2.x - 15, p2.y - 15, 30, 30);
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
      let maxLength;
      if (mode === "refine") {
        maxLength = agent1PathRefined.length;
      } else if (mode === "verify") {
        maxLength = agent1PathVerify.length;
      } else {
        maxLength = agent1PathOriginal.length;
      }
      stepIndex = (stepIndex + 1) % maxLength;
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

// Algorithm demo canvas
const algoCanvas = document.getElementById("algoCanvas");
const algoCaption = document.getElementById("algoCaption");
const algoButtons = document.querySelectorAll("[data-algo]");

if (algoCanvas) {
  const ctx = algoCanvas.getContext("2d");
  const grid = 10;
  const cell = 28;
  const offsetX = 40;
  const offsetY = 20;
  let algoMode = "astar";
  let tick = 0;
  let algoPlaying = true;
  let lastAlgoTick = 0;

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

  const cbsAgentA = [
    { x: 1, y: 4 }, { x: 2, y: 4 }, { x: 3, y: 4 }, { x: 4, y: 4 },
  ];
  const cbsAgentB = [
    { x: 4, y: 4 }, { x: 3, y: 4 }, { x: 2, y: 4 }, { x: 1, y: 4 },
  ];
  const cbsReplanA = [
    { x: 1, y: 3 }, { x: 2, y: 3 }, { x: 3, y: 3 }, { x: 4, y: 3 },
  ];
  const cbsReplanB = [
    { x: 4, y: 5 }, { x: 3, y: 5 }, { x: 2, y: 5 }, { x: 1, y: 5 },
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
    astarWalls.forEach((w) => drawCell(w, "#26323c"));
    drawCell(astarStart, "#66bb6a");
    drawCell(astarGoal, "#ffd166");

    const frontierCount = Math.min(tick + 2, astarPath.length);
    for (let i = 0; i < frontierCount; i++) {
      drawCell(astarPath[i], "rgba(79,195,247,0.8)");
    }
    if (frontierCount >= astarPath.length) {
      astarPath.forEach((p) => drawCell(p, "rgba(255,200,100,0.7)"));
    }
    algoCaption.textContent = "A*: frontier expansion (blue) and final path (amber).";
  }

  function drawCBS() {
    const t = Math.min(tick, cbsAgentA.length - 1);
    const conflictPos = cbsAgentA[2];
    drawCell(conflictPos, "rgba(239,83,80,0.6)");

    const a = cbsAgentA[t];
    const b = cbsAgentB[t];
    drawCell(a, "#f08c3a");
    drawCell(b, "#4fc3f7");

    if (tick > 3) {
      const rt = Math.min(tick - 4, cbsReplanA.length - 1);
      drawCell(cbsReplanA[rt], "#f08c3a");
      drawCell(cbsReplanB[rt], "#4fc3f7");
      algoCaption.textContent = "CBS: detect conflict (red), add constraint, replan around it.";
    } else {
      algoCaption.textContent = "CBS: agents approach the same cell (conflict).";
    }
  }

  function renderAlgo() {
    ctx.clearRect(0, 0, algoCanvas.width, algoCanvas.height);
    ctx.fillStyle = "#0f1318";
    ctx.fillRect(0, 0, algoCanvas.width, algoCanvas.height);
    drawGrid();
    if (algoMode === "astar") {
      drawAStar();
    } else {
      drawCBS();
    }
  }

  function algoTick(ts) {
    if (!lastAlgoTick) lastAlgoTick = ts;
    const elapsed = ts - lastAlgoTick;
    if (algoPlaying && elapsed > 500) {
      tick = (tick + 1) % 10;
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
    });
  });

  requestAnimationFrame(algoTick);
}
