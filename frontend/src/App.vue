<template>
  <div class="main-container">
    <!-- Top Toolbar (Photoshop-like) -->
    <TopToolbar 
      :currentTool="currentTool"
      :currentColor="currentColor"
      :toolOptions="currentToolOptions"
      :currentView="currentView"
      :paperList="paperList"
      @set-tool="setTool"
      @set-tool-option="setToolOption"
      @set-color="setColor"
      @toggle-markdown="toggleMarkdown"
      @switch-view="currentView = $event"
      @select-paper="handleSelectPaper"
    />

    <div class="content-area">
      <SideToolbar v-if="currentView === 'viewer'"
        :tools="commonTools"
        :availableTools="availableTools"
        @remove-tool="removeCommonTool"
        @add-tool="addCommonTool"
        @select-tool="setTool"
        :currentTool="currentTool"
      />

      <!-- Main Display Area -->
      <div v-show="currentView === 'viewer'" class="viewer-container" ref="viewerContainer">
        <DocumentViewer 
          :fileUrl="currentFileUrl" 
          :currentTool="currentTool"
          :currentColor="currentColor"
          :toolOptions="currentToolOptions"
          :content="documentContent"
          :initialStrokes="currentStrokes"
          :isVisible="currentView === 'viewer'"
          @show-translation="handleTranslation"
          @hide-translation="translationPopup.show = false"
          @mark-word="handleMarkWord"
          @save-strokes="handleSaveStrokes"
        />
      </div>
      
      <!-- Essay / Markdown Editor Split Pane -->
      <div v-if="showMarkdown && currentView === 'viewer'" class="essay-container">
        <div class="essay-header">
           <span>Essay / Notes</span>
           <div>
               <button class="save-btn" @click="handleSaveEssay(true)">Save</button>
               <button @click="toggleMarkdown"><i class="fas fa-times"></i></button>
           </div>
        </div>
        <div class="essay-body">
            <!-- Top: Preview -->
            <div class="markdown-preview" v-html="renderedMarkdown"></div>
            <!-- Bottom: Editor -->
            <textarea 
                v-model="markdownText" 
                placeholder="# Start writing here..."
                class="markdown-input"
            ></textarea>
        </div>
      </div>
      
      <!-- Word Book View -->
      <div v-if="currentView === 'wordbook'" class="viewer-container" style="background: #f5f5f5;">
          <WordBook :words="markedWords" @delete-word="handleDeleteWord" />
      </div>
    </div>

    <!-- Translation Popup -->
    <div v-if="translationPopup.show" 
         class="translation-popup" 
         :style="{ left: translationPopup.x + 'px', top: translationPopup.y + 'px' }">
        <div class="popup-header">
            <strong>{{ translationPopup.word }}</strong>
            <button class="close-btn" @click="translationPopup.show = false">×</button>
        </div>
        <div class="popup-body">
            <div v-if="translationPopup.loading">Loading...</div>
            <div v-else>
                <p>{{ translationPopup.cnen }}</p>
            </div>
        </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import { marked } from 'marked'; 
import TopToolbar from './components/TopToolbar.vue';
import SideToolbar from './components/SideToolbar.vue';
import DocumentViewer from './components/DocumentViewer.vue';
import WordBook from './components/WordBook.vue';

// State
const paperList = ref([]); // Flattened list for select dropdown
const documentContent = ref([]); // Content text lines
const currentView = ref('viewer'); // 'viewer' | 'wordbook'
const currentTool = ref('cursor'); // cursor, highlight, underline, box, circle, eraser
const currentToolOptions = ref({
    lineType: 'free', // 'free', 'straight'
    eraserType: 'pixel' // 'pixel', 'stroke'
});
const currentColor = ref('#ff0000');
const showMarkdown = ref(false);
const markdownText = ref('');
const markdownWidth = ref(400);
const currentFileUrl = ref('/sample.pdf'); // Placeholder
const currentDocId = ref(null);
const currentStrokes = ref([]);

