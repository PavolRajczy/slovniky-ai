import * as d3 from 'd3';
import { GraphNode, GraphEdge } from './ontologyGraphLayout';
import { ChangeType } from '@/store/ontologyChangesStore';
import { NodePosition } from '@/store/nodePositionsStore';

/** D3 runtime node used by the force simulation (canvas rendering). */
interface D3Node extends d3.SimulationNodeDatum {
  id: string;
  label: string;
  color: string;
  radius: number;
  pinned?: boolean;
  fx?: number | null;
  fy?: number | null;
  changeType?: ChangeType | null;
}

/** D3 runtime link with multi-edge metadata + relationship kind. */
interface D3Link extends d3.SimulationLinkDatum<D3Node> {
  source: string | D3Node;
  target: string | D3Node;
  label?: string;
  // Multi-edge metadata (computed in loadData)
  _parallelIndex?: number; // 0..n-1
  _parallelTotal?: number; // n
  // Relationship kind
  _kind: 'inheritance' | 'association';
  changeType?: ChangeType | null;
}

/** Central style palette for relationships */
const REL_STYLE = {
  association: {
    stroke: '#3b82f6', // blue (matching our theme)
    text: '#1e40af',
    arrowFill: '#3b82f6',
    dash: [] as number[],
  },
  inheritance: {
    stroke: '#94a3b8', // gray (matching our theme)
    text: '#64748b',
    arrowFill: '#94a3b8',
    dash: [6, 3] as number[], // dashed to distinguish
  },
};

export class OntologyCanvas {
  private canvas: HTMLCanvasElement;
  private context: CanvasRenderingContext2D;
  private width: number;
  private height: number;
  private nodes: D3Node[] = [];
  private links: D3Link[] = [];
  private simulation: d3.Simulation<D3Node, D3Link>;
  private transform: d3.ZoomTransform = d3.zoomIdentity;
  private onNodeClick?: (nodeId: string) => void;
  private hoveredNode: D3Node | null = null;
  private onNodePin?: (nodeId: string, x: number, y: number) => void;
  private onNodeUnpin?: (nodeId: string) => void;

  // Drag state
  private dragBehavior: d3.DragBehavior<HTMLCanvasElement, unknown, D3Node | null>;

  constructor(
    container: HTMLElement, 
    width: number, 
    height: number, 
    onNodeClick?: (nodeId: string) => void,
    onNodePin?: (nodeId: string, x: number, y: number) => void,
    onNodeUnpin?: (nodeId: string) => void
  ) {
    this.width = width;
    this.height = height;
    this.onNodeClick = onNodeClick;
    this.onNodePin = onNodePin;
    this.onNodeUnpin = onNodeUnpin;

    this.canvas = document.createElement('canvas');
    this.canvas.width = width;
    this.canvas.height = height;
    this.canvas.style.width = `${width}px`;
    this.canvas.style.height = `${height}px`;
    this.canvas.style.touchAction = 'none';
    this.canvas.style.cursor = 'grab';
    container.appendChild(this.canvas);

    const ctx = this.canvas.getContext('2d');
    if (!ctx) throw new Error('Canvas context not available');
    this.context = ctx;

    // Force simulation setup
    this.simulation = d3
      .forceSimulation<D3Node>()
      .force('link', d3.forceLink<D3Node, D3Link>().id(d => d.id).distance(150).strength(0.7))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('collide', d3.forceCollide<D3Node>().radius(d => d.radius + 10).iterations(2))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .on('tick', () => this.render());

    this.initZoom();
    this.dragBehavior = this.initDrag();
    this.initDoubleClickPin();
    this.initClickHandler();
    this.initHoverTracking();
  }

