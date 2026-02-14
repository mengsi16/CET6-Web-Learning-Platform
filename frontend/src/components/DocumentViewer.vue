<template>
  <div class="document-viewer">
    <div class="viewer-wrapper" :style="{ transform: `scale(${zoomLevel})` }">
      <!-- PDF Page Container -->
      <div 
        class="pdf-page" 
        ref="pageContainer"
        @mousemove="handlePageMouseMove"
        @mouseleave="handlePageMouseLeave"
      >
        <!-- Layer 1: Simulated PDF Content (Text Layer) -->
        <div class="text-layer">
          <p v-for="(line, index) in displayContent" :key="index" class="pdf-text">
            {{ line }}
          </p>
        </div>

        <!-- Layer 2: Drawing Canvas -->
        <canvas 
          ref="drawCanvas"
          class="draw-canvas"
          :class="{ 'pointer-events-none': currentTool === 'cursor' }"
          @mousedown="startDrawing"
          @mousemove="draw"
          @mouseup="stopDrawing"
          @mouseleave="stopDrawing"
        ></canvas>
      </div>
    </div>

    <!-- Zoom Controls -->
    <div class="zoom-controls">
      <button @click="zoomOut"><i class="fas fa-minus"></i></button>
      <span>{{ Math.round(zoomLevel * 100) }}%</span>
      <button @click="zoomIn"><i class="fas fa-plus"></i></button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue';

const props = defineProps(['fileUrl', 'currentTool', 'currentColor', 'toolOptions', 'content', 'initialStrokes']);
const emit = defineEmits(['show-translation', 'mark-word', 'hide-translation', 'save-strokes']);
const displayContent = computed(() => props.content || []);

const zoomLevel = ref(1.0);
const isDrawing = ref(false);
const drawCanvas = ref(null);
const ctx = ref(null);
const pageContainer = ref(null);

// Vector Storage
const strokes = ref([]); // { type: 'path'|'rect'|'circle'|'erase', color: string, width: number, points: {x,y}[], alpha: number }
const currentStroke = ref(null);
const hoveringStroke = ref(null);
const selectionRect = ref(null); // Track selection for auto-hide

const initCanvas = () => {
  if (pageContainer.value && drawCanvas.value) {
    if (pageContainer.value.clientWidth === 0) return; // Guard against hidden state
    
    drawCanvas.value.width = pageContainer.value.clientWidth;
    drawCanvas.value.height = pageContainer.value.clientHeight;
    ctx.value = drawCanvas.value.getContext('2d');
    ctx.value.lineCap = 'round';
    ctx.value.lineJoin = 'round';
    renderCanvas();
  }
};

const resizeCanvas = () => {
  if (pageContainer.value && pageContainer.value.clientWidth > 0) {
      initCanvas();
  }
};

const zoomIn = () => zoomLevel.value += 0.1;
const zoomOut = () => { if (zoomLevel.value > 0.2) zoomLevel.value -= 0.1; };

// Helper: Distance between point and segment
const distToSegment = (p, v, w) => {
  const l2 = (w.x - v.x)**2 + (w.y - v.y)**2;
  if (l2 === 0) return Math.hypot(p.x - v.x, p.y - v.y);
  let t = ((p.x - v.x) * (w.x - v.x) + (p.y - v.y) * (w.y - v.y)) / l2;
  t = Math.max(0, Math.min(1, t));
  return Math.hypot(p.x - (v.x + t * (w.x - v.x)), p.y - (v.y + t * (w.y - v.y)));
};

// Check intersection for Stroke Eraser
const checkStrokeIntersection = (s1, eraserPath) => {
    // Defines a hit threshold
    const THRESHOLD = 10; 
    
    // Check if any point in eraserPath is close to any segment in s1
    // Simplification: Check distance from eraser points to s1 points
    // Better: Check bounding boxes first
    
    for (const ep of eraserPath) {
        // Simple point-to-point check for speed in JS
        // For line segments, we should use segment distance
        for (let i = 0; i < s1.points.length - 1; i++) {
            const p1 = s1.points[i];
            const p2 = s1.points[i+1];
            if (distToSegment(ep, p1, p2) < THRESHOLD + (s1.width/2)) {
                return true;
            }
        }
    }
    return false;
};

// Drawing Logic
let startPoint = null;

const getPos = (evt) => {
  const rect = drawCanvas.value.getBoundingClientRect();
  const scaleX = drawCanvas.value.width / rect.width;
  const scaleY = drawCanvas.value.height / rect.height;
  return {
    x: (evt.clientX - rect.left) * scaleX,
    y: (evt.clientY - rect.top) * scaleY
  };
};

