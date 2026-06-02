<template>
  <div class="toolbar">
    <button
      v-for="tool in toolList"
      :key="tool.name"
      :class="['tool-btn', { active: activeTool === tool.name }]"
      @click="$emit('tool-change', tool.name)"
      :title="tool.label"
    >
      <span class="tool-icon">{{ tool.icon }}</span>
      <span class="tool-label">{{ tool.label }}</span>
    </button>
    <div class="toolbar-divider"></div>
    <button class="tool-btn" @click="$emit('submit')" title="提交标注">
      <span class="tool-icon">✓</span>
      <span class="tool-label">提交</span>
    </button>
    <button class="tool-btn" @click="$emit('clear')" title="清除当前">
      <span class="tool-icon">✕</span>
      <span class="tool-label">清除</span>
    </button>
  </div>
</template>

<script setup>
defineProps({
  activeTool: { type: String, default: 'bbox' },
})

defineEmits(['tool-change', 'submit', 'clear'])

const toolList = [
  { name: 'panzoom', icon: '✋', label: '平移缩放' },
  { name: 'bbox', icon: '□', label: '矩形框' },
  { name: 'polygon', icon: '⬠', label: '多边形' },
  { name: 'brush', icon: '●', label: '画笔' },
]
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 4px;
  padding: 8px 12px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  align-items: center;
}

.tool-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  transition: all 0.15s;
  font-size: 13px;
}

.tool-btn:hover {
  background: #f5f5f5;
  border-color: #bbb;
}

.tool-btn.active {
  background: #1a1a2e;
  color: white;
  border-color: #1a1a2e;
}

.tool-icon {
  font-size: 16px;
}

.toolbar-divider {
  width: 1px;
  height: 24px;
  background: #e0e0e0;
  margin: 0 8px;
}
</style>