  /** Load/replace data from your GraphNode/GraphEdge arrays */
  loadData(nodes: GraphNode[], edges: GraphEdge[], pinnedPositions?: Map<string, NodePosition>) {
    // Map to D3 runtime nodes/links
    this.nodes = nodes.map(n => {
      const pinnedPos = pinnedPositions?.get(n.id);
      
      return {
        id: n.id,
        label: n.data.label,
        color: '#4682b4',
        radius: 35, // Larger radius to fit more text
        // Use pinned position if available, otherwise use provided position or random
        x: pinnedPos?.x ?? (n.position?.x ?? (this.width / 2 + (Math.random() - 0.5) * 80)),
        y: pinnedPos?.y ?? (n.position?.y ?? (this.height / 2 + (Math.random() - 0.5) * 80)),
        changeType: n.data.changeType,
        // Restore pinned state
        pinned: pinnedPos !== undefined,
        fx: pinnedPos?.x ?? null,
        fy: pinnedPos?.y ?? null,
      };
    });

    // Create a set of valid node IDs for filtering edges
    const validNodeIds = new Set(this.nodes.map(n => n.id));

    console.log('🔍 Node IDs available:', Array.from(validNodeIds).slice(0, 5));
    console.log('🔍 Sample edge source/target:', edges.slice(0, 3).map(e => ({ source: e.source, target: e.target })));

    // Filter out edges that reference non-existent nodes
    const validEdges = edges.filter(e => {
      const sourceExists = validNodeIds.has(e.source);
      const targetExists = validNodeIds.has(e.target);
      
      if (!sourceExists || !targetExists) {
        console.warn(`⚠️ Skipping edge ${e.id}: source=${sourceExists ? '✓' : '✗'} target=${targetExists ? '✓' : '✗'}`, {
          source: e.source,
          target: e.target,
        });
        return false;
      }
      return true;
    });

    console.log(`🔧 Force Graph: Filtered ${edges.length - validEdges.length} invalid edges out of ${edges.length} total`);

    // Build multi-edge groups (undirected pairing for curve offset symmetry)
    const key = (a: string, b: string) => (a < b ? `${a}__${b}` : `${b}__${a}`);
    const groups = new Map<string, GraphEdge[]>();
    for (const e of validEdges) {
      const k = key(e.source, e.target);
      const arr = groups.get(k) || [];
      arr.push(e);
      groups.set(k, arr);
    }

    const d3links: D3Link[] = [];
    for (const [, arr] of groups) {
      const total = arr.length;
      // Sort to get deterministic index assignment (e.g., by id)
      arr.sort((a, b) => (a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
      arr.forEach((e, idx) => {
        const isInheritance = Boolean(e.data?.isInheritance);
        d3links.push({
          source: e.source,
          target: e.target,
          label: e.label,
          _parallelIndex: idx,
          _parallelTotal: total,
          _kind: isInheritance ? 'inheritance' : 'association',
          changeType: e.data?.changeType,
        });
      });
    }

    this.links = d3links;

    // CRITICAL: Set nodes first, then links (D3 needs nodes to exist before validating link endpoints)
    this.simulation.nodes(this.nodes);
    (this.simulation.force('link') as d3.ForceLink<D3Node, D3Link>).links(this.links);
    this.simulation.alpha(1).restart();
  }

  /** Update selected node (called externally when selection changes) */
  setSelectedNode(nodeId: string | null) {
    this.nodes.forEach(n => {
      // We'll use a visual indicator for selection (similar to pinned halo)
      (n as any).selected = n.id === nodeId;
    });
    this.render();
  }

  private initZoom() {
    const zoomBehavior = d3
      .zoom<HTMLCanvasElement, unknown>()
      .scaleExtent([0.1, 4])
      .filter((event) => {
        // Prevent zoom/pan when clicking on a node (allow node dragging instead)
        if (event.type === 'mousedown' && event.button === 0) {
          const rect = this.canvas.getBoundingClientRect();
          const cx = event.clientX - rect.left;
          const cy = event.clientY - rect.top;
          const [mx, my] = this.invertToGraphCoords(cx, cy);
          const node = this.findNodeAt(mx, my);
          if (node) return false; // Block zoom/pan, allow drag
        }
        return true; // Allow zoom/pan for other events
      })
      .on('zoom', e => {
        this.transform = e.transform;
        this.render();
      });

    d3.select(this.canvas).call(zoomBehavior as any);
  }

  private initDrag() {
    // Subject function: find the topmost node under the cursor (in graph coords)
    const subject: (event: d3.D3DragEvent<HTMLCanvasElement, unknown, D3Node | null>) => D3Node | null = (event) => {
      // Get mouse position in canvas coordinates
      const rect = this.canvas.getBoundingClientRect();
      const cx = event.sourceEvent.clientX - rect.left;
      const cy = event.sourceEvent.clientY - rect.top;
      // Transform to graph coordinates
      const [mx, my] = this.transform.invert([cx, cy]);
      for (let i = this.nodes.length - 1; i >= 0; i--) {
        const n = this.nodes[i];
        const dx = mx - (n.x ?? 0);
        const dy = my - (n.y ?? 0);
        if (dx * dx + dy * dy <= (n.radius + 4) * (n.radius + 4)) {
          return n;
        }
      }
      return null;
    };

    const dragBehavior = d3
      .drag<HTMLCanvasElement, unknown, D3Node | null>()
      .container(this.canvas)
      .subject(subject)
      .on('start', (event) => {
        const n = event.subject;
        if (!n) return;
        this.canvas.style.cursor = 'grabbing';
        if (!event.active) this.simulation.alphaTarget(0.3).restart();
        n.fx = n.x;
        n.fy = n.y;
      })
      .on('drag', (event) => {
        const n = event.subject;
        if (!n) return;
        // Get mouse position in canvas coordinates from the source event
        const rect = this.canvas.getBoundingClientRect();
        const cx = event.sourceEvent.clientX - rect.left;
        const cy = event.sourceEvent.clientY - rect.top;
        // Transform to graph coordinates
        const [mx, my] = this.transform.invert([cx, cy]);
        n.fx = mx;
        n.fy = my;
      })
      .on('end', (event) => {
        const n = event.subject;
        if (!n) return;
        this.canvas.style.cursor = 'grab';
        
        // Auto-pin the node when drag ends (keep it at the dragged position)
        n.pinned = true;
        n.fx = n.x;
        n.fy = n.y;
        
        // Notify store to persist position
        if (this.onNodePin && n.fx !== undefined && n.fy !== undefined) {
          this.onNodePin(n.id, n.fx, n.fy);
        }
        
        if (!event.active) this.simulation.alphaTarget(0);
        this.render(); // Re-render to show pin halo
      });

    d3.select(this.canvas).call(dragBehavior as any);
    return dragBehavior;
  }

  private initDoubleClickPin() {
    // Right-click to unpin a pinned node
    this.canvas.addEventListener('contextmenu', (e) => {
      e.preventDefault(); // Prevent browser context menu
      
      const rect = this.canvas.getBoundingClientRect();
      const cx = e.clientX - rect.left;
      const cy = e.clientY - rect.top;
      const [mx, my] = this.transform.invert([cx, cy]);

      const n = this.findNodeAt(mx, my);
      if (!n) return;

      // Only unpin if the node is currently pinned
      if (n.pinned) {
        n.pinned = false;
        n.fx = null;
        n.fy = null;
        
        // Notify store to remove persisted position
        if (this.onNodeUnpin) {
          this.onNodeUnpin(n.id);
        }
        
        this.simulation.alpha(0.4).restart();
        this.render();
      }
    });
  }

  private initClickHandler() {
    // Single click to select or deselect
    this.canvas.addEventListener('click', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const cx = e.clientX - rect.left;
      const cy = e.clientY - rect.top;
      const [mx, my] = this.invertToGraphCoords(cx, cy);

      const n = this.findNodeAt(mx, my);
      if (this.onNodeClick) {
        if (n) {
          // Click on a node - select it
          this.onNodeClick(n.id);
        } else {
          // Click on empty space - deselect (pass empty string or special value)
          this.onNodeClick('');
        }
      }
    });
  }

  private initHoverTracking() {
    // Track hover state for visual feedback
    this.canvas.addEventListener('mousemove', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const cx = e.clientX - rect.left;
      const cy = e.clientY - rect.top;
      const [mx, my] = this.invertToGraphCoords(cx, cy);

      const n = this.findNodeAt(mx, my);
      if (n !== this.hoveredNode) {
        this.hoveredNode = n;
        this.canvas.style.cursor = n ? 'pointer' : 'grab';
        this.render(); // Re-render to show hover effect
      }
    });

    this.canvas.addEventListener('mouseleave', () => {
      if (this.hoveredNode) {
        this.hoveredNode = null;
        this.canvas.style.cursor = 'grab';
        this.render();
      }
    });
  }

