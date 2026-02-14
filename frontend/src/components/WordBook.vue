<template>
  <div class="word-book-container">
    <!-- Navbar / Tabs for WordBook -->
    <div class="wb-nav">
      <button :class="{ active: view === 'list' }" @click="view = 'list'">Word List</button>
      <button :class="{ active: view === 'practice' }" @click="startPractice">Practice Mode</button>
    </div>

    <!-- Word List View -->
    <div v-if="view === 'list'" class="wb-list-view">
      <div class="wb-header">
        <div class="search-box">
          <i class="fas fa-search"></i>
          <input type="text" v-model="searchQuery" placeholder="Search words or meanings..." />
        </div>
        <div class="sort-box">
          <label>Sort by:</label>
          <select v-model="sortBy">
            <option value="alpha">A-Z</option>
            <option value="time">Date Added</option>
          </select>
        </div>
      </div>

      <div class="words-grid">
        <div class="column left-col">
          <div v-for="word in leftColumnWords" :key="word.id" class="word-card">
            <div class="word-main">
              <strong>{{ word.text }}</strong>
              <span class="phonetic" v-if="word.phonetic">[{{ word.phonetic }}]</span>
              <button class="delete-btn" @click="$emit('delete-word', word.id)" title="Delete Word">×</button>
            </div>
            <div class="word-meaning">{{ word.meaning }}</div>
            <div class="word-meta">{{ formatDate(word.addedAt) }}</div>
          </div>
        </div>
        <div class="column right-col">
           <div v-for="word in rightColumnWords" :key="word.id" class="word-card">
            <div class="word-main">
              <strong>{{ word.text }}</strong>
              <span class="phonetic" v-if="word.phonetic">[{{ word.phonetic }}]</span>
              <button class="delete-btn" @click="$emit('delete-word', word.id)" title="Delete Word">×</button>
            </div>
            <div class="word-meaning">{{ word.meaning }}</div>
            <div class="word-meta">{{ formatDate(word.addedAt) }}</div>
          </div>
        </div>
      </div>
      
      <div v-if="displayWords.length === 0" class="empty-state">
        No words found. Go mark some words in the documents!
      </div>
    </div>

    <!-- Practice View -->
    <div v-else class="wb-practice-view">
        <div v-if="practiceQueue.length === 0" class="practice-empty">
            <h3>No words to practice!</h3>
            <button @click="view = 'list'">Back to List</button>
        </div>
        <div v-else class="practice-card">
            <div class="progress-bar">
                <span>{{ currentPracticeIndex + 1 }} / {{ practiceQueue.length }}</span>
                <span class="score">Score: {{ score }}</span>
            </div>
            
            <!-- Type 1: Write English given Chinese -->
            <div v-if="currentQuestion.type === 'write'" class="question-type-write">
                <div class="q-label">Translate into English:</div>
                <div class="q-stimulus">{{ currentQuestion.word.meaning }}</div>
                <input 
                    type="text" 
                    v-model="userAnswer" 
                    @keyup.enter="checkAnswer" 
                    placehodler="Type word..." 
                    :class="{ 'correct': answerStatus === 'correct', 'wrong': answerStatus === 'wrong' }"
                    :disabled="answerStatus !== null"
                    ref="answerInput"
                />
                <div v-if="answerStatus" class="feedback">
                    <span v-if="answerStatus === 'correct'">Correct!</span>
                    <span v-else>Correct answer: <strong>{{ currentQuestion.word.text }}</strong></span>
                    <button @click="nextQuestion">Next</button>
                </div>
                <button v-else @click="checkAnswer" class="check-btn">Check</button>
            </div>

            <!-- Type 2: Select Chinese given English -->
            <div v-if="currentQuestion.type === 'select'" class="question-type-select">
                <div class="q-label">Select the meaning:</div>
                <div class="q-stimulus word-en">{{ currentQuestion.word.text }}</div>
                
                <div class="options-grid">
                    <button 
                        v-for="(opt, idx) in currentQuestion.options" 
                        :key="idx"
                        class="option-btn"
                        :class="{ 
                            'selected': userAnswer === idx,
                            'correct': answerStatus && idx === currentQuestion.correctOption,
                            'wrong': answerStatus === 'wrong' && userAnswer === idx
                        }"
                        @click="selectOption(idx)"
                        :disabled="answerStatus !== null"
                    >
                        {{ opt }}
                    </button>
                </div>
                 <div v-if="answerStatus" class="feedback">
                    <button @click="nextQuestion">Next</button>
                </div>
            </div>
        </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue';