// Master list of all possible tools
const allTools = [
  { id: 'cursor', icon: 'fas fa-mouse-pointer', name: 'Select Text' },
  { id: 'highlight', icon: 'fas fa-highlighter', name: 'Highlight Brush' },
  { id: 'underline', icon: 'fas fa-pen', name: 'Pen / Underline' },
  { id: 'box', icon: 'far fa-square', name: 'Box Tool' },
  { id: 'circle', icon: 'far fa-circle', name: 'Circle Tool' },
  { id: 'eraser', icon: 'fas fa-eraser', name: 'Eraser' },
  { id: 'star', icon: 'fas fa-star', name: 'Star Mark' },
  { id: 'check', icon: 'fas fa-check', name: 'Check Mark' },
  { id: 'question', icon: 'fas fa-question', name: 'Question Mark' }
];

const commonTools = ref([
  { id: 'highlight', icon: 'fas fa-highlighter', name: 'Highlight Brush' },
  { id: 'underline', icon: 'fas fa-pen', name: 'Pen / Underline' },
  { id: 'eraser', icon: 'fas fa-eraser', name: 'Eraser' }
]);

const availableTools = computed(() => {
    const commonIds = commonTools.value.map(t => t.id);
    return allTools.filter(t => !commonIds.includes(t.id));
});

const translationPopup = ref({
  show: false,
  x: 0,
  y: 0,
  word: '',
  cnen: '',
  loading: false
});

// Methods
const setTool = (tool) => {
  currentTool.value = tool;
};

const setToolOption = (option, value) => {
    currentToolOptions.value[option] = value;
};

const setColor = (color) => {
  currentColor.value = color;
};

const toggleMarkdown = () => {
  showMarkdown.value = !showMarkdown.value;
};

const removeCommonTool = (toolId) => {
  const index = commonTools.value.findIndex(t => t.id === toolId);
  if (index !== -1) commonTools.value.splice(index, 1);
};

const addCommonTool = (tool) => {
  // Logic to add tool if not exists
  if (!commonTools.value.find(t => t.id === tool.id)) {
      commonTools.value.push(tool);
  }
};

// Marked Words Logic
const markedWords = ref([]);

const fetchVocabulary = async () => {
  try {
    const res = await fetch('http://localhost:8000/api/v1/user/vocabulary');
    const json = await res.json();
    if (json.code === 200) {
      markedWords.value = json.data.items;
    }
  } catch (e) {
    console.error(e);
  }
};

const handleMarkWord = async (wordText) => {
    if (!wordText) return;
    try {
        const res = await fetch('http://localhost:8000/api/v1/user/vocabulary', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ word: wordText })
        });
        const json = await res.json();
        if (json.code === 200) {
           markedWords.value.push(json.data);
        }
    } catch (e) { console.error(e); }
};

const handleDeleteWord = async (id) => {
    try {
        await fetch(`http://localhost:8000/api/v1/user/vocabulary/${id}`, { method: 'DELETE' });
        markedWords.value = markedWords.value.filter(w => w.id !== id);
    } catch(e) { console.error(e); }
}

// Document fetching
const fetchPapers = async () => {
    try {
        const res = await fetch('http://localhost:8000/api/v1/documents/list');
        const json = await res.json();
        if (json.code === 200) {
            const flattened = [];
            json.data.forEach(yearGroup => {
                yearGroup.papers.forEach(paper => {
                    flattened.push({
                         id: paper.id,
                         label: `${yearGroup.year}年${yearGroup.month}月 - ${paper.title}`,
                         ...paper
                    });
                });
            });
            paperList.value = flattened;
        }
    } catch (err) { console.error(err); }
};

const handleSelectPaper = async (paperId) => {
    currentDocId.value = paperId;
    try {
        const res = await fetch(`http://localhost:8000/api/v1/documents/content?doc_id=${encodeURIComponent(paperId)}`);
        const json = await res.json();
        if (json.code === 200) {
            documentContent.value = json.data.lines;
        }
        
        // Load annotations
        const noteRes = await fetch(`http://localhost:8000/api/v1/user/annotations?doc_id=${encodeURIComponent(paperId)}`);
        const noteJson = await noteRes.json();
        if (noteJson.code === 200) {
            currentStrokes.value = noteJson.data || [];
        } else {
            currentStrokes.value = [];
        }

        // Load Essay
        markdownText.value = ''; // Reset first
        const essayRes = await fetch(`http://localhost:8000/api/v1/user/essay?doc_id=${encodeURIComponent(paperId)}`);
        const essayJson = await essayRes.json();
        if (essayJson.code === 200 && essayJson.data && essayJson.data.content) {
            markdownText.value = essayJson.data.content;
        }

    } catch (err) { console.error(err); }
};