  /** Convert screen coords (mouse) to graph coords, considering current zoom/pan */
  private invertToGraphCoords(sx: number, sy: number): [number, number] {
    const inv = this.transform.invert([sx, sy]);
    return [inv[0], inv[1]];
  }

  private findNodeAt(mx: number, my: number): D3Node | null {
    for (let i = this.nodes.length - 1; i >= 0; i--) {
      const n = this.nodes[i];
      const dx = mx - (n.x ?? 0);
      const dy = my - (n.y ?? 0);
      if (dx * dx + dy * dy <= (n.radius + 4) * (n.radius + 4)) {
        return n;
      }
    }
    return null;
  }

  /** Quadratic Bezier point at t */
  private quadPoint(t: number, p0: { x: number; y: number }, p1: { x: number; y: number }, p2: { x: number; y: number }) {
    const u = 1 - t;
    const x = u * u * p0.x + 2 * u * t * p1.x + t * t * p2.x;
    const y = u * u * p0.y + 2 * u * t * p1.y + t * t * p2.y;
    return { x, y };
  }

  /** Quadratic Bezier tangent vector at t */
  private quadTangent(t: number, p0: { x: number; y: number }, p1: { x: number; y: number }, p2: { x: number; y: number }) {
    const x = 2 * (1 - t) * (p1.x - p0.x) + 2 * t * (p2.x - p1.x);
    const y = 2 * (1 - t) * (p1.y - p0.y) + 2 * t * (p2.y - p1.y);
    return { x, y };
  }