const props = defineProps({
  words: {
    type: Array,
    required: true,
    default: () => []
  }
});
const emit = defineEmits(['delete-word']);

const view = ref('list'); // 'list' | 'practice'
const searchQuery = ref('');
const sortBy = ref('alpha'); // 'alpha' | 'time'

// --- List Logic ---
const formatDate = (ts) => {
    if (!ts) return '';
    return new Date(ts).toLocaleDateString();
}

const displayWords = computed(() => {
    let result = [...props.words];
    
    // Filter
    if (searchQuery.value) {
        const q = searchQuery.value.toLowerCase();
        result = result.filter(w => 
            w.text.toLowerCase().includes(q) || 
            w.meaning.includes(q)
        );
    }
    
    // Sort
    if (sortBy.value === 'alpha') {
        result.sort((a, b) => a.text.localeCompare(b.text));
    } else if (sortBy.value === 'time') {
        result.sort((a, b) => (b.addedAt || 0) - (a.addedAt || 0));
    }
    
    return result;
});

const leftColumnWords = computed(() => {
    return displayWords.value.filter((_, i) => i % 2 === 0);
});

const rightColumnWords = computed(() => {
    return displayWords.value.filter((_, i) => i % 2 !== 0);
});


// --- Practice Logic ---
const practiceQueue = ref([]);
const currentPracticeIndex = ref(0);
const currentQuestion = ref({});
const userAnswer = ref('');
const answerStatus = ref(null); // null, 'correct', 'wrong'
const score = ref(0);
const answerInput = ref(null);

const startPractice = () => {
    view.value = 'practice';
    // Generate questions
    // Shuffle words
    const shuffled = [...props.words].sort(() => Math.random() - 0.5);
    
    practiceQueue.value = shuffled.map((w, i) => {
        // Randomly decide type: write or select
        return {
            type: Math.random() > 0.5 ? 'write' : 'select',
            word: w,
            options: generateOptions(w)
        };
    });
    
    currentPracticeIndex.value = 0;
    score.value = 0;
    loadQuestion();
};

const generateOptions = (correctWord) => {
    // Pick 3 random other meanings
    const others = props.words.filter(w => w.id !== correctWord.id);
    const distractors = others.sort(() => Math.random() - 0.5).slice(0, 3).map(w => w.meaning);
    
    // If not enough words, pad with dummy
    while (distractors.length < 3) {
        distractors.push("Undefined Meaning " + Math.random());
    }
    
    const options = [...distractors, correctWord.meaning];
    return options.sort(() => Math.random() - 0.5); // Shuffle options
};

const loadQuestion = () => {
    if (currentPracticeIndex.value >= practiceQueue.value.length) {
        alert(`Practice Complete! Score: ${score.value}/${practiceQueue.value.length}`);
        view.value = 'list';
        return;
    }
    
    const q = practiceQueue.value[currentPracticeIndex.value];
    q.correctOption = q.type === 'select' ? q.options.indexOf(q.word.meaning) : -1;
    
    currentQuestion.value = q;
    userAnswer.value = '';
    answerStatus.value = null;
    
    if (q.type === 'write') {
        nextTick(() => {
            if (answerInput.value) answerInput.value.focus();
        });
    }
};

