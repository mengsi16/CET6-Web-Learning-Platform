<template>
  <div 
    class="side-toolbar" 
    :style="{ width: toolbarWidth + 'px' }"
    @dragover.prevent 
    @drop="handleDrop"
  >
    <div class="resizer" @mousedown="startResize"></div>

    <div class="toolbar-handle" title="Drag to Resize">
      <i class="fas fa-ellipsis-h"></i>
    </div>
    
    <div 
      v-for="tool in tools" 
      :key="tool.id"
      class="side-tool-item"
      :class="{ active: currentTool === tool.id }"
      draggable="true"
      @dragstart="startDrag($event, tool)"
      @dragend="endDrag($event, tool)"
      @click="$emit('select-tool', tool.id)"
      :title="tool.name"
    >
      <i :class="tool.icon"></i>
    </div>

    <div class="add-button" @click="showAddMenu = !showAddMenu">
      <i class="fas fa-plus"></i>
    </div>

    <div v-if="showAddMenu" class="add-menu">
      <div v-for="tool in availableTools" :key="tool.id" @click="addTool(tool)">
        <i :class="tool.icon"></i> {{ tool.name }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';

const props = defineProps(['tools', 'currentTool', 'availableTools']);
const emit = defineEmits(['add-tool', 'remove-tool', 'select-tool']);

const showAddMenu = ref(false);
const toolbarWidth = ref(60);
const isResizing = ref(false);

const startDrag = (evt, tool) => {
  evt.dataTransfer.effectAllowed = 'move';
  evt.dataTransfer.dropEffect = 'move';
};

const endDrag = (evt, tool) => {
  const sidebar = document.querySelector('.side-toolbar');
  const rect = sidebar.getBoundingClientRect();
  const x = evt.clientX;
  
  // If outside the bounds (with some buffer)
  if (x > rect.right + 50 || x < rect.left - 50) {
     emit('remove-tool', tool.id);
  }
};

const addTool = (tool) => {
  emit('add-tool', tool);
  showAddMenu.value = false;
};

const handleDrop = () => {};

// Resizing Logic
const startResize = () => {
    isResizing.value = true;
    document.addEventListener('mousemove', handleResize);
    document.addEventListener('mouseup', stopResize);
    document.body.style.cursor = 'ew-resize';
};

const handleResize = (e) => {
    if (!isResizing.value) return;
    const newWidth = e.clientX;
    if (newWidth > 50 && newWidth < 200) {
        toolbarWidth.value = newWidth;
    }
};

const stopResize = () => {
    isResizing.value = false;
    document.removeEventListener('mousemove', handleResize);
    document.removeEventListener('mouseup', stopResize);
    document.body.style.cursor = '';
};
</script>

<style scoped>
.side-toolbar {
  background: #444;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px 0;
  z-index: 5;
  position: relative;
  min-width: 50px;
}

.resizer {
    position: absolute;
    right: -5px;
    top: 0;
    width: 10px;
    height: 100%;
    cursor: ew-resize;
    z-index: 10;
}

.toolbar-handle {
  color: #888;
  margin-bottom: 10px;
}

.side-tool-item {
  width: 80%; /* Scale with width */
  aspect-ratio: 1; /* Keep square */
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 10px;
  color: #ccc;
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 1.2rem;
}

.side-tool-item:hover {
  background: #555;
  color: white;
}

.side-tool-item.active {
  background: #4caf50;
  color: white;
}

.add-button {
  margin-top: auto; /* Push to bottom or just below list */
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 1px dashed #777;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #777;
  cursor: pointer;
}

.add-button:hover {
  border-color: #aaa;
  color: #aaa;
}

.add-menu {
  position: absolute;
  left: 100%;
  bottom: 0;
  background: #333;
  color: white;
  min-width: 150px;
  border-radius: 0 4px 4px 0;
  box-shadow: 2px 2px 10px rgba(0,0,0,0.3);
}

.add-menu div {
  padding: 10px;
  cursor: pointer;
}

.add-menu div:hover {
  background: #444;
}
</style>