  /** Compute control point for a curved edge with multi-edge offset. */
  private computeControlPoint(s: D3Node, t: D3Node, link: D3Link) {
    const sx = s.x ?? 0, sy = s.y ?? 0;
    const tx = t.x ?? 0, ty = t.y ?? 0;
    const mx = (sx + tx) / 2;
    const my = (sy + ty) / 2;
    const dx = tx - sx;
    const dy = ty - sy;
    const len = Math.hypot(dx, dy) || 1;
    // Normal vector (perpendicular)
    const nx = -dy / len;
    const ny = dx / len;

    const total = link._parallelTotal ?? 1;
    const idx = link._parallelIndex ?? 0;
    // Offset index centered around zero, e.g., for total=3 => [-1, 0, 1]
    const centered = idx - (total - 1) / 2;
    // Curvature base proportional to edge length (clamped)
    const base = Math.min(80, Math.max(20, len * 0.2));
    const offset = centered * base;

    return { x: mx + nx * offset, y: my + ny * offset };
  }

  /** Draw an arrowhead at (x,y) pointing in direction of angle (radians). */
  private drawArrowhead(ctx: CanvasRenderingContext2D, x: number, y: number, angle: number, size = 8, fill = '#666', outline?: string) {
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(angle);
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(-size, size * 0.5);
    ctx.lineTo(-size, -size * 0.5);
    ctx.closePath();
    if (outline) {
      ctx.fillStyle = '#ffffff';
      ctx.fill();
      ctx.strokeStyle = outline;
      ctx.lineWidth = 1.25;
      ctx.stroke();
    } else {
      ctx.fillStyle = fill;
      ctx.fill();
    }
    ctx.restore();
  }