const startDrawing = (evt) => {
  if (props.currentTool === 'cursor') return;
  isDrawing.value = true;
  const pos = getPos(evt);
  startPoint = pos;

  // New Stroke Object
  currentStroke.value = {
      type: props.currentTool,
      color: props.currentColor,
      width: 2,
      alpha: 1.0,
      points: [pos],
      isPreview: true // Flag to show it's being drawn
  };
  
  // Custom properties based on tool
  if (props.currentTool === 'highlight') {
      currentStroke.value.width = 15;
      currentStroke.value.alpha = 0.5; // Semi-transparent
      currentStroke.value.blendMode = 'multiply'; // Simulation, canvas uses globalCompositeOperation
  } else if (props.currentTool === 'underline') {
       currentStroke.value.width = 2;
  } else if (props.currentTool === 'eraser') {
       currentStroke.value.width = 20;
       currentStroke.value.type = 'erase';
  }
  
  strokes.value.push(currentStroke.value);
};

const draw = (evt) => {
  if (!isDrawing.value || !currentStroke.value) return;
  const pos = getPos(evt);
  
  if (props.currentTool === 'highlight' || props.currentTool === 'underline') {
      // Check Line Type
      if (props.toolOptions.lineType === 'straight') {
          // Replace all middle points, just keep start and current
          currentStroke.value.points = [startPoint, pos];
      } else {
          currentStroke.value.points.push(pos);
      }
  } else if (props.currentTool === 'box' || props.currentTool === 'circle') {
       // Just update end point for preview
       currentStroke.value.points = [startPoint, pos];
  } else if (props.currentTool === 'eraser') {
      currentStroke.value.points.push(pos);
      
      // Real-time Stroke Eraser Logic?
      // No, usually stroke eraser works on mouse up or hover.
      // But user said "Select to erase whole stroke or pixel".
      // If Pixel Eraser: Just adding points to an "erase" stroke works visually (masking).
      // If Stroke Eraser: Maybe we should visualize the erasing path red?
      if (props.toolOptions.eraserType === 'stroke') {
          // Optional: Visual indicator of eraser path
      }
  }
  
  // Trigger reactivity for render
  // strokes.value = [...strokes.value]; // Or relying on deep watch
  renderCanvas();
};

const stopDrawing = (evt) => {
  if (!isDrawing.value) return;
  isDrawing.value = false;
  if (!currentStroke.value) return;

  const pos = getPos(evt);
  
  // Finalize
  currentStroke.value.isPreview = false;
  
  // Handle Stroke Eraser Logic
  if (props.currentTool === 'eraser' && props.toolOptions.eraserType === 'stroke') {
      const eraserPath = currentStroke.value.points;
      // Remove the eraser stroke itself, it's just a tool
      strokes.value.pop(); 
      
      // Filter out strokes that intersect
      strokes.value = strokes.value.filter(s => {
          if (s.type === 'erase') return true; // Keep pixel erasures? Or remove them too?
          return !checkStrokeIntersection(s, eraserPath);
      });
  } else {
      // "Identify" logic for Highlighter
      if (props.currentTool === 'highlight') {
  emit('save-strokes', strokes.value);
         // Logic to detect word under highlight
         checkIntersectionWithText(currentStroke.value.points, evt);
      }
  }
  
  currentStroke.value = null;
  renderCanvas();
};

const renderCanvas = () => {
    if (!ctx.value || !drawCanvas.value) return;
    const c = ctx.value;
    c.clearRect(0, 0, drawCanvas.value.width, drawCanvas.value.height);
    
    strokes.value.forEach(stroke => {
        c.save();
        c.beginPath();
        
        if (stroke.type === 'erase') {
             // Pixel Eraser
             c.globalCompositeOperation = 'destination-out';
             c.lineWidth = stroke.width;
             c.lineCap = 'round';
             c.lineJoin = 'round';
        } else {
            c.globalCompositeOperation = 'source-over';
            // If highlight, maybe use multiply?
            // Note: destination-out clears pixels. Source-over draws.
            // If we want highlighter to look 'behind' text, the text must be ON the canvas or we use CSS mix-blend-mode.
            // Since text is DOM P tags, the canvas is ON TOP.
            // So we need opacity.
            c.globalAlpha = stroke.alpha;
            c.strokeStyle = stroke.color;
            c.lineWidth = stroke.width;
        }

        if (stroke.type === 'box') {
             const start = stroke.points[0];
             const end = stroke.points[1];
             if (start && end) c.strokeRect(start.x, start.y, end.x - start.x, end.y - start.y);
        } else if (stroke.type === 'circle') {
             const start = stroke.points[0];
             const end = stroke.points[1];
             if (start && end) {
                const radius = Math.hypot(end.x - start.x, end.y - start.y);
                c.arc(start.x, start.y, radius, 0, 2 * Math.PI);
                c.stroke();
             }
        } else {
            // Path based
            if (stroke.points.length > 0) {
                c.moveTo(stroke.points[0].x, stroke.points[0].y);
                for (let i = 1; i < stroke.points.length; i++) {
                    c.lineTo(stroke.points[i].x, stroke.points[i].y);
                }
                c.stroke();
            }
        }
        
        c.restore();
    });
};