const handleSaveStrokes = async (strokes) => {
    if (!currentDocId.value) return;
    try {
        await fetch('http://localhost:8000/api/v1/user/annotations', {
             method: 'POST',
             headers: { 'Content-Type': 'application/json' },
             body: JSON.stringify({ docId: currentDocId.value, strokes })
        });
    } catch (e) { console.error(e); }
};

const renderedMarkdown = computed(() => marked.parse(markdownText.value));
let saveTimeout = null;

const handleSaveEssay = async (force = false) => {
    if (!currentDocId.value) return;
    try {
        await fetch('http://localhost:8000/api/v1/user/essay', {
             method: 'POST',
             headers: { 'Content-Type': 'application/json' },
             body: JSON.stringify({ docId: currentDocId.value, content: markdownText.value })
        });
        if (force) {
            console.log("Saved essay manually");
        }
    } catch(e) { console.error(e); }
};

watch(markdownText, (newVal) => {
    if (saveTimeout) clearTimeout(saveTimeout);
    saveTimeout = setTimeout(() => {
        handleSaveEssay();
    }, 2000);
});

onMounted(() => {
    fetchPapers();
    fetchVocabulary();
});

const handleTranslation = async (data) => {
    // data: { x, y, text }
    translationPopup.value.show = true;
    translationPopup.value.x = data.x;
    translationPopup.value.y = data.y;
    translationPopup.value.word = data.text;
    translationPopup.value.loading = true;

    try {
        const res = await fetch(`http://localhost:8000/api/v1/dictionary/lookup?word=${data.text}`);
        const json = await res.json();
        if (json.code === 200) {
            translationPopup.value.cnen = json.data.meaning;
        } else {
             translationPopup.value.cnen = "Translation not found.";
        }
    } catch (e) {
        translationPopup.value.cnen = "Error fetching translation.";
    } finally {
        translationPopup.value.loading = false;
    }
    // return marked.parse(markdownText.value);
    return markdownText.value; // Simplification for now
};
</script>

<style scoped>
.main-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.content-area {
  display: flex;
  flex: 1;
  overflow: hidden;
  position: relative;
}

.viewer-container {
  flex: 1;
  position: relative;
  background-color: #525659;
  overflow: hidden;
}

.essay-container {
  width: 50%; /* Split screen */
  display: flex;
  flex-direction: column;
  background: white;
  border-left: 2px solid #ccc;
  box-shadow: -2px 0 5px rgba(0,0,0,0.1);
}

.essay-header {
  height: 40px;
  background: #eee;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 10px;
  border-bottom: 1px solid #ddd;
}

.save-btn {
    margin-right: 10px;
    padding: 2px 8px;
    cursor: pointer;
}

.essay-body {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.markdown-preview {
    flex: 1;
    padding: 15px;
    overflow-y: auto;
    border-bottom: 1px solid #ddd;
    background: #fdfdfd;
}

/* Markdown Styles */
.markdown-preview h1, .markdown-preview h2 { border-bottom: 1px solid #eee; padding-bottom: 5px; }
.markdown-preview blockquote { border-left: 3px solid #ccc; padding-left: 10px; color: #666; }

.markdown-input {
    height: 40%; /* Bottom part for writing */
    padding: 15px;
    border: none;
    resize: none;
    font-family: monospace;
    font-size: 14px;
    background: #fafafa;
    outline: none;
}

.markdown-input:focus {
    background: white;
}

.translation-popup {
    position: fixed;
    background: white;
    border: 1px solid #ccc;
    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    padding: 10px;
    z-index: 1000;
    max-width: 200px;
    border-radius: 4px;
}

.popup-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 5px;
    border-bottom: 1px solid #eee;
    padding-bottom: 4px;
}
.close-btn {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 16px;
}
</style>