  /** Main renderer: draws curved links with arrowheads and labels; then nodes. */
  private render() {
    const ctx = this.context;
    ctx.save();
    ctx.clearRect(0, 0, this.width, this.height);
    ctx.translate(this.transform.x, this.transform.y);
    ctx.scale(this.transform.k, this.transform.k);

    // Draw links (curved with arrowheads)
    ctx.lineWidth = 1.25;

    for (const link of this.links) {
      const s = link.source as D3Node;
      const t = link.target as D3Node;
      if (!s || !t || s.x == null || s.y == null || t.x == null || t.y == null) continue;

      const style = REL_STYLE[link._kind];
      const cp = this.computeControlPoint(s, t, link);

      // Override style based on change type
      let strokeColor = style.stroke;
      let lineWidth = 1.25;
      if (link.changeType) {
        switch (link.changeType) {
          case 'created':
            strokeColor = '#22c55e'; // green
            lineWidth = 2.5;
            break;
          case 'modified':
            strokeColor = '#eab308'; // yellow
            lineWidth = 2.5;
            break;
          case 'deleted':
            strokeColor = '#ef4444'; // red
            lineWidth = 2.5;
            ctx.globalAlpha = 0.5;
            break;
        }
      }

      // Path
      ctx.beginPath();
      ctx.setLineDash(style.dash);
      ctx.strokeStyle = strokeColor;
      ctx.lineWidth = lineWidth;
      ctx.moveTo(s.x, s.y);
      ctx.quadraticCurveTo(cp.x, cp.y, t.x, t.y);
      ctx.stroke();
      ctx.setLineDash([]);
      
      if (link.changeType === 'deleted') {
        ctx.globalAlpha = 1.0;
      }

      // Arrowhead: orient by tangent near the end (t=0.95)
      const pEnd = this.quadPoint(0.95, { x: s.x, y: s.y }, cp, { x: t.x, y: t.y });
      const tan = this.quadTangent(0.95, { x: s.x, y: s.y }, cp, { x: t.x, y: t.y });
      const ang = Math.atan2(tan.y, tan.x);

      // Pull tip back by target radius so it touches node boundary instead of center
      const ux = Math.cos(ang);
      const uy = Math.sin(ang);
      const tipX = t.x - ux * ((t.radius ?? 18) + 2);
      const tipY = t.y - uy * ((t.radius ?? 18) + 2);

      // Inheritance: outlined arrow; Association: filled arrow
      if (link._kind === 'inheritance') {
        this.drawArrowhead(ctx, tipX, tipY, ang, 9, style.arrowFill, style.arrowFill);
      } else {
        this.drawArrowhead(ctx, tipX, tipY, ang, 8, style.arrowFill);
      }

      // Label (at midpoint t=0.5)
      if (link.label) {
        const mid = this.quadPoint(0.5, { x: s.x, y: s.y }, cp, { x: t.x, y: t.y });
        ctx.save();
        // Text halo for readability (neutral background)
        ctx.fillStyle = 'rgba(255,255,255,0.9)';
        const padX = 3, padY = 2;
        ctx.font = '10px sans-serif';
        const metrics = ctx.measureText(link.label);
        const w = metrics.width + padX * 2;
        const h = 10 + padY * 2; // rough line height
        ctx.fillRect(mid.x - w / 2, mid.y - h / 2, w, h);

        ctx.fillStyle = style.text;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(link.label, mid.x, mid.y);
        ctx.restore();
      }
    }

    // Draw nodes
    for (const node of this.nodes) {
      if (node.x == null || node.y == null) continue;

      const isHovered = node === this.hoveredNode;

      // Change type halo (before selection and hover)
      if (node.changeType) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius + 8, 0, 2 * Math.PI);
        let haloColor = '#666';
        switch (node.changeType) {
          case 'created':
            haloColor = '#22c55e'; // green
            break;
          case 'modified':
            haloColor = '#eab308'; // yellow
            break;
          case 'deleted':
            haloColor = '#ef4444'; // red
            break;
        }
        ctx.strokeStyle = haloColor;
        ctx.lineWidth = 4;
        ctx.stroke();
      }