const checkIntersectionWithText = (strokePoints, evt) => {
    // We need to find the text under the drawn stroke.
    // Since the canvas is on top, we temporarily disable pointer events on it
    // so we can "pierce" through to the text layer.
    if (!drawCanvas.value) return;

    const canvas = drawCanvas.value;
    const originalPointerEvents = canvas.style.pointerEvents;
    canvas.style.pointerEvents = 'none';

    // We'll check a few points along the stroke to catch the word(s).
    // checking every point is too expensive, so let's check every Nth point.
    const step = Math.max(1, Math.floor(strokePoints.length / 5)); 
    const wordsFound = new Set();
    
    // Helper to get client coordinates from canvas coordinates
    const rect = canvas.getBoundingClientRect();
    const scaleX = rect.width / canvas.width;
    const scaleY = rect.height / canvas.height;

    for (let i = 0; i < strokePoints.length; i += step) {
        const p = strokePoints[i];
        const clientX = rect.left + p.x * (1/scaleX); // p.x is canvas coord
        // Actually, getPos did: x: (evt.clientX - rect.left) * scaleX
        // So clientX = (p.x / scaleX) + rect.left
        // But wait, scaleX might be > 1 if canvas.width > rect.width (high DPI)
        // Let's re-verify getPos logic.
        // getPos: x = (clientX - left) * (width / rectWidth)
        // -> x * (rectWidth / width) = clientX - left
        // -> clientX = x * (rectWidth / width) + left
        
        const cx = p.x * (rect.width / canvas.width) + rect.left;
        const cy = p.y * (rect.height / canvas.height) + rect.top;

        // Use caretRangeFromPoint (Standard) or caretPositionFromPoint (Firefox)
        let range, node, offset;
        if (document.caretRangeFromPoint) {
            range = document.caretRangeFromPoint(cx, cy);
            if (range) {
                node = range.startContainer;
                offset = range.startOffset;
            }
        } else if (document.caretPositionFromPoint) {
            const pos = document.caretPositionFromPoint(cx, cy);
            if (pos) {
                node = pos.offsetNode;
                offset = pos.offset;
            }
        }

        if (node && node.nodeType === Node.TEXT_NODE) {
            const word = getWordAtOffset(node.textContent, offset);
            if (word) wordsFound.add(word);
        }
    }

    canvas.style.pointerEvents = originalPointerEvents;

    if (wordsFound.size > 0) {
        // Just take the first word or join them? 
        // Typically a user highlights one word or phrase. 
        // For dictionary lookup, single word is best.
        // Let's prioritize the longest word found or the first one.
        const text = Array.from(wordsFound)[0]; 

        emit('mark-word', text);
        
        if (evt) {
            emit('show-translation', {
                x: evt.clientX,
                y: evt.clientY + 20,
                text: text
            });
        }
    }
};

