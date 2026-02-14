<template>
  <div class="top-toolbar">
    <div class="tool-group">
      <select 
        class="paper-select" 
        @change="$emit('select-paper', $event.target.value)"
      >
        <option value="" disabled selected>Select Paper</option>
        <option v-for="paper in paperList" :key="paper.id" :value="paper.id">
          {{ paper.label }}
        </option>
      </select>
      <div class="separator"></div>

      <button 
        v-for="tool in tools" 
        :key="tool.id"
        :class="{ active: currentTool === tool.id }"
        @click="$emit('set-tool', tool.id)"
        :title="tool.name"
      >
        <i :class="tool.icon"></i>
      </button>
      
      <div class="separator"></div>

      <input 
        type="color" 
        :value="currentColor" 
        @input="$emit('set-color', $event.target.value)"
        title="Color Picker"
      />
      
      <!-- Tool Options Area -->
      <div class="tool-options" v-if="currentTool === 'highlight' || currentTool === 'underline'">
        <select :value="toolOptions.lineType" @change="$emit('set-tool-option', 'lineType', $event.target.value)">
            <option value="free">Freehand</option>
            <option value="straight">Straight Line</option>
        </select>
      </div>
      
      <div class="tool-options" v-if="currentTool === 'eraser'">
        <select :value="toolOptions.eraserType" @change="$emit('set-tool-option', 'eraserType', $event.target.value)">
            <option value="pixel">Pixel Eraser</option>
            <option value="stroke">Stroke Eraser</option>
        </select>
      </div>

    </div>

    <div class="tool-group right">
      <button :class="{ active: currentView === 'viewer' }" @click="$emit('switch-view', 'viewer')">
         <i class="fas fa-file-alt"></i> Document
      </button>
      <button :class="{ active: currentView === 'wordbook' }" @click="$emit('switch-view', 'wordbook')">
         <i class="fas fa-book"></i> Word Book
      </button>
      <div class="separator"></div>
      <button @click="$emit('toggle-markdown')" title="Open Essay Writer">
        <i class="fas fa-pen-nib"></i> Essay
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

defineProps(['currentTool', 'currentColor', 'toolOptions', 'currentView', 'paperList']);
defineEmits(['set-tool', 'set-color', 'toggle-markdown', 'set-tool-option', 'switch-view', 'select-paper']);

const tools = [
  { id: 'cursor', icon: 'fas fa-mouse-pointer', name: 'Select Text' },
  { id: 'highlight', icon: 'fas fa-highlighter', name: 'Highlight Brush' },
  { id: 'underline', icon: 'fas fa-pen', name: 'Pen / Underline' },
  { id: 'box', icon: 'far fa-square', name: 'Box Tool' },
  { id: 'circle', icon: 'far fa-circle', name: 'Circle Tool' },
  { id: 'eraser', icon: 'fas fa-eraser', name: 'Eraser' }
];
</script>

<style scoped>
.top-toolbar {
  height: 50px;
  background-color: #333;
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.2);
  z-index: 10;
}

.tool-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.tool-options select {
    background: #555;
    color: white;
    border: 1px solid #777;
    padding: 5px;
    border-radius: 4px;
}

button {
  background: none;
  border: 1px solid transparent;
  color: #ccc;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

button:hover {
  background-color: #444;
  color: white;
}

button.active {
  background-color: #555;
  color: #4caf50;
  border-color: #666;
}

.separator {
  width: 1px;
  height: 30px;
  background-color: #555;
  margin: 0 10px;
}

input[type="color"] {
  border: none;
  width: 30px;
  height: 30px;
  cursor: pointer;
  background: none;
}

.paper-select {
  background: #444;
  color: #ddd;
  border: 1px solid #555;
  padding: 5px 10px;
  border-radius: 4px;
  margin-right: 10px;
}
</style>