      // Hover glow (subtle)
      if (isHovered) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius + 8, 0, 2 * Math.PI);
        ctx.strokeStyle = 'rgba(59, 130, 246, 0.3)';
        ctx.lineWidth = 6;
        ctx.stroke();
      }

      // Selection halo (blue)
      if ((node as any).selected) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius + 6, 0, 2 * Math.PI);
        ctx.strokeStyle = '#3b82f6';
        ctx.lineWidth = 3;
        ctx.stroke();
      }

      // Pin halo (orange dashed)
      if (node.pinned) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius + 5, 0, 2 * Math.PI);
        ctx.strokeStyle = '#f97316';
        ctx.lineWidth = 2;
        ctx.setLineDash([3, 3]);
        ctx.stroke();
        ctx.setLineDash([]);
      }

      // node body - adjust opacity if deleted
      if (node.changeType === 'deleted') {
        ctx.globalAlpha = 0.5;
      }
      
      ctx.beginPath();
      ctx.arc(node.x, node.y, node.radius, 0, 2 * Math.PI);
      ctx.fillStyle = isHovered ? '#5b9bd5' : node.color;
      ctx.fill();
      ctx.strokeStyle = '#2f2f2f';
      ctx.lineWidth = 1.5;
      ctx.stroke();
      
      if (node.changeType === 'deleted') {
        ctx.globalAlpha = 1.0;
      }

      // Multi-line label inside node (max 30 characters total)
      const MAX_LABEL_CHARS = 30;
      const fontSize = 11;
      const lineHeight = 13;
      const maxLines = 3;
      const maxWidth = node.radius * 1.6; // Text area width (leave margins)
      
      ctx.font = `${fontSize}px sans-serif`;
      ctx.textAlign = 'center';
      
      // Word wrap the label
      const words = node.label.split(' ');
      const lines: string[] = [];
      let currentLine = '';
      
      for (const word of words) {
        const testLine = currentLine ? `${currentLine} ${word}` : word;
        const metrics = ctx.measureText(testLine);
        
        if (metrics.width > maxWidth && currentLine) {
          lines.push(currentLine);
          currentLine = word;
        } else {
          currentLine = testLine;
        }
      }
      if (currentLine) lines.push(currentLine);
      
      // Truncate if too many lines or too long
      const isTruncated = lines.length > maxLines || node.label.length > MAX_LABEL_CHARS;
      let displayLines = lines.slice(0, maxLines);
      
      // If last line is too wide or we're truncated, add ellipsis
      if (isTruncated && displayLines.length > 0) {
        const lastIdx = displayLines.length - 1;
        let lastLine = displayLines[lastIdx];
        // Try to fit ellipsis
        while (ctx.measureText(lastLine + '…').width > maxWidth && lastLine.length > 0) {
          lastLine = lastLine.slice(0, -1).trim();
        }
        displayLines[lastIdx] = lastLine + '…';
      }
      
      // Draw text with shadow for visibility
      const totalHeight = displayLines.length * lineHeight;
      const startY = node.y - totalHeight / 2 + lineHeight / 2;
      
      displayLines.forEach((line, i) => {
        const y = startY + i * lineHeight;
        
        // Text shadow for visibility
        ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
        ctx.textBaseline = 'middle';
        ctx.fillText(line, node.x! + 1, y + 1);
        
        // Main text
        ctx.fillStyle = '#ffffff';
        ctx.fillText(line, node.x!, y);
      });

      // Show full label on hover (only if truncated)
      if (isHovered && isTruncated) {
        const tooltipY = node.y! - node.radius - 10;
        const tooltipFont = 'bold 13px sans-serif';
        ctx.font = tooltipFont;
        
        // Measure full label for background
        const metrics = ctx.measureText(node.label);
        const textWidth = metrics.width;
        const textHeight = 16;
        const padding = 6;
        
        // Tooltip background (darker, more prominent)
        ctx.fillStyle = 'rgba(15, 23, 42, 0.95)';
        ctx.strokeStyle = 'rgba(59, 130, 246, 0.8)';
        ctx.lineWidth = 2;
        
        const rectX = node.x! - textWidth / 2 - padding;
        const rectY = tooltipY - textHeight / 2 - padding;
        const rectWidth = textWidth + padding * 2;
        const rectHeight = textHeight + padding * 2;
        
        // Rounded rectangle
        const radius = 4;
        ctx.beginPath();
        ctx.moveTo(rectX + radius, rectY);
        ctx.lineTo(rectX + rectWidth - radius, rectY);
        ctx.quadraticCurveTo(rectX + rectWidth, rectY, rectX + rectWidth, rectY + radius);
        ctx.lineTo(rectX + rectWidth, rectY + rectHeight - radius);
        ctx.quadraticCurveTo(rectX + rectWidth, rectY + rectHeight, rectX + rectWidth - radius, rectY + rectHeight);
        ctx.lineTo(rectX + radius, rectY + rectHeight);
        ctx.quadraticCurveTo(rectX, rectY + rectHeight, rectX, rectY + rectHeight - radius);
        ctx.lineTo(rectX, rectY + radius);
        ctx.quadraticCurveTo(rectX, rectY, rectX + radius, rectY);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
        
        // Full label text
        ctx.fillStyle = '#ffffff';
        ctx.textBaseline = 'middle';
        ctx.fillText(node.label, node.x!, tooltipY);
      }
    }

    ctx.restore();
  }

  /** Stop the simulation and clean up */
  destroy() {
    this.simulation.stop();
    this.canvas.remove();
  }
}
