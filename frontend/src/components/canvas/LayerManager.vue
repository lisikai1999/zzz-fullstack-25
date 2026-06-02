<template>
  <div class="layer-manager">
    <h4>标注图层</h4>
    <div class="layer-list">
      <div
        v-for="(layer, idx) in layers"
        :key="idx"
        class="layer-item"
        :class="{ active: idx === activeLayer }"
        @click="$emit('select-layer', idx)"
      >
        <input
          type="checkbox"
          :checked="layer.visible"
          @change="$emit('toggle-layer', idx)"
          @click.stop
        />
        <span class="layer-color" :style="{ background: layer.color }"></span>
        <span class="layer-name">{{ layer.name || `图层 ${idx + 1}` }}</span>
        <span class="layer-count">{{ (layer.annotations || []).length }}</span>
      </div>
    </div>
    <div class="layer-controls">
      <button @click="$emit('add-layer')">+ 新建图层</button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  layers: { type: Array, default: () => [] },
  activeLayer: { type: Number, default: 0 },
})

defineEmits(['select-layer', 'toggle-layer', 'add-layer'])
</script>

<style scoped>
.layer-manager {
  background: white;
  border-radius: 8px;
  padding: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.layer-manager h4 {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.layer-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.layer-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s;
}

.layer-item:hover {
  background: #f5f5f5;
}

.layer-item.active {
  background: #e8f0fe;
}

.layer-color {
  width: 12px;
  height: 12px;
  border-radius: 3px;
}

.layer-name {
  flex: 1;
  font-size: 13px;
}

.layer-count {
  font-size: 11px;
  color: #999;
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 10px;
}

.layer-controls {
  margin-top: 8px;
}

.layer-controls button {
  width: 100%;
  padding: 6px;
  border: 1px dashed #ccc;
  border-radius: 4px;
  background: transparent;
  cursor: pointer;
  font-size: 12px;
  color: #666;
}

.layer-controls button:hover {
  border-color: #999;
  background: #fafafa;
}
</style>