const getWordAtOffset = (text, offset) => {
    // Find word boundaries
    const isWordChar = (char) => /[a-zA-Z0-9\-\']/.test(char);
    
    let start = offset;
    while (start > 0 && isWordChar(text[start - 1])) {
        start--;
    }
    
    let end = offset;
    while (end < text.length && isWordChar(text[end])) {
        end++;
    }
    
    if (start < end) {
        return text.substring(start, end);
    }
    return null;
};

const handlePageMouseMove = (evt) => {
    // Safety check for canvas availability
    if (!drawCanvas.value) return;

    // If drawing, we skip this to avoid conflict/perf issues,
    // although showing translation while highlighting could be cool, usually distraction.
    if (isDrawing.value) return;

    const pos = getPos(evt); // Canvas relative pos
    const clientX = evt.clientX;
    const clientY = evt.clientY;

    // 1. Check if hovering over stored selection
    if (selectionRect.value) {
        const rect = selectionRect.value;
        const PADDING = 10;
        // Check if mouse is within rect + padding
        if (clientX >= rect.left - PADDING && 
            clientX <= rect.right + PADDING &&
            clientY >= rect.top - PADDING &&
            clientY <= rect.bottom + PADDING) {
            // Still inside selection, do nothing (keep showing)
            return;
        } else {
            // Left selection
            selectionRect.value = null; // Clear it so we don't check again
            emit('hide-translation');
        }
    }

    // 2. Find if mouse is over any 'highlight' stroke
    // Iterate in reverse to match visual stacking (top first)
    let foundStroke = null;
    for (let i = strokes.value.length - 1; i >= 0; i--) {
        const s = strokes.value[i];
        if (s.type === 'highlight') {
            // Treat mouse pos as a tiny path or use logic similar to eraser
            if (checkStrokeIntersection(s, [pos])) {
                foundStroke = s;
                break;
            }
        }
    }

    if (foundStroke) {
        if (hoveringStroke.value !== foundStroke) {
            hoveringStroke.value = foundStroke;
            
            // Determine text for this stroke
            const strokePoints = foundStroke.points;
            
            // Use the center point of the stroke for lookup
            const centerPoint = strokePoints[Math.floor(strokePoints.length / 2)];
            
            // Get client coordinates from canvas coordinates
            const canvas = drawCanvas.value;
            const rect = canvas.getBoundingClientRect();
            const cx = centerPoint.x * (rect.width / canvas.width) + rect.left;
            const cy = centerPoint.y * (rect.height / canvas.height) + rect.top;

            // Use caretRangeFromPoint / caretPositionFromPoint
            let node, offset;
            const originalPointerEvents = canvas.style.pointerEvents;
            canvas.style.pointerEvents = 'none'; // Temporarily pass through

            if (document.caretRangeFromPoint) {
                const range = document.caretRangeFromPoint(cx, cy);
                if (range) {
                    node = range.startContainer;
                    offset = range.startOffset;
                }
            } else if (document.caretPositionFromPoint) {
                const pos = document.caretPositionFromPoint(cx, cy);
                if (pos) {
                    node = pos.offsetNode;
                    offset = pos.offset;
                }
            }
            
            canvas.style.pointerEvents = originalPointerEvents; // Restore

            let text = null;
            if (node && node.nodeType === Node.TEXT_NODE) {
                 text = getWordAtOffset(node.textContent, offset);
            }
            // Fallback for visual continuity if caret/range fails? 
            // For now, only show if we hit text.
            
            if (!text) return; // Don't show popup if no text mapped

             emit('show-translation', {
                 x: evt.clientX,
                 y: evt.clientY + 20, // Offset a bit
                 text: text
             });
        }
    } else {
        if (hoveringStroke.value) {
            hoveringStroke.value = null;
            emit('hide-translation');
        }
    }
};

const handlePageMouseLeave = () => {
    if (hoveringStroke.value) {
        hoveringStroke.value = null;
        emit('hide-translation');
    }
};

// Text Selection Listener for "Cursor" mode
onMounted(() => {
    document.addEventListener('mouseup', () => {
         if (props.currentTool !== 'cursor') return;
         const selection = window.getSelection();
         const text = selection.toString().trim();
         
         if (text.length > 0) {
             const range = selection.getRangeAt(0);
             const rect = range.getBoundingClientRect();
             // Store rect for hover-out detection
             selectionRect.value = rect;
             
             emit('show-translation', {
                 x: rect.left,
                 y: rect.bottom + 10,
                 text: text
             });
         } else {
             // Clicked without selection -> clear
             if (selectionRect.value) {
                 selectionRect.value = null;
                 emit('hide-translation');
             }
         }
    });
});

// Initialize Canvas & Watchers
onMounted(() => {
  initCanvas();
  window.addEventListener('resize', resizeCanvas);
});

watch(() => props.isVisible, (newVal) => {
    if (newVal) {
        requestAnimationFrame(() => initCanvas());
    }
});

watch(displayContent, () => {
    requestAnimationFrame(() => initCanvas());
}, { deep: true });

watch(() => strokes.value, () => {
    requestAnimationFrame(renderCanvas);
}, { deep: true });

watch(() => props.initialStrokes, (val) => {
    if (val) {
        strokes.value = JSON.parse(JSON.stringify(val));
        renderCanvas();
    }
}, { immediate: true });

</script>

<style scoped>
.document-viewer {
  width: 100%;
  height: 100%;
  overflow: auto;
  display: flex;
  justify-content: center;
  background-color: #525659;
  padding: 20px;
}

.viewer-wrapper {
  transition: transform 0.2s;
  transform-origin: top center;
}

.pdf-page {
  width: 800px; /* A4 Ratio approx */
  min-height: 1131px;
  background: white;
  box-shadow: 0 0 10px rgba(0,0,0,0.5);
  position: relative;
}

.text-layer {
  padding: 50px;
  font-family: 'Times New Roman', Times, serif;
  font-size: 18px;
  line-height: 1.6;
  user-select: text; /* Allow selection */
}

.draw-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 10;
  cursor: crosshair;
}

.pointer-events-none {
  pointer-events: none; /* Let clicks pass through to text */
}

.zoom-controls {
  position: fixed;
  bottom: 20px;
  right: 20px;
  background: rgba(0,0,0,0.7);
  color: white;
  padding: 5px 10px;
  border-radius: 4px;
  display: flex;
  gap: 10px;
  align-items: center;
}

.zoom-controls button {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
}
</style>