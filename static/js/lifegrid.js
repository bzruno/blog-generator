function initLifeGrid(config) {
  const canvas = document.getElementById("lifeGrid");
  if (!canvas) return;
  
  const ctx = canvas.getContext("2d");
  const { totalWeeks, livedWeeks, weeksPerRow, rows, marcosEspeciais } = config;
  const baseSquareSize = 10;
  const baseGap = 2;
  let opacity = 1.0;
  let fadingIn = true;

  function resizeCanvas() {
    const container = canvas.parentElement;
    const containerWidth = container.clientWidth;
    const maxCanvasWidth = Math.min(containerWidth * 0.95, weeksPerRow * (baseSquareSize + baseGap) - baseGap);
    const scale = maxCanvasWidth / (weeksPerRow * (baseSquareSize + baseGap) - baseGap);
    const squareSize = Math.max(baseSquareSize * scale, 3);
    const gap = Math.max(baseGap * scale, 1);
    canvas.width = weeksPerRow * (squareSize + gap) - gap;
    canvas.height = rows * (squareSize + gap) - gap;
    return { squareSize, gap };
  }

  function isMarcoEspecial(week) {
    return marcosEspeciais.find(marco => marco.semana === week);
  }

  function drawGrid() {
    const { squareSize, gap } = resizeCanvas();
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (let week = 0; week < totalWeeks; week++) {
      const row = Math.floor(week / weeksPerRow);
      const col = week % weeksPerRow;
      const x = col * (squareSize + gap);
      const y = row * (squareSize + gap);
      const marco = isMarcoEspecial(week);
      if (marco) {
        ctx.fillStyle = marco.cor;
        ctx.fillRect(x, y, squareSize, squareSize);
      } else if (week < livedWeeks - 1) {
        ctx.fillStyle = "#6c7086";
        ctx.fillRect(x, y, squareSize, squareSize);
      } else if (week === livedWeeks - 1 && livedWeeks > 0) {
        ctx.fillStyle = `rgb(108, 112, 134, ${opacity})`;
        ctx.fillRect(x, y, squareSize, squareSize);
      } else {
        ctx.fillStyle = "#313244";
        ctx.fillRect(x, y, squareSize, squareSize);
      }
    }
  }

  function animate() {
    if (fadingIn) {
      opacity += 0.003;
      if (opacity >= 1.0) fadingIn = false;
    } else {
      opacity -= 0.012;
      if (opacity <= 0.3) fadingIn = true;
    }
    drawGrid();
    requestAnimationFrame(animate);
  }

  window.addEventListener("resize", drawGrid);
  drawGrid();
  animate();
}