const checkAnswer = () => {
    if (answerStatus.value !== null) return; // Already checked
    
    const q = currentQuestion.value;
    let isCorrect = false;
    
    if (q.type === 'write') {
        if (userAnswer.value.trim().toLowerCase() === q.word.text.toLowerCase()) {
            isCorrect = true;
        }
    } else {
        // Select handled by selectOption, but strictly:
        // Not used here for select type as selectOption triggers immediately? 
        // User requirements: "Select selection... select right then go to next"
        // Let's implement immediate feedback in selectOption
    }
    
    if (isCorrect) {
        answerStatus.value = 'correct';
        score.value++;
        setTimeout(nextQuestion, 1000);
    } else {
        answerStatus.value = 'wrong';
    }
};

const selectOption = (idx) => {
    if (answerStatus.value !== null) return;
    
    userAnswer.value = idx;
    if (idx === currentQuestion.value.correctOption) {
        answerStatus.value = 'correct';
        score.value++;
        setTimeout(nextQuestion, 500); // Fast transition for select
    } else {
        answerStatus.value = 'wrong';
        // Don't auto advance on wrong, let them see
    }
}

const nextQuestion = () => {
    currentPracticeIndex.value++;
    loadQuestion();
};

</script>

<style scoped>
.word-book-container {
    height: 100%;
    overflow: auto;
    background: #f5f5f5;
    padding: 20px;
    box-sizing: border-box;
}

.wb-nav {
    display: flex;
    justify-content: center;
    gap: 10px;
    margin-bottom: 20px;
}

.wb-nav button {
    padding: 10px 20px;
    border: none;
    background: #ddd;
    color: #333;
    cursor: pointer;
    font-size: 16px;
    border-radius: 5px;
}

.wb-nav button.active {
    background: #4caf50;
    color: white;
}

.wb-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 20px;
    background: white;
    padding: 15px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.search-box {
    display: flex;
    align-items: center;
    background: #f0f0f0;
    padding: 5px 10px;
    border-radius: 20px;
    flex: 1;
    max-width: 400px;
}

.search-box input {
    border: none;
    background: transparent;
    margin-left: 10px;
    width: 100%;
    outline: none;
    font-size: 14px;
}

.sort-box select {
    margin-left: 10px;
    padding: 5px;
}

.words-grid {
    display: flex;
    gap: 20px;
}

.column {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.word-card {
    background: white;
    padding: 15px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    border-left: 4px solid #4caf50;
}

.word-main {
    font-size: 18px;
    margin-bottom: 5px;
    display: flex;
    align-items: center;
}

.word-main strong {
    margin-right: 10px;
}

.delete-btn {
    margin-left: auto;
    background: none;
    border: none;
    color: #999;
    font-size: 20px;
    cursor: pointer;
    line-height: 1;
}

.delete-btn:hover {
    color: #f44336;
}

.word-meaning {
    color: #555;
    margin-bottom: 8px;
}

.word-meta {
    font-size: 12px;
    color: #999;
}

.practice-card {
    max-width: 600px;
    margin: 40px auto;
    background: white;
    padding: 40px;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    text-align: center;
}

.q-stimulus {
    font-size: 24px;
    font-weight: bold;
    margin: 20px 0;
    color: #333;
}

.options-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 15px;
    margin: 20px 0;
}

.option-btn {
    padding: 15px;
    border: 2px solid #eee;
    background: white;
    border-radius: 8px;
    cursor: pointer;
    font-size: 16px;
    transition: all 0.2s;
}

.option-btn:hover {
    border-color: #aaa;
}

.option-btn.selected {
    border-color: #2196f3;
    background: #e3f2fd;
}

.option-btn.correct {
    border-color: #4caf50;
    background: #e8f5e9;
    color: #2e7d32;
}

.option-btn.wrong {
    border-color: #f44336;
    background: #ffebee;
}

input[type="text"] {
    width: 80%;
    padding: 10px;
    font-size: 18px;
    border: 2px solid #ddd;
    border-radius: 6px;
    margin-bottom: 15px;
}

input.correct {
    border-color: #4caf50;
    background: #e8f5e9;
}

input.wrong {
    border-color: #f44336;
    background: #ffebee;
}

.check-btn {
    padding: 10px 30px;
    background: #4caf50;
    color: white;
    border: none;
    border-radius: 20px;
    font-size: 16px;
    cursor: pointer;
}
</style>
